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
Test definitions
"""

import logging
import sys
# Because we wish to support Python versions back to 3.6, we
# import Union rather than using |
from typing import (get_args,
                    DefaultDict,
                    FrozenSet,
                    NamedTuple,
                    Tuple,
                    Union)

# collections.abc.Callable/Iterable made parameterizable in Python 3.9
# Literal was added to typing in 3.9
# TypeAlias was added to typing in 3.10
if sys.version_info >= (3, 10):
    from collections.abc import Callable, Iterable
    from typing import Literal, TypeAlias
elif sys.version_info >= (3, 9):
    from collections.abc import Callable, Iterable
    from typing import Literal
    from typing_extensions import TypeAlias
else:
    from typing import Callable, Iterable
    from typing_extensions import Literal, TypeAlias

import requests_retry_session as rrs

# In our testing, we are only going to ever use protocols http and https
SingleProtocol: TypeAlias = Literal['http', 'https']
SINGLE_PROTOCOLS: FrozenSet[SingleProtocol] = frozenset(get_args(SingleProtocol))
ProtocolType: TypeAlias = Union[SingleProtocol, Iterable[SingleProtocol]]
SERVER_HOSTNAME = 'localhost'

class ReqParams(NamedTuple):
    id: str
    scs: Tuple[int, ...]
    delays: Tuple[float, ...]

# Type annotation helpers

# Obviously there are more methods, but we are only listing the ones we use
ReqMethodName: TypeAlias = Literal['GET', 'POST']
ReqCountKey: TypeAlias = Tuple[ReqMethodName, ReqParams]
ReqCountDict: TypeAlias = DefaultDict[ReqCountKey, int]

# A tuple of a requests method and a string describing it
ReqMethodToTest: TypeAlias = Tuple[Callable, str]

RR_TIMEOUT = 0.05
TIMEOUT_DELAY = 0.06
RR_STATUS_FORCELIST = (521, 522, 523)
RR_NUM_RETRIES = 2

# DROP_SC is the SC that tells the server to just disconnect without response
DROP_SC = 0
GOOD_SCS = tuple(range(210,300))
BAD_NORETRY_SCS = tuple(range(510,521))

RR_ADAPTER_ARGS = rrs.RequestsRetryAdapterArgs(
    retries=RR_NUM_RETRIES,
    backoff_factor=0.01,
    status_forcelist=RR_STATUS_FORCELIST,
    connect_timeout=RR_TIMEOUT,
    read_timeout=RR_TIMEOUT
)

NOTICE_LOG_LEVEL: int = (logging.WARNING + logging.ERROR) // 2 + logging.WARNING