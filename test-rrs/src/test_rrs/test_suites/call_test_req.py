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

# Because we wish to support Python versions back to 3.6, we
# import things from typing that are not necessary in newer
# Python versions
from typing import (
    Type,
    Union,
    TYPE_CHECKING,
)

from test_rrs.results import (
    RequestTestOptions,
    RRTestOptions,
    TestResults,
)
from test_rrs.typing_imports import (
    Iterable,
    Protocol,
    TypedDict,
)

if TYPE_CHECKING:
    from test_rrs.typing_imports import Unpack


class CallTestReqRequiredKwargs(TypedDict, total=True):
    """
    Required kwargs for the call_test function
    """
    expected_sc: Union[int, Type[Exception]]
    scs: Union[int, Iterable[int]]


class CallTestReqKwargs(CallTestReqRequiredKwargs, total=False):
    """
    Inherit the required kwargs, add in the optional ones
    """
    rr_test_options: RRTestOptions
    base_req_test_options: RequestTestOptions
    test_results: TestResults
    delays: Union[float, Iterable[float], None]


class CallTestReq(Protocol):
    """
    Define a protocol for callables which take the kwargs we just defined
    """
    def __call__(
        self,
        **kwargs: "Unpack[CallTestReqKwargs]"
    ) -> None: ...
