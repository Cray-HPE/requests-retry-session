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

from test_rrs.rrs_lib import RR_STATUS_FORCELIST, RR_TIMEOUT


# How long to have the test server delay responses in order to provoke the
# request to time out
TIMEOUT_DELAY = 1.5 * RR_TIMEOUT

# "Good" status codes that should not trigger retries
GOOD_SCS = tuple(x for x in range(210, 300) if x not in RR_STATUS_FORCELIST)

# "Bad" status codes that should not trigger retries
# Make sure to start with 502, since that is one of the default values for retry-able
# status codes in RRS. If there is a bug where the defaults are being used even though
# our test specifies a different list, this may help detect it.
BAD_NORETRY_SCS = tuple(x for x in range(502, 600) if x not in RR_STATUS_FORCELIST)
