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
from typing import Type, Union

from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import ReadTimeout as RequestsReadTimeout
from requests.exceptions import RetryError as RequestsRetryError

from test_rrs.defs import ReqRetries
from test_rrs.rrs_lib import RR_STATUS_FORCELIST
from test_rrs.server import DROP_SC

from .call_test_req import CallTestReq
from .defs import BAD_NORETRY_SCS, GOOD_SCS, TIMEOUT_DELAY
from .test_suite_base import TestSuiteMeta


class TestSuite1A(metaclass=TestSuiteMeta):
    """ First test suite """
    @classmethod
    def run(
        cls,
        *,
        retry: ReqRetries,
        call_test_req: CallTestReq,
    ) -> None:
        """
        Run the tests
        """
        logging.debug("TestSuite1A: run()")
        # Verify that a good status code is returned to us,
        # regardless of protocol or method
        call_test_req(expected_sc=GOOD_SCS[0],
                      scs=GOOD_SCS[0])

        # Now test that a bad non-retry-able SC is also returned to us,
        # regardless of protocol or method
        call_test_req(expected_sc=BAD_NORETRY_SCS[0],
                      scs=BAD_NORETRY_SCS[0])

        # Now test an endpoint that initially returns bad retry-able SC, then returns a good one
        # If we are working with a retry-able protocol and method, then we expect the good SC.
        # Otherwise, we expect the bad SC
        call_test_req(expected_sc=GOOD_SCS[0] if retry else RR_STATUS_FORCELIST[0],
                      scs=(RR_STATUS_FORCELIST[0], GOOD_SCS[0]))

        # No need to do the following test if there are no retries, because
        # it's basically the same as the previous test in that case
        if retry:
            # Now test an endpoint that always returns bad retry-able statuses
            # If the protocol and method are retry-able, then once our retries are exhausted,
            # we should get RequestsRetryError.
            # Otherwise, we expect to get back the first bad SC
            call_test_req(expected_sc=RequestsRetryError if retry else RR_STATUS_FORCELIST[0],
                          scs=RR_STATUS_FORCELIST)

        # Now test an endpoint that initially should drop connection, then returns good SC.
        # If retries enabled, we expect the good SC.
        # Otherwise, we expect a ConnectionError
        call_test_req(expected_sc=GOOD_SCS[0] if retry else RequestsConnectionError,
                      scs=(DROP_SC, GOOD_SCS[0]))

        # No need to do the following test if there are no retries, because
        # it's basically the same as the previous test in that case
        if retry:
            # Now test an endpoint that should always drop connection,
            # so we expect ConnectionError regardless
            call_test_req(expected_sc=RequestsConnectionError,
                          scs=DROP_SC)

        # Now test an endpoint that initially should time out, but always returns good SCs.
        # If we are not using our adapter at all (that is, the protocol is not
        # retryable), then the request will never actually timeout, and we expect
        # to get back the first good SC.
        # If we ARE using our adapter, but the method is not retryable, then we
        # expect to get back a ReadTimeout.
        # Finally, if we ARE using our adapter AND the method is retryable, then
        # we expect to get back the second good SC.
        expected_sc: Union[int, Type[Exception]]
        if retry:
            expected_sc = GOOD_SCS[1]
        elif retry.protocol:
            expected_sc = RequestsReadTimeout
        else:
            expected_sc = GOOD_SCS[0]
        call_test_req(expected_sc=expected_sc,
                      scs=GOOD_SCS[:2],
                      delays=(TIMEOUT_DELAY, 0))


class TestSuite1B(metaclass=TestSuiteMeta):
    """
    Second test suite
    """
    @classmethod
    def run(
        cls,
        *,
        retry: ReqRetries,
        call_test_req: CallTestReq,
    ) -> None:
        """
        Test an endpoint that should always time out, if we are using
        our timeout adapter, but always returns a good status code.
        If we are not using our adapter at all (that is, the protocol is
        not retryable), then no timeout will happen, and we expect to get
        back the good SC.
        If we are using our adapter but the method is not retryable, then
        we expect RequestsReadTimeout
        And if both method and protocol are retryable, then we expect to
        eventually get a ConnectionError.
        """
        logging.debug("TestSuite1B: run()")
        expected_sc: Union[int, Type[Exception]]
        if retry:
            expected_sc = RequestsConnectionError
        elif retry.protocol:
            # This case (method_retry False, proto_retry True) is a duplicate
            # of the last test in suite1, so we skip in that case
            return
        else:
            expected_sc = GOOD_SCS[0]
        call_test_req(expected_sc=expected_sc,
                      scs=GOOD_SCS[0],
                      delays=TIMEOUT_DELAY)
