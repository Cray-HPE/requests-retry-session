%define doc_dir /usr/share/doc/%(echo $NAME)/
%define install_dir /usr/lib/%(echo $NAME)/
%define install_python_dir %{install_dir}libcsm-venv

# Define which Python flavors python-rpm-macros will use (this can be a list).
# https://github.com/openSUSE/python-rpm-macros#terminology
%define pythons %(echo $PYTHON_BIN)

# python*-devel is not listed because we do not ship the ability to rebuild our PIP package.
AutoReqProv: no
BuildRequires: python-rpm-generators
BuildRequires: python-rpm-macros
Requires: python%{python_version_nodots}-base
Name: %(echo $NAME)
BuildArch: %(echo $ARCH)
License: MIT License
#Summary:
Version: %(echo $VERSION)
Release: %{echo $RELEASE)
Source: %{name}-%{version}.tar.bz2
#Vendor:
Obsoletes: %{python_flavor}-%{name}

%description

%prep
%setup

%build
%python_exec -m build --sdist
%python_exec -m build --wheel

%install

# Create our virtualenv
%python_exec -m virtualenv --no-periodic-update %{buildroot}%{install_python_dir}

# Build a source distribution.
%{buildroot}%{install_python_dir}/bin/python -m pip install --disable-pip-version-check --no-cache ./dist/*.whl

# Remove build tools to decrease the virtualenv size.
%{buildroot}%{install_python_dir}/bin/python -m pip uninstall -y pip setuptools wheel

# Fix the virtualenv activation script, ensure VIRTUAL_ENV points to the installed location on the system.
find %{buildroot}%{install_python_dir}/bin -type f | xargs -t -i sed -i 's:%{buildroot}%{install_python_dir}:%{install_python_dir}:g' {}

find %{buildroot}%{install_python_dir} | sed 's:'${RPM_BUILD_ROOT}'::' | tee INSTALLED_FILES
cat INSTALLED_FILES | xargs -i sh -c 'test -f $RPM_BUILD_ROOT{} && echo {} || echo %dir {}' | sort -u > FILES

%clean

%files -f FILES
%docdir %{doc_dir}
%doc README.adoc
%defattr(755,root,root)
%dir %{install_dir}
%license LICENSE

%changelog
