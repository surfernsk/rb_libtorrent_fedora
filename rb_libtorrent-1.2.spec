%if 0%{?fedora} || 0%{?rhel} >= 8
%bcond_without python3
%else
%bcond_with python3
%endif

Name:		rb_libtorrent
Version:	1.2.12
Release:	1%{?dist}
Summary:	A C++ BitTorrent library aiming to be the best alternative

License:	BSD
URL:		https://www.libtorrent.org
Source0:	https://github.com/arvidn/libtorrent/releases/download/v%{version}/libtorrent-rasterbar-%{version}.tar.gz
Source1:	%{name}-README-renames.Fedora
Source2:	%{name}-COPYING.Boost
Source3:	%{name}-COPYING.zlib

%if 0%{?rhel} && 0%{?rhel} < 8
# aarch64 is broken and I have zero interest in fixing it
ExcludeArch:	aarch64
%endif

BuildRequires:	asio-devel
BuildRequires:	cmake
BuildRequires:	gcc-c++
BuildRequires:	ninja-build
BuildRequires:	openssl-devel
BuildRequires:	pkgconfig(zlib)
%if 0%{?fedora} < 31 && 0%{?rhel} < 8
BuildRequires:	pkgconfig(python2)
%endif
BuildRequires:	util-linux

%description
%{name} is a C++ library that aims to be a good alternative to all
the other BitTorrent implementations around. It is a library and not a full
featured client, although it comes with a few working example clients.

Its main goals are to be very efficient (in terms of CPU and memory usage) as
well as being very easy to use both as a user and developer.

%package 	devel
Summary:	Development files for %{name}
License:	BSD and zlib and Boost
Requires:	%{name}%{?_isa} = %{version}-%{release}
## FIXME: Same include directory. :(
Conflicts:	libtorrent-devel
## Needed for various headers used via #include directives...
Requires:	asio-devel
Requires:	boost-devel
Requires:	pkgconfig(openssl)
Requires:	pkgconfig(geoip)

%description	devel
The %{name}-devel package contains libraries and header files for
developing applications that use %{name}.

The various source and header files included in this package are licensed
under the revised BSD, zlib/libpng, and Boost Public licenses. See the various
COPYING files in the included documentation for the full text of these
licenses, as well as the comments blocks in the source code for which license
a given source or header file is released under.

%package	examples
Summary:	Example clients using %{name}
License:	BSD
Requires:	%{name}%{?_isa} = %{version}-%{release}

%description	examples
The %{name}-examples package contains example clients which intend to
show how to make use of its various features. (Due to potential
namespace conflicts, a couple of the examples had to be renamed. See the
included documentation for more details.)

%if 0%{?fedora} < 31 && 0%{?rhel} < 8
%package	python2
Summary:	Python bindings for %{name}
License:	Boost
BuildRequires:	python2-devel
%if 0%{?fedora} > 28
BuildRequires:	boost-python2-devel
%endif
BuildRequires:	python2-setuptools
Requires:	%{name}%{?_isa} = %{version}-%{release}
Provides:	%{name}-python
Obsoletes:	%{name}-python < 1.0.9

%description	python2
The %{name}-python2 package contains Python language bindings
(the 'libtorrent' module) that allow it to be used from within
Python applications.
%endif

%if %{with python3}
%package	python3
Summary:	Python bindings for %{name}
License:	Boost
BuildRequires:	python3-devel
BuildRequires:	pkgconfig(python3)
BuildRequires:	boost-python3-devel
BuildRequires:	python3-setuptools
Requires:	%{name}%{?_isa} = %{version}-%{release}

%description	python3
The %{name}-python3 package contains Python language bindings
(the 'libtorrent' module) that allow it to be used from within
Python applications.
%endif # with python3

%prep
%setup -q -n "libtorrent-rasterbar-%{version}"

