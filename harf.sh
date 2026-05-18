#!/usr/bin/env bash

rpm -a | grep -E 'rpm|macro'
rpm --eval '%pyproject_save_files foo'
rpm -q --whatprovides 'rpm_macro(pyproject_save_files)'

exit 0
