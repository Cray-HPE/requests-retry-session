#!/usr/bin/env bash

set -x

zypper --non-interactive ar --no-gpgcheck https://download.opensuse.org/tumbleweed/repo/oss/repodata tumbleweed/repo/oss/repodata
zypper --non-interactive in python-rpm-macros
zypper --non-interactive in python3-rpm-macros
zypper --non-interactive in pyproject-rpm-macros

rpm -a | grep -E 'rpm|macro'
rpm --eval '%pyproject_save_files foo'
rpm -q --whatprovides 'rpm_macro(pyproject_save_files)'

exit 0
