# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Add support for Python 3.13

### Changed
- Specify minimum `typing_extensions` version (based on what we are using from it)

## [0.5.2] - 2025-05-05

### Changed
- CASMCMS-9410: Add `TYPE_CHECKING`-only code in `RetrySessionManager` to work around  https://github.com/python/typing/issues/1992

## [0.5.1] - 2025-02-24

### Fixed
- Fixed typo in `DEFAULT_RETRIES` definition

## [0.5.0] - 2025-01-10

No changes from 0.2.2 below.

## [0.2.2] - 2025-01-10

### Fixed
- Fixed syntax error in requests_retry_manager function
- Exclude mypy cache from RPM source tarball

### Dependencies
- Added constraints to dependency versions

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
