# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.10] - 2026-04-14

### Fixed

- When creating RPM source tarball, adjust `tar` command to avoid superfluous `/./` in file paths,
  since that apparently breaks something in the Python 3.13 RPM build environment (and is, as noted,
  superfluous)

## [0.1.9] - 2026-04-13

### Changed
- Specified minimum dependency versions for specific Python versions, based on basic testing.
  This is not a statement that these versions have been thoroughly vetted, just that lower versions
  will definitely not work.

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
