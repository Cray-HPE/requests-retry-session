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
import sys

from .defs import NOTICE_LOG_LEVEL
from .test import run_all_tests

LOG_FORMAT = "%(asctime)-15s - %(process)d - %(thread)d - %(levelname)-7s - %(name)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s"
LOG_FILE = "test_rrs.log"

def notice(self, msg, *args, **kwargs):
    if self.isEnabledFor(NOTICE_LOG_LEVEL):
        self._log(NOTICE_LOG_LEVEL, msg, args, **kwargs)

if __name__ == '__main__':
    logging.addLevelName(NOTICE_LOG_LEVEL, "NOTICE")
    logging.Logger.notice = notice

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)   # Capture everything at the root

    log_formatter = logging.Formatter(LOG_FORMAT)

    # --- File handler: log everything ---
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_formatter)

    # --- Screen handler: only errors ---
    screen_handler = logging.StreamHandler(sys.stderr)
    screen_handler.setLevel(logging.ERROR)
    screen_handler.setFormatter(log_formatter)

    # Attach both handlers
    logger.addHandler(file_handler)
    logger.addHandler(screen_handler)

    sys.exit(run_all_tests())
