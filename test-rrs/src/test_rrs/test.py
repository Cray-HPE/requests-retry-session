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

import logging
# Because we wish to support Python versions back to 3.6, we
# import things from typing that are not necessary in newer
# Python versions
from typing import (
    Type,
    Union
)

from requests import Response as RequestsResponse
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import ReadTimeout as RequestsReadTimeout
from requests.exceptions import RetryError as RequestsRetryError

from .defs import (
    BAD_NORETRY_SCS,
    DROP_SC,
    GOOD_SCS,
    ReqMethodToTest,
    RequestsMethod,
    RR_ADAPTER_ARGS,
    RR_STATUS_FORCELIST,
    SingleProtocol,
    TIMEOUT_DELAY
)
from .defs import NOTICE_LOG_LEVEL as NOTICE
from .request_sessions import RequestSessions
from .servers import BackgroundServers
from .suppress_ssl_warnings import suppress_ssl_warnings
from .typing_imports import Container, Iterable
from .utils import random_id


# Prior to requests 2.18, response objects were not context managers.
# Since this version of RRS supports these older requests versions, let's check
# and define our request response handling accordingly

if hasattr(RequestsResponse, "__enter__") and hasattr(RequestsResponse, "__exit__"):
    # Responses are context managers
    def req_sc(session_method, url, params):
        with session_method(url, params=params, verify=False) as resp:
            return resp.status_code
else:
    # Responses are not context managers
    def req_sc(session_method, url, params):
        return session_method(url, params=params, verify=False).status_code


def test_req(
    session_method: RequestsMethod,
    session_desc: str,
    url: str,
    *,
    expected_sc: Union[int, Type[Exception]],
    scs: Union[int, Iterable[int]],
    delays: Union[float, Iterable[float], None] = None
) -> int:
    """
    expected_sc is either the expected status code, or the type of Exception
    we expect to be raised

    If no delays are specified, they default to all 0s
    """
    if delays is None:
        if isinstance(scs, int):
            delays = 0
        else:
            delays = [0 for _ in scs]
    req_id = random_id()
    req_params = {'id': req_id, 'delays': delays, 'scs': scs}
    msg_pre = f"{session_desc} to {url} with params={req_params}"
    if isinstance(expected_sc, int):
        msg_post = f"(expected status code {expected_sc})"
    else:
        msg_post = f"(expected to raise {expected_sc.__name__} exception)"

    logging.debug("%s %s", msg_pre, msg_post)
    try:
        with suppress_ssl_warnings():
            sc = req_sc(session_method, url, req_params)
    except Exception as err:
        msg = f"{msg_pre} raised {type(err).__name__}: {err} {msg_post}"
        if isinstance(expected_sc, int):
            logging.error(msg)
            return 1
        assert issubclass(expected_sc, Exception)
        if isinstance(err, expected_sc):
            logging.debug(msg)
            return 0
        logging.error(msg)
        return 1

    # If we get here, it means no exception was raised, so we can examine
    # the status code of the response (sc)
    msg = f"{msg_pre} returned status code {sc} {msg_post}"
    if isinstance(expected_sc, int) and sc == expected_sc:
        logging.debug(msg)
        return 0
    logging.error(msg)
    return 1


