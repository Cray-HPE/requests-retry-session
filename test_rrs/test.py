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
import sys
# Because we wish to support Python versions back to 3.6, we
# import things from typing that are not necessary in newer
# Python versions
from typing import (
    Type,
    Union
)

# collections.abc.Callable/Iterable made parameterizable in Python 3.9
if sys.version_info >= (3, 9):
    from collections.abc import Callable, Iterable
else:
    from typing import Callable, Iterable

from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import ReadTimeout as RequestsReadTimeout
from requests.exceptions import RetryError as RequestsRetryError

from .defs import (
    BAD_NORETRY_SCS,
    DROP_SC,
    GOOD_SCS,
    ReqMethodToTest,
    RR_ADAPTER_ARGS,
    RR_STATUS_FORCELIST,
    SingleProtocol,
    TIMEOUT_DELAY
)
from .defs import NOTICE_LOG_LEVEL as NOTICE
from .request_sessions import RequestSessions
from .server import BackgroundServer
from .suppress_ssl_warnings import suppress_ssl_warnings
from .utils import random_id

def test_req(
    session_method: Callable,
    session_desc: str,
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
            delays=0
        else:
            delays=[0 for _ in scs]
    req_id = random_id()
    req_params = { 'id': req_id, 'delays': delays, 'scs': scs }
    msg_pre=f"{session_desc} with params={req_params}"
    if isinstance(expected_sc, int):
        msg_post=f"(expected status code {expected_sc})"
    else:
        msg_post=f"(expected to raise {expected_sc.__name__} exception)"

    logging.debug("%s %s", msg_pre, msg_post)
    try:
        with suppress_ssl_warnings():
            with session_method(URL, params=req_params) as resp:
                sc = resp.status_code
    except Exception as err:
        msg = f"{msg_pre} raised {type(err).__name__}: {err} {msg_post}"
        if isinstance(expected_sc, int):
            logging.error(msg)
            return 1
        if issubclass(expected_sc, Exception) and isinstance(err, expected_sc):
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
    protocols: Iterable[SingleProtocol],
    retry_test_list: Iterable[ReqMethodToTest],
    nonretry_test_list: Union[Iterable[ReqMethodToTest], None] = None
) -> int:
    """
    retry_test_list -- methods to test where we expect retries
    nonretry_test_list -- methods to test where we do not expect retries
    """
    exit_rc = 0
    if nonretry_test_list is None:
        nonretry_test_list = []
    for proto in protocols:
        for sfunc, sdesc in retry_test_list:
            with BackgroundServer(proto) as url:
                # Verify that a good status code is returned to us
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=GOOD_SCS[0],
                                    scs=GOOD_SCS[0]
                )
                # Now test that a bad non-retry-able SC is also returned to us
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=BAD_NORETRY_SCS[0],
                                    scs=BAD_NORETRY_SCS[0]
                )
                # Now test an endpoint that initially returns bad retry-able SC, then returns a good one
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=GOOD_SCS[0],
                                    scs=(RR_STATUS_FORCELIST[0], GOOD_SCS[0])
                )
                # Now test an endpoint that always returns bad retry-able statuses
                # Once our retries are exhausted, we should get RequestsRetryError
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=RequestsRetryError,
                                    scs=RR_STATUS_FORCELIST
                )
                # Now test an endpoint that initially should drop connection, then returns good SC
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=GOOD_SCS[0],
                                    scs=(DROP_SC, GOOD_SCS[0])
                )
                # Now test an endpoint that should always drop connection (so we expect ConnectionError)
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=RequestsConnectionError,
                                    scs=DROP_SC
                )
                # Now test an endpoint that initially should time out, but always returns good SCs.
                # We expect to get back the second good SC, since the first one should time out and
                # be retries.
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=GOOD_SCS[1],
                                    scs=GOOD_SCS[:2],
                                    delays=(TIMEOUT_DELAY, 0)
                )

            # To make sure the server is not still dealing with the timeout from the previous subtest,
            # use a fresh one
            with BackgroundServer(proto) as url:
                # Now test an endpoint that should always time out (so we expect ConnectionError)
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=RequestsConnectionError,
                                    scs=GOOD_SCS[0],
                                    delays=TIMEOUT_DELAY
                )

        for sfunc, sdesc in nonretry_test_list:
            with BackgroundServer(proto) as url:
                # Verify that a good status code is returned to us
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=GOOD_SCS[0],
                                    scs=GOOD_SCS[0]
                )
                # Now test that a bad non-retry-able SC is also returned to us
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=BAD_NORETRY_SCS[0],
                                    scs=BAD_NORETRY_SCS[0]
                )
                # Now test an endpoint that initially returns bad retry-able SC, then returns a good one.
                # Without retries, we should get the bad SC back.
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=RR_STATUS_FORCELIST[0],
                                    scs=(RR_STATUS_FORCELIST[0], GOOD_SCS[0])
                )
                # Now test an endpoint that initially should drop connection, then returns a good SC.
                # We should not be retrying on the dropped connection, so a ConnectionError is expected
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=RequestsConnectionError,
                                    scs=(DROP_SC, GOOD_SCS[0])
                )
                # Now test an endpoint that initially should time out, but always returns good status codes
                # We should not be retrying on the timeout, so a ReadTimeout is expected
                exit_rc += test_req(sfunc, sdesc, url,
                                    expected_sc=RequestsReadTimeout,
                                    scs=GOOD_SCS[:2],
                                    delays=(TIMEOUT_DELAY, 0)
                )

    return exit_rc

def run_all_tests() -> int:
    exit_rc = 0
    post_only_adapter_args = RR_ADAPTER_ARGS.copy()
    post_only_adapter_args['allowed_methods'] = ('POST',)

    for proto in [ ('http', ),
                   ('https', 'http') ]:
        with RequestSessions(proto, RR_ADAPTER_ARGS) as rrs_sessions:
            logging.log(NOTICE, "Running tests (protocol=%s args=%s)", proto, RR_ADAPTER_ARGS)
            exit_rc += run_tests(protocol=proto,
                                 retry_test_list=rrs_sessions.test_list("get"))

        with RequestSessions(proto, post_only_adapter_args) as rrs_sessions:
            logging.log(NOTICE, "Running tests (protocol=%s args=%s)", proto, post_only_adapter_args)
            exit_rc += run_tests(
                        protocol=proto,
                        retry_test_list=rrs_sessions.test_list("post"),
                        nonretry_test_list=rrs_sessions.test_list("get"))

    if exit_rc:
        logging.error("At least one subtest failed")
    else:
        logging.log(NOTICE, "All subtests passed")

    return exit_rc
