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

# Because we wish to support Python versions back to 3.6, we
# import Union rather than using |
from typing import Union

import requests_retry_session as rrs


# What timeout value to use when creating RR sessions
RR_TIMEOUT = 0.05

# The status codes for which retries should be enabled
RR_STATUS_FORCELIST = (521, 522, 523)

# Maximum number of retries
RR_NUM_RETRIES = 2

# Backoff factor to use when creating RR sessions
BACKOFF_FACTOR = 0.01


def rr_adapter_args(
    allowed_methods: Union[rrs.AllowedMethodsType, None] = None,
) -> rrs.RequestsRetryAdapterArgs:
    """
    Return RR adapter args with our test values.
    If allowed_methods are specified, include those as well.
    """
    base = rrs.RequestsRetryAdapterArgs(
        retries=RR_NUM_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=RR_STATUS_FORCELIST,
        connect_timeout=RR_TIMEOUT,
        read_timeout=RR_TIMEOUT
    )
    if allowed_methods is not None:
        base["allowed_methods"] = allowed_methods
    return base
