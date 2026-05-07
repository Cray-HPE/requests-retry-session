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
import logging
# Because we wish to support Python versions back to 3.6, we
# import things from typing that are not necessary in newer
# Python versions
from typing import (
    List,
    Tuple,
    Type,
    Union
)

from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import ReadTimeout as RequestsReadTimeout
from requests.exceptions import RetryError as RequestsRetryError

from .defs import (
    BAD_NORETRY_SCS,
    DROP_SC,
    GOOD_SCS,
    ReqMethodToTest,
    ReqParams,
    RequestsMethod,
    RR_ADAPTER_ARGS,
    RR_STATUS_FORCELIST,
    SingleProtocol,
    TestRecord,
    TestResults,
    TIMEOUT_DELAY
)
from .defs import NOTICE_LOG_LEVEL as NOTICE
from .request_sessions import RequestSessions
from .servers import BackgroundServers
from .suppress_ssl_warnings import suppress_ssl_warnings
from .typing_imports import (
    Container,
    Iterable,
    IterableProtocol
)
from .utils import random_id


def test_req(
    session_method: RequestsMethod,
    session_desc: str,
    url: str,
    *,
    expected_sc: Union[int, Type[Exception]],
    scs: Union[int, Iterable[int]],
    base_tr: TestRecord,
    test_results: TestResults,
    delays: Union[float, Iterable[float], None] = None
) -> None:
    """
    expected_sc is either the expected status code, or the type of Exception
    we expect to be raised

    If no delays are specified, they default to all 0s
    """
    scs_tuple: Tuple[int, ...]
    delays_tuple: Tuple[float, ...]
    if isinstance(scs, tuple):
        scs_tuple = scs
    elif isinstance(scs, IterableProtocol):
        scs_tuple = tuple(scs)
    else:
        scs_tuple = (scs,)
    if delays is None:
        delays_tuple = tuple(0 for _ in scs_tuple)
    elif isinstance(delays, tuple):
        delays_tuple = delays
    elif isinstance(delays, IterableProtocol):
        delays_tuple = tuple(delays)
    else:
        delays_tuple = (delays,)

    req_id = random_id()
    req_params = ReqParams(id=req_id, delays=delays_tuple, scs=scs_tuple)
    msg_pre = f"{session_desc} to {url} with params={req_params}"
    if isinstance(expected_sc, int):
        msg_post = f"(expected status code {expected_sc})"
    else:
        msg_post = f"(expected to raise {expected_sc.__name__} exception)"
    # The protocols field is filled in the base_tr record
    # Now we create a new TR for this subtest, filling in the remaining fields
    tr = base_tr._replace(url=url,
                          desc=f"{msg_pre} {msg_post}",
                          params=req_params)

    logging.debug("%s %s", msg_pre, msg_post)
    try:
        with suppress_ssl_warnings():
            with session_method(url, params=req_params._asdict(), verify=False) as resp:
                sc = resp.status_code
    except Exception as err:
        msg = f"{msg_pre} raised {type(err).__name__}: {err} {msg_post}"
        if isinstance(expected_sc, int):
            logging.error(msg)
            test_results.failed.append(tr)
            return
        assert issubclass(expected_sc, Exception)
        if isinstance(err, expected_sc):
            logging.debug(msg)
            test_results.passed.append(tr)
            return
        logging.error(msg)
        test_results.failed.append(tr)
        return

    # If we get here, it means no exception was raised, so we can examine
    # the status code of the response (sc)
    msg = f"{msg_pre} returned status code {sc} {msg_post}"
    if isinstance(expected_sc, int) and sc == expected_sc:
        logging.debug(msg)
        test_results.passed.append(tr)
        return
    logging.error(msg)
    test_results.failed.append(tr)


