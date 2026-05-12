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
    Any,
    ClassVar,
    Dict,
    List,
    Tuple,
)

from test_rrs.defs import ReqRetries
from test_rrs.typing_imports import Protocol, runtime_checkable
from .call_test_req import CallTestReq


@runtime_checkable
class TestSuite(Protocol):
    """
    Defines what a test suite class needs to look like
    """
    @classmethod
    def run(
        cls,
        *,
        retry: ReqRetries,
        call_test_req: CallTestReq,
    ) -> None:
        """ Execute the tests in the suite """


class TestSuiteMeta(type):
    """
    Record every test suite that we define, so we don't
    have to do it manually
    """
    test_suites: "ClassVar[List[TestSuite]]" = []

    def __init__(
        cls,
        name: str,
        bases: Tuple[type, ...],
        namespace: Dict[str, Any]
    ):
        super().__init__(name, bases, namespace)
        if issubclass(cls, TestSuite):
            TestSuiteMeta.test_suites.append(cls)


def test_suites() -> List[TestSuite]:
    """ Return a list of all defined test suite classes """
    logging.debug("test_suites() = %s", TestSuiteMeta.test_suites)
    return list(TestSuiteMeta.test_suites)
