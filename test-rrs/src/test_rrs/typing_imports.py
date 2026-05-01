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
Centralized place for Python-version-dependent imports
(to simplify the rest of the files)
"""

import sys

# collections.abc.Callable/Container/Iterable made parameterizable in Python 3.9
# Literal and TypedDict added to typing in 3.9
# TypeAlias was added to typing in 3.10
if sys.version_info >= (3, 10):
    from collections.abc import Callable, Container, Iterable
    from typing import Literal, TypeAlias, TypedDict
elif sys.version_info >= (3, 9):
    from collections.abc import Callable, Container, Iterable
    from typing import Literal, TypedDict
    from typing_extensions import TypeAlias
else:
    from typing import Callable, Container, Iterable
    from typing_extensions import Literal, TypeAlias, TypedDict

# Explicitly re-export everything
__all__ = ["Callable", "Container", "Iterable", "Literal", "TypeAlias", "TypedDict"]