def run_tests(
    protocols: Container[SingleProtocol],
    retry_test_list: Iterable[ReqMethodToTest],
    test_results: TestResults,
    nonretry_test_list: Union[Iterable[ReqMethodToTest], None] = None
) -> None:
    """
    protocols - The protocols where timeout/retry is enabled
    retry_test_list -- methods to test where we expect retries
    nonretry_test_list -- methods to test where we do not expect retries
    """
    if nonretry_test_list is None:
        nonretry_test_list = []

    base_tr = TestRecord(protocols=protocols)
    call_test_req = functools.partial(test_req,
                                      base_tr=base_tr,
                                      test_results=test_results)

    for sfunc, sdesc in retry_test_list:
        with BackgroundServers() as urls:
            for proto, url in urls._asdict().items():
                # Verify that a good status code is returned to us, regardless of protocol
                call_test_req(sfunc, sdesc, url,
                              expected_sc=GOOD_SCS[0],
                              scs=GOOD_SCS[0])

                # Now test that a bad non-retry-able SC is also returned to us,
                # regardless of protocol
                call_test_req(sfunc, sdesc, url,
                              expected_sc=BAD_NORETRY_SCS[0],
                              scs=BAD_NORETRY_SCS[0])

                # Now test an endpoint that initially returns bad retry-able SC, then returns a good one
                # If we are working with a retry-able protocol, then we expect the good SC.
                # Otherwise, we expect the bad SC
                call_test_req(sfunc, sdesc, url,
                              expected_sc=GOOD_SCS[0] if proto in protocols else RR_STATUS_FORCELIST[0],
                              scs=(RR_STATUS_FORCELIST[0], GOOD_SCS[0]))

                # Now test an endpoint that always returns bad retry-able statuses
                # If the protocol is retry-able, then once our retries are exhausted,
                # we should get RequestsRetryError.
                # Otherwise, we expect to get back the first bad SC
                call_test_req(sfunc, sdesc, url,
                              expected_sc=RequestsRetryError if proto in protocols else RR_STATUS_FORCELIST[0],
                              scs=RR_STATUS_FORCELIST)

                # Now test an endpoint that initially should drop connection, then returns good SC.
                # If the protocol has retries enabled, we expect the good SC.
                # Otherwise, we expect a ConnectionError
                call_test_req(sfunc, sdesc, url,
                              expected_sc=GOOD_SCS[0] if proto in protocols else RequestsConnectionError,
                              scs=(DROP_SC, GOOD_SCS[0]))

                # Now test an endpoint that should always drop connection,
                # so we expect ConnectionError regardless of protocol
                call_test_req(sfunc, sdesc, url,
                              expected_sc=RequestsConnectionError,
                              scs=DROP_SC)

                # Now test an endpoint that initially should time out, but always returns good SCs.
                # If timeouts are enabled for this protocol, then we expect to get back the second SC.
                # Otherwise we expect to get back the first.
                call_test_req(sfunc, sdesc, url,
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
                call_test_req(sfunc, sdesc, url,
                              expected_sc=RequestsConnectionError if proto in protocols else GOOD_SCS[0],
                              scs=GOOD_SCS[0],
                              delays=TIMEOUT_DELAY)

    for sfunc, sdesc in nonretry_test_list:
        with BackgroundServers() as urls:
            for proto, url in urls._asdict().items():
                # Verify that a good status code is returned to us, regardless of protocol
                call_test_req(sfunc, sdesc, url,
                              expected_sc=GOOD_SCS[0],
                              scs=GOOD_SCS[0])

                # Now test that a bad non-retry-able SC is also returned to us,
                # regardless of protocol
                call_test_req(sfunc, sdesc, url,
                              expected_sc=BAD_NORETRY_SCS[0],
                              scs=BAD_NORETRY_SCS[0])

                # Now test an endpoint that initially returns bad retry-able SC, then returns a good one.
                # Regardless of protocol, since there are no retries, we should get the bad SC back.
                call_test_req(sfunc, sdesc, url,
                              expected_sc=RR_STATUS_FORCELIST[0],
                              scs=(RR_STATUS_FORCELIST[0], GOOD_SCS[0]))

                # Now test an endpoint that initially should drop connection, then returns a good SC.
                # We should not be retrying on the dropped connection, so a ConnectionError is expected,
                # regardless of protocol
                call_test_req(sfunc, sdesc, url,
                              expected_sc=RequestsConnectionError,
                              scs=(DROP_SC, GOOD_SCS[0]))

                # Now test an endpoint that initially should time out, but always returns good status codes
                # We should not be retrying on the timeout, so a ReadTimeout is expected.
                # But that is only if we're using our retry/timeout adapter. If not, there should
                # be no timeout at all, and we eventually expect to get back the good SC.
                call_test_req(sfunc, sdesc, url,
                              expected_sc=RequestsReadTimeout if proto in protocols else GOOD_SCS[0],
                              scs=GOOD_SCS[:2],
                              delays=(TIMEOUT_DELAY, 0))


def run_all_tests_with_protocols(
    *protocols: SingleProtocol,
    test_results: TestResults
) -> None:
    """
    Run all of the tests with the specified protocols set to be re-tryable.
    """
    post_only_adapter_args = RR_ADAPTER_ARGS.copy()
    post_only_adapter_args['allowed_methods'] = ('POST',)

    with RequestSessions(protocols, RR_ADAPTER_ARGS) as rrs_test_lists:
        logging.log(NOTICE, "Running tests (protocol=%s args=%s)", protocols, RR_ADAPTER_ARGS)
        run_tests(protocols=protocols,
                  retry_test_list=rrs_test_lists.get(),
                  test_results=test_results)

    with RequestSessions(protocols, post_only_adapter_args) as rrs_test_lists:
        logging.log(NOTICE, "Running tests (protocol=%s args=%s)", protocols, post_only_adapter_args)
        run_tests(protocols=protocols,
                  retry_test_list=rrs_test_lists.post(),
                  nonretry_test_list=rrs_test_lists.get(),
                  test_results=test_results)


def run_all_tests() -> int:
    """
    Run all of the tests. Return 0 if all tests pass, non-0 otherwise.
    """
    failed_subtests: List[TestRecord] = []
    passed_subtests: List[TestRecord] = []
    test_results = TestResults(failed=failed_subtests, passed=passed_subtests)

    run_all_tests_with_protocols('http', test_results=test_results)
    run_all_tests_with_protocols('https', 'http', test_results=test_results)
    logging.debug("Listing all %d passed subtests", len(test_results.passed))
    for tr in test_results.passed:
        logging.debug("Passed: %s", tr)
    if not test_results.failed:
        logging.log(NOTICE, "All %d subtests passed", len(test_results.passed))
        return 0
    logging.log(NOTICE, "Listing all %d failed subtests", len(test_results.failed))
    for tr in test_results.failed:
        logging.log(NOTICE, "Failed: %s", tr)
    return 1
