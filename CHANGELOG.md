# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [5.0.0] - 2025-07-02

### Removed
- Removed support for Python 3.12

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
