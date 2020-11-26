%if 0%{?fedora} || 0%{?rhel} >= 8
%bcond_without python3
%else
%bcond_with python3
%endif

# we don't want to provide private python extension libs
%if 0%{?fedora} || 0%{?rhel} >= 7
%global __provides_exclude_from ^(%{python2_sitearch}|%{python3_sitearch})/.*\.so$
%else
%filter_provides_in %{python_sitearch}/.*\.so$
# actually set up the filtering
%filter_setup
%endif


Name:		rb_libtorrent
Version:	1.2.11
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
BuildRequires:	automake
BuildRequires:	autoconf-archive
BuildRequires:	boost-devel
BuildRequires:	gcc-c++
BuildRequires:	openssl-devel
BuildRequires:	pkgconfig(zlib)
%if 0%{?fedora} < 31 && 0%{?rhel} < 8
BuildRequires:	pkgconfig(python2)
%endif
BuildRequires:	libtool
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
%endif

%prep
%setup -q -n "libtorrent-rasterbar-%{version}"
sed -i -e 's|include/libtorrent/version.hpp|../include/libtorrent/version.hpp|' configure configure.ac

# Remove the default debug flags as we provide our own
sed -i -e 's|"-g0 -Os"|""|' configure configure.ac

# Use c++14 to fix LTO issue with qbittorrent 
# qbittorrent: symbol lookup error: qbittorrent: undefined symbol: _ZN10libtorrent5entryC1ESt3mapINSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEES0_NS_3aux12strview_lessESaISt4pairIKS7_S0_EEE
rm m4/ax_cxx_compile_stdcxx.m4 m4/ax_cxx_compile_stdcxx_11.m4
sed -i -e 's|AX_CXX_COMPILE_STDCXX_11|AX_CXX_COMPILE_STDCXX_14|' configure.ac

autoreconf -fiv

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

# safer and less side-effects than using LIBTOOL=/usr/bin/libtool -- Rex
# else, can use the autoreconf -i hammer
%if "%{_libdir}" != "/usr/lib"
sed -i -e 's|"/lib /usr/lib|"/%{_lib} %{_libdir}|' configure
%endif

%build
%define _configure ../configure

mkdir -p build/bindings build-python3/bindings
echo build/bindings build-python3/bindings | xargs -n 1 cp -r bindings/python

%if 0%{?fedora} < 31 && 0%{?rhel} < 8
# Build the lib with Python 2 bindings
export PYTHON=/usr/bin/python%{python2_version}
pushd build
%configure \
	--disable-static \
	--enable-examples \
	--enable-python-binding \
	--with-boost-system=boost_system \
	--with-boost-python=boost_python%{python2_version_nodots} \
	--with-libiconv \
	--enable-export-all
%else
# Build the lib with Python 3 bindings
# This is ugly but can't think of an easier way to build the binding
export CPPFLAGS="$CPPFLAGS $(python%{python3_version}-config --includes)"
export LDFLAGS="$LDFLAGS -L%{_builddir}/libtorrent-rasterbar-%{version}/build/src/.libs"
export PYTHON=/usr/bin/python%{python3_version}
export PYTHON_LDFLAGS="$PYTHON_LDFLAGS $(python%{python3_version}-config --libs)"
pushd build
%configure \
	--disable-static \
	--enable-examples \
	--enable-python-binding \
	--with-boost-system=boost_system \
	--with-boost-python=boost_python%{python3_version_nodots} \
	--with-libiconv \
	--enable-export-all
%endif

make V=1 %{?_smp_mflags}
popd

%if 0%{?with_python3}
# This is ugly but can't think of an easier way to build the binding
export CPPFLAGS="$CPPFLAGS $(python%{python3_version}-config --includes)"
export LDFLAGS="$LDFLAGS -L%{_builddir}/libtorrent-rasterbar-%{version}/build/src/.libs"
export PYTHON=/usr/bin/python%{python3_version}
export PYTHON_LDFLAGS="$PYTHON_LDFLAGS $(python%{python3_version}-config --libs)"

pushd build-python3
%configure \
	--disable-static \
	--enable-examples \
	--enable-python-binding \
	--with-boost-system=boost_system \
	--with-boost-python=boost_python%{python3_version_nodots} \
	--with-libiconv \
	--enable-export-all

pushd bindings/python
make V=1 %{?_smp_mflags}
%endif

#%check
#pushd build
#cp -Rp ../test/mutable_test_torrents ../test/test_torrents ./test/
#cp ../test/*.{cpp,hpp,py,gz} ./test/
#make %{?_smp_mflags} check
#popd

#%if %{with python3}
#pushd build-python3
#cp -Rp ../test/mutable_test_torrents ../test/test_torrents ./test/
#cp ../test/*.{cpp,hpp,py,gz} ./test/
#make %{?_smp_mflags} check
#popd
#%endif

%install
## Ensure that we preserve our timestamps properly.
export CPPROG="%{__cp} -p"

pushd build
%{make_install}
## Do the renaming due to the somewhat limited %%_bindir namespace.
rename client torrent_client %{buildroot}%{_bindir}/*

%if 0%{?fedora} < 31 && 0%{?rhel} < 8
## Install the python 2 binding module.
pushd bindings/python
%{__python2} setup.py install -O1 --skip-build --root %{buildroot}
popd && popd
%else
popd
%endif

%if 0%{?with_python3}
pushd build-python3/bindings/python
%{__python3} setup.py install -O1 --skip-build --root %{buildroot}
popd
%endif

install -p -m 0644 %{SOURCE1} ./README-renames.Fedora

#Remove libtool archives.
find %{buildroot} -name '*.la' -or -name '*.a' | xargs rm -f

%ldconfig_scriptlets

%files
%{!?_licensedir:%global license %doc}
%doc AUTHORS ChangeLog
%license COPYING
%{_libdir}/libtorrent-rasterbar.so.10*

%files	devel
%doc docs/
%license COPYING.Boost COPYING.BSD COPYING.zlib
%{_libdir}/pkgconfig/libtorrent-rasterbar.pc
%{_includedir}/libtorrent/
%{_libdir}/libtorrent-rasterbar.so
%{_datadir}/cmake/Modules/FindLibtorrentRasterbar.cmake

%files examples
%doc README-renames.Fedora
%license COPYING
%{_bindir}/*torrent*
%{_bindir}/bt_ge*
%{_bindir}/connection_tester
%{_bindir}/custom_storage
%{_bindir}/dht_put
%{_bindir}/session_log_alerts
%{_bindir}/stats_counters
%{_bindir}/upnp_test

%if 0%{?fedora} < 31 && 0%{?rhel} < 8
%files	python2
%doc AUTHORS ChangeLog
%license COPYING.Boost
%{python2_sitearch}/python_libtorrent-%{version}-py2.?.egg-info
%{python2_sitearch}/libtorrent.so
%endif

%if 0%{?with_python3}
%files	python3
%doc AUTHORS ChangeLog
%license COPYING.Boost
%{python3_sitearch}/python_libtorrent-%{version}-py3.?.egg-info
%{python3_sitearch}/libtorrent.cpython-*.so
%endif

%changelog
* Thu Nov 26 2020 Evgeny Lensky <surfernsk@gmail.com> - 1.2.11-1
- release 1.2.11

* Sat Mar 14 2020 leigh123linux <leigh123linux@googlemail.com> - 1.2.5-1
- Upgrade to 1.2.5
