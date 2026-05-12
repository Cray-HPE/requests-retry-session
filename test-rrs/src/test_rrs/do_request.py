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
    Tuple,
    Type,
    Union,
)

from test_rrs.defs import (
    ReqParams,
    RequestMethod,
    RequestMethodFunction,
)
from test_rrs.results import (
    RequestTestOptions,
    RRTestOptions,
    TestRecord,
    TestResults,
)
from test_rrs.typing_imports import Iterable, IterableProtocol
from test_rrs.utils import random_id, suppress_ssl_warnings


def test_req(
    method: RequestMethod,
    url: str,
    *,
    expected_sc: Union[int, Type[Exception]],
    scs: Union[int, Iterable[int]],
    rr_test_options: RRTestOptions,
    base_req_test_options: RequestTestOptions,
    test_results: TestResults,
    delays: Union[float, Iterable[float], None] = None
) -> None:
    """
    expected_sc is either the expected status code, or the type of Exception
    we expect to be raised

    If no delays are specified, they default to all 0s
    """
    logging.debug(
        "test_req: method=%s, url=%s, expected_sc=%s, scs=%s, delays=%s",
        method,
        url,
        expected_sc,
        scs,
        delays,
    )
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
    # Create the completed TestRecord for this subtest
    tr = TestRecord(
        rr=rr_test_options,
        req=base_req_test_options._replace(params=req_params)
    )
    msg_pre = f"{method.description} to {url} with params={req_params}"
    if isinstance(expected_sc, int):
        msg_post = f"(expected status code {expected_sc})"
    else:
        msg_post = f"(expected to raise {expected_sc.__name__} exception)"
    if _do_test_req(
        session_method=method.function,
        url=url,
        req_params=req_params,
        expected_sc=expected_sc,
        msg_pre=msg_pre,
        msg_post=msg_post
    ):
        test_results.passed.append(tr)
    else:
        test_results.failed.append(tr)


def _do_test_req(
    *,
    session_method: RequestMethodFunction,
    url: str,
    req_params: ReqParams,
    expected_sc: Union[int, Type[Exception]],
    msg_pre: str,
    msg_post: str,
) -> bool:
    """
    Makes the specified request.
    Returns True if the outcome matches the expected outcome.
    Returns False otherwise.
    """
    logging.debug("%s %s", msg_pre, msg_post)
    try:
        with suppress_ssl_warnings():
            with session_method(url, params=req_params._asdict(), verify=False) as resp:
                sc = resp.status_code
    except Exception as err:
        msg = f"{msg_pre} raised {type(err).__name__}: {err} {msg_post}"
        if isinstance(expected_sc, int):
            logging.error(msg)
            return False
        assert issubclass(expected_sc, Exception)
        if isinstance(err, expected_sc):
            logging.debug(msg)
            return True
        logging.error(msg)
        return False

    # If we get here, it means no exception was raised, so we can examine
    # the status code of the response (sc)
    msg = f"{msg_pre} returned status code {sc} {msg_post}"
    if isinstance(expected_sc, int) and sc == expected_sc:
        logging.debug(msg)
        return True
    logging.error(msg)
    return False
