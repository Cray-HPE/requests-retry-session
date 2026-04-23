# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [4.1.2] - 2026-04-23

### Added
- Added tests for `allowed_methods` and specifying multiple protocols
- Added timeout tests

### Changed
- Refactored tests for clarity

### Fixed
- Fixed bug in `TimeoutHTTPAdapter` preventing timeouts from happening

### Dependencies
- Raise minimum required versions for `requests` (to `2.25`) and
  `urllib3` (to `1.26`) for all Python versions, to support `allowed_methods` `Retry`
  argument.

## [4.1.1] - 2026-04-17

### Added
- Added basic build time tests to catch bugs that break the module in a basic way,
  for any of the supported Python versions

### Changed
- Removed dependence on Retry.DEFAULT_ALLOWED_METHODS

## [4.1.0] - 2026-04-15

### Changed
- Changed default protocol from `http` to both `http` and `https`.
  This is a BREAKING CHANGE for anyone relying on the previous default behavior.

### Removed
- Removed callback functionality from `RetryWithLogs`.
  This is a BREAKING CHANGE for anyone using that option.

## [4.0.2] - 2026-04-15

### Added
- Added support for `allowed_methods` argument, to allow retries for non-default
  methods like `PATCH` and `POST`.
- Added comments explaining that protocol arguments must omit the trailing "://"
- Added explicit type annotations for `TimeoutHTTPAdapter.__init__()`
- Add `ProtocolType`, `StatusForcelistType` to simplify type annotations
- Added support for specifying multiple protocols

### Changed
- Changed type hint for timeout arguments from `int` to `float` (`float` values
  already work fine, except for raising type check errors)
- Change `Optional` to `| None` since all supported Python versions allow this syntax.
- Mark type definitions with `type` keyword

## [4.0.1] - 2026-04-14

### Fixed
- When creating RPM source tarball, adjust `tar` command to avoid superfluous `/./` in file paths,
  since that apparently breaks something in the Python 3.13 RPM build environment (and is, as noted,
  superfluous)
- Disable `mypy` caching to avoid build failures

### Changed
- Specified minimum dependency versions for specific Python versions, based on basic testing.
  This is not a statement that these versions have been thoroughly vetted, just that lower versions
  will definitely not work.

## [4.0.0] - 2025-07-02

### Removed
- Removed support for Python 3.11

## [3.0.0] - 2025-07-02

### Removed
- Removed support for Python 3.10

## [2.0.3] - 2025-06-27

### Added
- Add support for Python 3.13

### Changed
- Specify minimum `typing_extensions` version (based on what we are using from it)

### Dependencies
- Bump `dangoslen/dependabot-changelog-helper` from 3 to 4 ([#27](https://github.com/Cray-HPE/requests-retry-session/pull/27))

## [2.0.2] - 2025-05-05

### Changed
- CASMCMS-9410: Add `TYPE_CHECKING`-only code in `RetrySessionManager` to work around  https://github.com/python/typing/issues/1992

## [2.0.1] - 2024-12-06

### Fixed
- Exclude mypy cache from RPM source tarball

## [2.0.0] - 2024-12-06

### Removed
- Removed support for Python 3.9

## [1.0.1] - 2024-12-06

### Added
- Added mylint and pypy to build pipeline

## [1.0.0] - 2024-12-06

### Removed
- Removed support for Python 3.6

## [0.2.2] - 2024-12-04

### Fixed
- Fixed syntax error in requests_retry_manager function

## [0.2.1] - 2024-12-04

### Added
- Added context manager function to handle closing both the session and adapter.

## [0.2.0] - 2024-12-03

### Added
- Added standalone functions to create http adapters, to allow them to be closed by the caller.
- Created `RetrySessionManager` context manager class.

## [0.1.8] - 2024-10-10

### Fixed
- Corrected type hint to variable-length int tuple

## [0.1.7] - 2024-10-10

### Added
- Added `py.typed` file to package

## [0.1.6] - 2024-10-10

### Changed
- Add type hints to externally-facing function

### Dependencies
- Bump `tj-actions/changed-files` from 44 to 45 ([#22](https://github.com/Cray-HPE/requests-retry-session/pull/22))

## [0.1.5] - 2024-08-21
### Changed
- Change how RPM release value is set

## [0.1.4] - 2024-08-20

### Added
- Build RPMs to install module to system Python directory (for various Python versious)

### Changed
- Change required minimum Python version to 3.6

## [0.1.3] - 2024-08-16

### Added
- Ported `RetryWithLogs` class over from `cfs-trust`

### Dependencies
- Bump `tj-actions/changed-files` from 42 to 44 ([#17](https://github.com/Cray-HPE/requests-retry-session/pull/17))

## [0.1.2]

### Fixed
- Address problems with PR checkers

## [0.1.1]

### Fixed
- Fix module name

## [0.1.0]

### Added
- Initial version
