#
# MIT License
#
# (C) Copyright 2024 Hewlett Packard Enterprise Development LP
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
# If you wish to perform a local build, you will need to clone or copy the contents of the
# cms-meta-tools repo to ./cms_meta_tools

NAME ?= requests-retry-session
RPM_VERSION ?= $(shell head -1 .version)
RPM_NAME ?= ${NAME}

SPEC_FILE ?= ${NAME}.spec
BUILD_METADATA ?= "1~development~$(shell git rev-parse --short HEAD)"
SOURCE_NAME ?= ${RPM_NAME}-${RPM_VERSION}
SOURCE_BASENAME := ${SOURCE_NAME}.tar.bz2
BUILD_DIR ?= $(PWD)/dist/rpmbuild
SOURCE_PATH := ${BUILD_DIR}/SOURCES/${SOURCE_BASENAME}
PYTHON_BIN := python$(PY_VERSION)
PYLINT_VENV_BASE_DIR ?= pylint-venv
PYLINT_VENV ?= $(PYLINT_VENV_BASE_DIR)/$(PY_VERSION)
PYLINT_VENV_PYBIN ?= $(PYLINT_VENV)/bin/python3
PIP_INSTALL_ARGS ?= --trusted-host arti.hpc.amslabs.hpecorp.net --trusted-host artifactory.algol60.net --index-url https://arti.hpc.amslabs.hpecorp.net:443/artifactory/api/pypi/pypi-remote/simple --extra-index-url http://artifactory.algol60.net/artifactory/csm-python-modules/simple --no-cache

all : runbuildprep lint pymod
rpm: rpm_prepare rpm_package_source rpm_build_source rpm_build
pymod: pymod_build pymod_validate
pymod_validate: pymod_validate_setup pymod_validate_pylint_error pymod_validate_pylint_full pymod_validate_mypy

runbuildprep:
		./cms_meta_tools/scripts/runBuildPrep.sh

lint:
		./cms_meta_tools/scripts/runLint.sh

pymod_build:
		$(PYTHON_BIN) --version
		$(PYTHON_BIN) -m pip install --upgrade --user pip build setuptools wheel
		$(PYTHON_BIN) -m build --sdist
		$(PYTHON_BIN) -m build --wheel
		cp ./dist/requests_retry_session*.whl .

pymod_validate_setup:
		$(PYTHON_BIN) --version
		mkdir -p $(PYLINT_VENV_BASE_DIR)
		$(PYTHON_BIN) -m venv $(PYLINT_VENV)
		$(PYLINT_VENV_PYBIN) -m pip install --upgrade $(PIP_INSTALL_ARGS) pip
		$(PYLINT_VENV_PYBIN) -m pip install --disable-pip-version-check $(PIP_INSTALL_ARGS) -r validate-requirements.txt requests_retry_session*.whl
		$(PYLINT_VENV_PYBIN) -m pip list --format freeze

pymod_validate_pylint_error:
		$(PYLINT_VENV_PYBIN) -m pylint --errors-only requests_retry_session

pymod_validate_pylint_full:
		$(PYLINT_VENV_PYBIN) -m pylint --disable missing-module-docstring --fail-under 9 requests_retry_session

pymod_validate_mypy:
		$(PYLINT_VENV_PYBIN) -m mypy requests_retry_session

rpm_prepare:
		rm -rf $(BUILD_DIR)
		mkdir -p $(BUILD_DIR)/SPECS $(BUILD_DIR)/SOURCES
		cp $(SPEC_FILE) $(BUILD_DIR)/SPECS/

rpm_package_source:
		touch $(SOURCE_PATH)
		tar --transform 'flags=r;s,^,/$(SOURCE_NAME)/,' \
			--exclude .git \
			--exclude .requests_retry_session.egg-info \
			--exclude .github \
			--exclude .mypy_cache \
			--exclude ./cms_meta_tools \
			--exclude ./build \
			--exclude ./dist \
            --exclude ./'$(PYLINT_VENV_BASE_DIR)' \
			--exclude '$(SOURCE_BASENAME)' \
			-cvjf $(SOURCE_PATH) .

rpm_build_source:
		RPM_NAME=$(RPM_NAME) PYTHON_BIN=$(PYTHON_BIN) BUILD_METADATA=$(BUILD_METADATA) rpmbuild -bs $(SPEC_FILE) --target $(RPM_ARCH) --define "_topdir $(BUILD_DIR)"

rpm_build:
		RPM_NAME=$(RPM_NAME) PYTHON_BIN=$(PYTHON_BIN) BUILD_METADATA=$(BUILD_METADATA) rpmbuild -ba $(SPEC_FILE) --target $(RPM_ARCH) --define "_topdir $(BUILD_DIR)"
