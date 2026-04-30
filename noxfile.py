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
"""Nox definitions for linting, type checks, and tests"""

from __future__ import absolute_import
import nox  # pylint: disable=import-error

PYTHON = ["3"]


@nox.session(python=PYTHON)
def lint(session):
    """Run linters.
    Run Pylint and Pycodestyle against src and tests.
    Returns a failure if the linters find linting errors or sufficiently
    serious code quality issues.
    """
    session.install("./rrs[lint]","./test-rrs[lint]")
    session.install("./rrs","./test-rrs")
    session.run("pip","list","--format","freeze")
    session.log("Running pylint...")
    session.run("pylint", "--rcfile=.pylintrc", "requests_retry_session", "test_rrs")

    session.log("Running pycodestyle...")
    session.run("pycodestyle", "--config=.pycodestyle", "rrs/src", "test-rrs/src")


@nox.session(python=PYTHON)
def type_check(session):
    """Run Mypy with config."""
    assert len(session.posargs) == 1
    label = f"type_check{session.posargs[0]}"
    session.install(f"./rrs[{label}]", "./test-rrs[type_check]")
    if label == "type_check2":
        session.install("./vendor/cray_types_urllib3-1.26.25.14.1-py3-none-any.whl")
    session.install("./rrs", "./test-rrs")
    session.run("pip","list","--format","freeze")
    session.log("Running mypy...")
    session.run("mypy", "--strict", "-p", "requests_retry_session", "-p", "test_rrs")
