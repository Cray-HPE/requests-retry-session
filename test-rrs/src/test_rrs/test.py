#
# MIT License
#
# (C) Copyright 2026 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#

"""
Minimal RRS module test, mainly to ensure that it is not completely broken.
"""

import functools
import itertools
import logging
# Because we wish to support Python versions back to 3.6, we
# import things from typing that are not necessary in newer
# Python versions
from typing import List, Tuple

import requests
import requests_retry_session as rrs

from test_rrs.defs import (
    ReqRetries,
    REQUEST_VERBS,
    REQUEST_PROTOCOLS,
    RequestMethod,
    RequestProtocol,
    RequestVerb,
)
from test_rrs.defs import NOTICE_LOG_LEVEL as NOTICE
from test_rrs.do_request import test_req
from test_rrs.results import (
    RequestTestOptions,
    RRTestOptions,
    TestResults,
)
from test_rrs.rrs_lib import MyRRSessionManager, rr_adapter_args
from test_rrs.server import background_server
from test_rrs.test_suites import test_suites


def retryable_method(
    rr_args: rrs.RequestsRetryAdapterArgs,
    method: RequestVerb,
) -> bool:
    """
    Returns True if the specified HTTP method/verb is enabled for
    retries, given the specified requests_retry_session arguments.
    Returns False otherwise.
    Assumes that if the arguments do not specify allowed methods,
    then GET is allowed, but POST is not.
    """
    try:
        return method in rr_args["allowed_methods"]
    except KeyError:
        pass
    if method == "GET":
        return True
    if method == "POST":
        return False
    raise ValueError(f"Invalid request method: {method}")


def run_tests_with_method(
    method: RequestMethod,
    rr_test_options: RRTestOptions,
    test_results: TestResults,
) -> None:
    """
    Loop over the different request protocols and different test suites,
    and run every combination of them with the specified method
    """
    logging.debug("run_tests_with_method: method=%s, rr_test_options=%s", method, rr_test_options)
    for req_proto, tests in itertools.product(REQUEST_PROTOCOLS, test_suites()):
        logging.debug("run_tests_with_method: req_proto=%s", req_proto)
        retry = ReqRetries(method=method.retry,
                           protocol=req_proto in rr_test_options.proto)
        base_req_test_options = RequestTestOptions(verb=method.verb, proto=req_proto)
        with background_server(req_proto) as url:
            logging.debug("run_tests_with_method: url=%s", url)
            call_test_req = functools.partial(test_req,
                                              method,
                                              url,
                                              rr_test_options=rr_test_options,
                                              base_req_test_options=base_req_test_options,
                                              test_results=test_results)
            tests.run(retry=retry, call_test_req=call_test_req)


def run_tests_with_session(
    rr_session: requests.Session,
    rr_test_options: RRTestOptions,
    *,
    test_results: TestResults
) -> None:
    """
    Loop over the request verbs and run tests on the given session for each given verb
    """
    logging.log(NOTICE, "Running tests (protocol=%s args=%s)", rr_test_options.proto, rr_test_options.args)
    for req_verb in REQUEST_VERBS:
        method = RequestMethod(function=rr_session.get if req_verb == "GET" else rr_session.post,
                               verb=req_verb,
                               description=f"{rr_test_options.entry} {req_verb}",
                               retry=retryable_method(rr_test_options.args, req_verb))
        run_tests_with_method(method=method,
                              rr_test_options=rr_test_options,
                              test_results=test_results)


def run_tests_with_rr_options(
    rr_args: rrs.RequestsRetryAdapterArgs,
    rr_proto: Tuple[RequestProtocol, ...],
    test_results: TestResults,
) -> None:
    """
    For the specified set of RR options, test different requests_retry_session
    paths:

    - The retry_session_manager function
    - The RetrySessionManager class
    - The requests_retry_session function
    """
    base_rr_test_options = RRTestOptions(args=rr_args, proto=rr_proto)
    with rrs.retry_session_manager(protocol=rr_proto, **rr_args) as session:
        run_tests_with_session(
            session,
            base_rr_test_options._replace(entry="rrs.retry_session_manager"),
            test_results=test_results,
        )

    with MyRRSessionManager(rr_proto, rr_args) as mgr:
        run_tests_with_session(
            mgr.requests_session,
            base_rr_test_options._replace(entry="rrs.RetrySessionManager"),
            test_results=test_results,
        )

    with rrs.requests_retry_session(protocol=rr_proto, **rr_args) as session:
        run_tests_with_session(
            session,
            base_rr_test_options._replace(entry="rrs.requests_retry_session"),
            test_results=test_results,
        )


def run_all_tests() -> TestResults:
    """
    Run all of the tests. Return 0 if all tests pass, non-0 otherwise.
    """
    test_results = TestResults()

    rr_arg_list: List[rrs.RequestsRetryAdapterArgs] = [
        rr_adapter_args(),
        rr_adapter_args(allowed_methods=['POST']),
    ]
    rr_proto_list: List[Tuple[RequestProtocol, ...]] = [
        ('http',),
        ('http', 'https'),
    ]
    for rr_args, rr_proto in itertools.product(rr_arg_list, rr_proto_list):
        run_tests_with_rr_options(rr_args, rr_proto, test_results)

    return test_results