def run_tests(
    protocols: Container[SingleProtocol],
    retry_test_list: Iterable[ReqMethodToTest],
    nonretry_test_list: Union[Iterable[ReqMethodToTest], None] = None
) -> int:
    """
    protocols - The protocols where timeout/retry is enabled
    retry_test_list -- methods to test where we expect retries
    nonretry_test_list -- methods to test where we do not expect retries
    """
    exit_rc = 0
    if nonretry_test_list is None:
        nonretry_test_list = []

    for sfunc, sdesc in retry_test_list:
        with BackgroundServers() as urls:
            for proto, url in urls._asdict().items():
                # Verify that a good status code is returned to us, regardless of protocol
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=GOOD_SCS[0],
                                    scs=GOOD_SCS[0])

                # Now test that a bad non-retry-able SC is also returned to us,
                # regardless of protocol
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=BAD_NORETRY_SCS[0],
                                    scs=BAD_NORETRY_SCS[0])

                # Now test an endpoint that initially returns bad retry-able SC, then returns a good one
                # If we are working with a retry-able protocol, then we expect the good SC.
                # Otherwise, we expect the bad SC
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=GOOD_SCS[0] if proto in protocols else RR_STATUS_FORCELIST[0],
                                    scs=(RR_STATUS_FORCELIST[0], GOOD_SCS[0]))

                # Now test an endpoint that always returns bad retry-able statuses
                # If the protocol is retry-able, then once our retries are exhausted,
                # we should get RequestsRetryError.
                # Otherwise, we expect to get back the first bad SC
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=RequestsRetryError if proto in protocols else RR_STATUS_FORCELIST[0],
                                    scs=RR_STATUS_FORCELIST)

                # Now test an endpoint that initially should drop connection, then returns good SC.
                # If the protocol has retries enabled, we expect the good SC.
                # Otherwise, we expect a ConnectionError
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=GOOD_SCS[0] if proto in protocols else RequestsConnectionError,
                                    scs=(DROP_SC, GOOD_SCS[0]))

                # Now test an endpoint that should always drop connection,
                # so we expect ConnectionError regardless of protocol
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=RequestsConnectionError,
                                    scs=DROP_SC)

                # Now test an endpoint that initially should time out, but always returns good SCs.
                # If timeouts are enabled for this protocol, then we expect to get back the second SC.
                # Otherwise we expect to get back the first.
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=GOOD_SCS[1] if proto in protocols else GOOD_SCS[0],
                                    scs=GOOD_SCS[:2],
                                    delays=(TIMEOUT_DELAY, 0))

        # To make sure the servers are not still dealing with the timeout from the previous subtest,
        # use a fresh one
        with BackgroundServers() as urls:
            for proto, url in urls._asdict().items():
                # Now test an endpoint that should always time out, if timeouts/retries are
                # enabled. In that case, we expect ConnectionError. Otherwise we expect
                # the good SC
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=RequestsConnectionError if proto in protocols else GOOD_SCS[0],
                                    scs=GOOD_SCS[0],
                                    delays=TIMEOUT_DELAY)

    for sfunc, sdesc in nonretry_test_list:
        with BackgroundServers() as urls:
            for proto, url in urls._asdict().items():
                # Verify that a good status code is returned to us, regardless of protocol
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=GOOD_SCS[0],
                                    scs=GOOD_SCS[0])

                # Now test that a bad non-retry-able SC is also returned to us,
                # regardless of protocol
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=BAD_NORETRY_SCS[0],
                                    scs=BAD_NORETRY_SCS[0])

                # Now test an endpoint that initially returns bad retry-able SC, then returns a good one.
                # Regardless of protocol, since there are no retries, we should get the bad SC back.
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=RR_STATUS_FORCELIST[0],
                                    scs=(RR_STATUS_FORCELIST[0], GOOD_SCS[0]))

                # Now test an endpoint that initially should drop connection, then returns a good SC.
                # We should not be retrying on the dropped connection, so a ConnectionError is expected,
                # regardless of protocol
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=RequestsConnectionError,
                                    scs=(DROP_SC, GOOD_SCS[0]))

                # Now test an endpoint that initially should time out, but always returns good status codes
                # We should not be retrying on the timeout, so a ReadTimeout is expected.
                # But that is only if we're using our retry/timeout adapter. If not, there should
                # be no timeout at all, and we eventually expect to get back the good SC.
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=RequestsReadTimeout if proto in protocols else GOOD_SCS[0],
                                    scs=GOOD_SCS[:2],
                                    delays=(TIMEOUT_DELAY, 0))

    return exit_rc


def run_all_tests_with_protocols(*protocols: SingleProtocol) -> int:
    """
    Run all of the tests with the specified protocols set to be re-tryable.
    Return 0 if all tests pass, non-0 otherwise.
    """
    exit_rc = 0

    with RequestSessions(protocols, RR_ADAPTER_ARGS) as rrs_test_lists:
        logging.log(NOTICE, "Running tests (protocol=%s args=%s)", protocols, RR_ADAPTER_ARGS)
        exit_rc += run_tests(protocols=protocols,
                             retry_test_list=rrs_test_lists.get(),
                             nonretry_test_list=rrs_test_lists.post())

    return exit_rc


def run_all_tests() -> int:
    """
    Run all of the tests. Return 0 if all tests pass, non-0 otherwise.
    """
    exit_rc = 0
    exit_rc += run_all_tests_with_protocols('http')
    exit_rc += run_all_tests_with_protocols('https')
    if exit_rc:
        logging.error("At least one subtest failed")
    else:
        logging.log(NOTICE, "All subtests passed")
    return exit_rc
