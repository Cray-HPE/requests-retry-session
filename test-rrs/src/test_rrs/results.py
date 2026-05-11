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

from dataclasses import dataclass, field
import logging
# Because we wish to support Python versions back to 3.6, we
# import things from typing that are not necessary in newer
# Python versions
from typing import (
    List,
    NamedTuple,
    Tuple,
    Union,
)

import requests_retry_session as rrs

from test_rrs.defs import ReqParams, RequestProtocol, RequestVerb
from test_rrs.defs import NOTICE_LOG_LEVEL as NOTICE


class RequestTestOptions(NamedTuple):
    """
    Request options for a single subtest
    """
    verb: RequestVerb
    proto: RequestProtocol
    params: Union[ReqParams, None] = None


class RRTestOptions(NamedTuple):
    """
    RRS options for a single subtest
    """
    args: rrs.RequestsRetryAdapterArgs
    proto: Tuple[RequestProtocol, ...]
    entry: Union[str, None] = None


class TestRecord(NamedTuple):
    """
    Parameters that define a single subtest
    """
    req: RequestTestOptions
    rr: RRTestOptions


@dataclass(frozen=True)
class TestResults:
    """
    Summary of subtest execution
    """
    passed: List[TestRecord] = field(default_factory=list)
    failed: List[TestRecord] = field(default_factory=list)


def log_test_results(test_results: TestResults) -> None:
    """
    Log the test results
    """
    logging.debug("Listing all %d passed subtests", len(test_results.passed))
    for tr in test_results.passed:
        logging.debug("Passed: %s", tr)
    if not test_results.failed:
        logging.log(NOTICE, "All %d subtests passed", len(test_results.passed))
        return
    logging.log(NOTICE, "Listing all %d failed subtests", len(test_results.failed))
    for tr in test_results.failed:
        logging.log(NOTICE, "Failed: %s", tr)
