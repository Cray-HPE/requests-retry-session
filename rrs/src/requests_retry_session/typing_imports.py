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

In later Python versions, this file is redundant, but it is retained to keep the
rest of the code base as common as possible with previous Python versions

This module is also symbolically linked into the test-rrs package.
"""

# Python 3.11+
from collections.abc import (
    Callable,
    Collection,
    Container,
    Generator,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
)
from typing import (
    Literal,
    ParamSpec,
    ParamSpecArgs,
    ParamSpecKwargs,
    Protocol,
    Self,
    TypeAlias,
    TypeGuard,
    TypeVarTuple,
    TypedDict,
    Unpack,
    final,
    get_args,
    runtime_checkable,
)
# In order to keep the code common for Python 3.6, we define
# a separate IterableProtocol variable, which in Python 3.9+
# is the same as what we imported from collections.abc
IterableProtocol = Iterable


# Explicitly re-export
__all__ = [
    "Callable",
    "Collection",
    "Container",
    "Generator",
    "Iterable",
    "IterableProtocol",
    "Iterator",
    "Literal",
    "Mapping",
    "MutableMapping",
    "MutableSequence",
    "MutableSet",
    "ParamSpec",
    "ParamSpecArgs",
    "ParamSpecKwargs",
    "Protocol",
    "Self",
    "Sequence",
    "TypeAlias",
    "TypeGuard",
    "TypeVarTuple",
    "TypedDict",
    "Unpack",
    "final",
    "get_args",
    "runtime_checkable",
]
