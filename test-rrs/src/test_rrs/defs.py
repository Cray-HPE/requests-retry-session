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
# Because we wish to support Python versions back to 3.6, we
# import Union rather than using |
from typing import (DefaultDict,
                    FrozenSet,
                    NamedTuple,
                    Tuple)

import requests

import requests_retry_session as rrs

from .typing_imports import Callable, Literal, TypeAlias


RequestsMethod: TypeAlias = Callable[..., requests.Response]

# In our testing, we are only going to ever use protocols http and https
SingleProtocol: TypeAlias = Literal['http', 'https']
SINGLE_PROTOCOLS: FrozenSet[SingleProtocol] = frozenset({'http', 'https'})
# In this version of RRS, only a single protocol can be specified
ProtocolType: TypeAlias = SingleProtocol
SERVER_HOSTNAME = 'localhost'

ReqParamId: TypeAlias = str
ReqParamDelays: TypeAlias = Tuple[float, ...]
ReqParamScs: TypeAlias = Tuple[int, ...]


class ReqParams(NamedTuple):
    """
    Request parameters

    id: A unique identifier for this reqeust
    scs: The sequence of status codes that the server should respond with
    delays: A sequence of time delays (in seconds) that the server should wait before
            returning the corresponding status code

    e.g.    id = "abcdefgh12345678"
            scs = [510, 200]
            delays = [1.5, 0]

    The first time the server receives a GET request with the above parameters,
    it will wait 1.5 seconds, then return 510.
    If it gets a second GET request with the above parameters, it will immediately
    return 200.
    Any subsequent GET requests with the above parameters will also immediately return
    200.

    Note: If any parameter value is changed, then it is considered a new set of parameters,
    and thus will not continue the previous sequence. Also, the request method used is also
    part of the key -- If a GET request with a given set of parameters is followed by a POST
    request with the same set of parameters, then the server will not consider them part of the
    same sequence.
    """
    id: ReqParamId
    delays: ReqParamDelays
    scs: ReqParamScs


class CertFilePaths(NamedTuple):
    """
    Paths to the cert file and key file
    """
    cert_file: str
    key_file: str


class ServerUrls(NamedTuple):
    """
    URLs for the servers
    """
    http: str
    https: str


# Type annotation helpers

# Obviously there are more methods, but we are only listing the ones we use
ReqMethodName: TypeAlias = Literal['GET', 'POST']
ReqCountKey: TypeAlias = Tuple[ReqMethodName, ReqParams]
ReqCountDict: TypeAlias = DefaultDict[ReqCountKey, int]

# A tuple of a requests method and a string describing it
ReqMethodToTest: TypeAlias = Tuple[RequestsMethod, str]

RR_TIMEOUT = 0.05
TIMEOUT_DELAY = 0.09
RR_STATUS_FORCELIST = (521, 522, 523)
RR_NUM_RETRIES = 2

# DROP_SC is the SC that tells the server to just disconnect without response
DROP_SC = 0
GOOD_SCS = tuple(range(210, 300))
BAD_NORETRY_SCS = tuple(range(510, 521))

RR_ADAPTER_ARGS = rrs.RequestsRetryAdapterArgs(
    retries=RR_NUM_RETRIES,
    backoff_factor=0.01,
    status_forcelist=RR_STATUS_FORCELIST,
    connect_timeout=RR_TIMEOUT,
    read_timeout=RR_TIMEOUT
)

NOTICE_LOG_LEVEL: int = (logging.WARNING + logging.ERROR) // 2 + logging.WARNING
NOTICE_LOG_NAME: str = "NOTICE"
