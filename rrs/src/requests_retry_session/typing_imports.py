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

This module is also symbolically linked into the test-rrs package.
"""

import sys

# collections.abc.Callable/Container/Iterable/etc made parameterizable in Python 3.9
# Literal, Protocol, TypedDict, final, get_args, runtime_checkable added to typing in 3.9
if sys.version_info < (3, 9):
    from typing import (
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
    from typing_extensions import (
        Literal,
        Protocol,
        TypedDict,
        final,
        runtime_checkable,
    )
    from collections.abc import Iterable as IterableProtocol

    # Not even typing_extensions has get_args in this version, so
    # we have to define a hack version ourselves
    from enum import Enum
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Any, List, Tuple, Union
        from typing_extensions import TypeAlias
        LiteralValue: "TypeAlias" = Union[bool, int, str, bytes, Enum, None]

    def get_args(literal: "Any") -> "Tuple[LiteralValue, ...]":
        """
        Returns the list of items used to create a literal.
        Notes:
        - This relies on how Literal is implemented internally. I have
          confirmed that it works for all versions of typing_extensions
          available for Python 3.6 that include Literal (3.7.2+).
          They no longer update typing_extensions for Python 3.6,
          so we can assume that this will not change.
        - The type signature for this function is much broader
          than it "should" be, but unfortunately there is no way to
          define it more accurately in a way that mypy will accept.
        """
        assert hasattr(literal, "__values__")
        assert isinstance(literal.__values__, tuple)
        value_list: "List[LiteralValue]" = []
        for val in literal.__values__:
            if val is None:
                value_list.append(val)
                continue
            if isinstance(val, (bool, int, str, bytes, Enum)):
                value_list.append(val)
                continue
            # It is possible to have another Literal inside a Literal
            value_list.extend(get_args(val))
        return tuple(value_list)

else:
    # Python 3.9+
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
        Protocol,
        TypedDict,
        final,
        get_args,
        runtime_checkable,
    )
    # In order to keep the code common for Python 3.6, we define
    # a separate IterableProtocol variable, which in Python 3.9+
    # is the same as what we imported from collections.abc
    IterableProtocol = Iterable


# ParamSpec*, TypeAlias, and TypeGuard was added to typing in 3.10
if sys.version_info < (3, 10):
    from typing_extensions import (
        ParamSpec,
        ParamSpecArgs,
        ParamSpecKwargs,
        TypeAlias,
        TypeGuard,
    )
else:
    # Python 3.10+
    from typing import (
        ParamSpec,
        ParamSpecArgs,
        ParamSpecKwargs,
        TypeAlias,
        TypeGuard,
    )


# Self, TypeVarTuple were added to typing in 3.11
if sys.version_info < (3, 11):
    from typing_extensions import Self, TypeVarTuple
else:
    # Python 3.11+
    from typing import Self, TypeVarTuple


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
    "final",
    "get_args",
    "runtime_checkable",
]


# Unpack added to typing in 3.11
# Unpack was not available even in typing_extensions for 3.6.
# However, it is only used for type checking, which should not be
# running on Python 3.6.
#
# get_args was in typing in 3.9, but not even in typing_extensions for 3.6
if sys.version_info >= (3, 9):
    # pylint is uneasy when it comes to appending to __all__, so we
    # have to quiet its false alarms here
    if sys.version_info < (3, 11):
        # Python 3.9 and 3.10
        from typing_extensions import Unpack  # pylint: disable=unused-import
    else:
        # Python 3.11+
        from typing import Unpack  # pylint: disable=unused-import
    __all__.append('Unpack')
