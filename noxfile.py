from pathlib import Path
import sys

import nox

# Get project root directory
if getattr(sys, "frozen", False) and hasattr(
    sys,
    "_MEIPASS"
):  # pragma: no cover
    project_root = sys._MEIPASS
else:
    prog = __file__
    project_root = Path(__file__).resolve().parent

COVERAGE_FAIL = 85
ERROR_ON_GENERATE = True
locations = '@@MYPROJECT@@'
nox.options.sessions = 'test', 'docs', 'lint', 'cover'


@nox.session(python='3')
def test(session):
    """Default unit test session."""
    session.install('.[test]')
    session.install('.')

    # Run pytest against the tests.
    session.run(
        'pytest',
        '--quiet',
        f'--cov={locations}',
        '--cov-append',
        '--cov-report=',
        f'--cov-fail-under={COVERAGE_FAIL}',
        '.',
        success_codes=[0, 5],
    )


@nox.session(python='3')
def lint(session):
    """Run flake8 linter and plugins."""
    session.install(".[lint]")
    session.install(".[test]")
    session.install(".")
    session.run("ruff", "check", f"{locations}/")

@nox.session(python='3')
def cover(session):
    """Run the final coverage report."""
    session.install('.[test]')
    session.install('.')
    session.run(
        'coverage',
        'report',
        '--show-missing',
        f'--fail-under={COVERAGE_FAIL}',
        success_codes=[0, 5]
    )
    session.run('coverage', 'erase')
