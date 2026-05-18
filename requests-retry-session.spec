# Copyright 2024-2026 Hewlett Packard Enterprise Development LP
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
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# (MIT License)

# Define which Python flavors python-rpm-macros will use (this can be a list).
# https://github.com/openSUSE/python-rpm-macros#terminology
%define pythons %(echo ${PYTHON_BIN})
%define py_version %(echo ${PY_VERSION})

# Wheel already built and provided
%define wheelfile requests_retry_session-%{version}-py3-none-any.whl


Name: %(echo ${RPM_NAME})
License: MIT
Summary: The requests-retry-session Python package for Python %{py_version}
Group: System/Management
Version: %(cat .version)
Release: %(cat .rpm_release)
Source: %{name}-%{version}.tar.bz2
BuildArch: %(echo ${RPM_ARCH})
Vendor: Cray Inc.
# Using or statements in spec files requires RPM >= 4.13
BuildRequires: rpm-build >= 4.13
Requires: rpm >= 4.13
BuildRequires: (python%{python_version_nodots}-devel or python3-devel >= %{py_version})
BuildRequires: (python%{python_version_nodots}-pip or python3-pip >= %{py_version})
BuildRequires: python-rpm-generators
BuildRequires: python-rpm-macros

%description
The requests-retry-session Python package for Python %{py_version}

%prep
# Just unpack the wheel
%autosetup

%build

%install

# Install wheel into buildroot
%python3 -m pip install \
    --no-deps \
    --root %{buildroot} \
    --prefix %{_prefix} \
    %{wheelfile}

%pyproject_save_files requests_retry_session

%check
# Optional: could import to verify
%python3 -c "import requests_retry_session"

%files -n %(echo ${RPM_NAME}) -f %{pyproject_files}
%defattr(-,root,root)

%license LICENSE
