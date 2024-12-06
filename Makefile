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

all : runbuildprep lint pymod
rpm: rpm_prepare rpm_package_source rpm_build_source rpm_build

runbuildprep:
		./cms_meta_tools/scripts/runBuildPrep.sh

lint:
		./cms_meta_tools/scripts/runLint.sh

pymod:
		python3 --version
		python3 -m pip install --upgrade --user pip build setuptools wheel
		python3 -m build --sdist
		python3 -m build --wheel
		cp ./dist/requests_retry_session*.whl .

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
			--exclude $(SOURCE_BASENAME) \
			-cvjf $(SOURCE_PATH) .

rpm_build_source:
		RPM_NAME=$(RPM_NAME) PYTHON_BIN=$(PYTHON_BIN) BUILD_METADATA=$(BUILD_METADATA) rpmbuild -bs $(SPEC_FILE) --target $(RPM_ARCH) --define "_topdir $(BUILD_DIR)"

rpm_build:
		RPM_NAME=$(RPM_NAME) PYTHON_BIN=$(PYTHON_BIN) BUILD_METADATA=$(BUILD_METADATA) rpmbuild -ba $(SPEC_FILE) --target $(RPM_ARCH) --define "_topdir $(BUILD_DIR)"