## The RST files are the sources used to create the final HTML files; and are
## not needed.
rm -f docs/*.rst
## Ensure that we get the licenses installed appropriately.
install -p -m 0644 COPYING COPYING.BSD
install -p -m 0644 %{SOURCE2} COPYING.Boost
install -p -m 0644 %{SOURCE3} COPYING.zlib
## Finally, ensure that everything is UTF-8, as it should be.
iconv -t UTF-8 -f ISO_8859-15 AUTHORS -o AUTHORS.iconv
mv AUTHORS.iconv AUTHORS

%build
mkdir -p build build-python3
%if 0%{?fedora} < 31 && 0%{?rhel} < 8
# Build the lib with Python 2 bindings
export PYTHON=/usr/bin/python%{python2_version}
pushd build
%cmake3 \
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \
	-DCMAKE_CXX_STANDARD=14 \
	-GNinja \
	-Dbuild_examples=ON \
	-Dbuild_tests=ON \
	-Dbuild_tools=ON \
	-Dpython-bindings=ON \
	-Dpython-egg-info=ON \
	-Dpython-install-system-dir=ON \
	-DPYTHON_EXECUTABLE:FILEPATH=/usr/bin/python%{python2_version} \
	..
pushd %{_host}*
%ninja_build
popd
popd
%endif

%if 0%{?with_python3}
# This is ugly but can't think of an easier way to build the binding
export CPPFLAGS="$CPPFLAGS $(python%{python3_version}-config --includes)"
export LDFLAGS="$LDFLAGS -L%{_builddir}/libtorrent-rasterbar-%{version}/build/src/.libs"
export PYTHON=/usr/bin/python%{python3_version}
export PYTHON_LDFLAGS="$PYTHON_LDFLAGS $(python%{python3_version}-config --libs)"

pushd build-python3
%cmake3 \
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \
	-DCMAKE_CXX_STANDARD=14 \
	-GNinja \
	-Dbuild_examples=ON \
	-Dbuild_tests=ON \
	-Dbuild_tools=ON \
	-Dpython-bindings=ON \
	-Dpython-egg-info=ON \
	-Dpython-install-system-dir=ON \
	..

pushd %{_host}*
%ninja_build
popd
popd
%endif # with_python3

%check
%if 0%{?fedora} < 31 && 0%{?rhel} < 8
pushd build/%{_host}*/test
# Skip UPnP test as it requires a UPnP server on the same network, others due to aarch64 failures
echo "set (CTEST_CUSTOM_TESTS_IGNORE
  "test_upnp"
  "test_flags"
  "test_torrent"
  "test_resume"
)" > CTestCustom.cmake
ctest %{?_smp_mflags}
popd
%endif
%if 0%{?with_python3}
pushd build-python3/%{_host}*/test
# Skip UPnP test as it requires a UPnP server on the same network, others due to aarch64 failures
echo "set (CTEST_CUSTOM_TESTS_IGNORE
  "test_upnp"
  "test_flags"
  "test_torrent"
  "test_resume"
)" > CTestCustom.cmake
ctest
popd
%endif

%install
mkdir -p %{buildroot}%{_bindir}/

%if 0%{?fedora} < 31 && 0%{?rhel} < 8
pushd build/%{_host}*
%ninja_install
install -p -m 0755 \
 examples/{client_test,connection_tester,custom_storage,dump_torrent,make_torrent,simple_client,stats_counters,upnp_test} \
 tools/{dht,session_log_alerts} \
 %{buildroot}%{_bindir}/
popd
sed -i 's/Version:.*/Version: %{version}/' %{python2_sitearch}/libtorrent.egg-info/PKG-INFO
%endif

%if 0%{?with_python3}
pushd build-python3/%{_host}*
%ninja_install
install -p -m 0755 \
 examples/{client_test,connection_tester,custom_storage,dump_torrent,make_torrent,simple_client,stats_counters,upnp_test} \
 tools/{dht,session_log_alerts} \
 %{buildroot}%{_bindir}/
popd
# Written version is malformed
sed -i 's/^Version:.*/Version: %{version}/' %{buildroot}%{python3_sitearch}/libtorrent.egg-info/PKG-INFO
%endif # with python3

## Do the renaming due to the somewhat limited %%_bindir namespace.
rename client torrent_client %{buildroot}%{_bindir}/*

install -p -m 0644 %{SOURCE1} ./README-renames.Fedora

%ldconfig_scriptlets

%files
%{!?_licensedir:%global license %doc}
%doc AUTHORS ChangeLog
%license COPYING
%{_libdir}/libtorrent-rasterbar.so.1.*
%{_libdir}/libtorrent-rasterbar.so.10

%files	devel
%doc docs/
%license COPYING.Boost COPYING.BSD COPYING.zlib
%{_libdir}/pkgconfig/libtorrent-rasterbar.pc
%{_includedir}/libtorrent/
%{_libdir}/libtorrent-rasterbar.so
%{_libdir}/cmake/LibtorrentRasterbar/
%{_datadir}/cmake/Modules/FindLibtorrentRasterbar.cmake

%files examples
%doc README-renames.Fedora
%license COPYING
%{_bindir}/*torrent*
%{_bindir}/connection_tester
%{_bindir}/custom_storage
%{_bindir}/dht
%{_bindir}/session_log_alerts
%{_bindir}/stats_counters
%{_bindir}/upnp_test

%if 0%{?fedora} < 31 && 0%{?rhel} < 8
%files	python2
%doc AUTHORS ChangeLog
%license COPYING.Boost
%{python2_sitearch}/libtorrent.egg-info/
%{python2_sitearch}/libtorrent.so
%endif

%if 0%{?with_python3}
%files	python3
%doc AUTHORS ChangeLog
%license COPYING.Boost
%{python3_sitearch}/libtorrent.egg-info/
%{python3_sitearch}/libtorrent.cpython-*.so
%endif # with python3

%changelog
* Fri Mar 26 2021 Evgeny Lensky <surfernsk@gmail.com> - 1.2.12-1
- release 1.2.12

* Thu Nov 26 2020 Evgeny Lensky <surfernsk@gmail.com> - 1.2.11-1
- release 1.2.11

* Sat Mar 14 2020 leigh123linux <leigh123linux@googlemail.com> - 1.2.5-1
- Upgrade to 1.2.5
