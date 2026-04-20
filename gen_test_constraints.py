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
Reads in test_constraint_combinations.dat
Based on value of PY_VERSION environment variable,
prints out every valid constraint combination, one per line
(this will always include the null constraint -- that is, no
constraints)
"""

from itertools import combinations
from os import environ
import sys
# In order to be compatible with older Python versions, use old-style type hinting
# for built-in types.
# Also note that Iterable is imported from typing instead of collections.abc because
# in Python 3.6, only typing.Iterable supported type subscripting.
from typing import Generator, Iterable, Set, TypeVar

# The older Python version we care about is 3.6, the highest is 3.13, and
# our environment does not have 3.7 or 3.8. This definition (and
# test_constraint_combinations.dat) should be updated if any of this changes.
PY_VERSIONS = frozenset({ '3.6', '3.9', '3.10', '3.11', '3.12', '3.13' })

INFILE="test_constraint_combinations.dat"

T = TypeVar('T')

def print_err(s) -> None:
    sys.stderr.write(f"ERROR: {s}\n")

def power_sets(s: Iterable[T]) -> Generator[Set[T], None, None]:
    """
    Yields all members of the power set of the set s, as sets.
    This includes s itself (as a set) and the empty set (as a set).
    """
    i=0
    while i <= len(s):
        for combo in combinations(s, i):
            yield frozenset(combo)
        i+=1

def main() -> int:
    try:
        pyver = environ['PY_VERSION']
    except KeyError:
        print_err("PY_VERSION env variable not set")
        return 1
    if pyver not in PY_VERSIONS:
        print_err(f"Invalid PY_VERSION env variable value: '{pyver}'\nValid values: {PY_VERSIONS}")
        return 1

    all_constraints = set()
    with open(INFILE, "rt") as f:
        for lnum, line in enumerate(f, 1):
            if line[0] == "#":
                # skip commented lines
                continue
            if "|" not in line:
                print_err(f"Line {lnum} in {INFILE} has no '|' character")
                return 1
            line_fields = line.split('|')
            line_pyvers = line_fields[0].split()
            if 'all' not in line_pyvers and pyver not in line_pyvers:
                # This line does not apply to our Python version
                continue
            line_constraints = { const.strip() for const in line_fields[1:] }
            # Remove empty constraint, if present (it is not needed)
            if '' in line_constraints:
                line_constraints.remove('')
            for constraint_set in power_sets(line_constraints):
                all_constraints.add(' '.join(sorted(constraint_set)))
    for const in sorted(all_constraints):
        print(const)
    return 0

if __name__ == '__main__':
    sys.exit(main())
