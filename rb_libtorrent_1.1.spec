%define gtag libtorrent-1_1_6
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
Version:	1.1.6
Release:	1%{?dist}
Summary:	A C++ BitTorrent library aiming to be the best alternative

Group:		System Environment/Libraries
License:	BSD
URL:		http://www.rasterbar.com/products/libtorrent
Source0:	https://github.com/arvidn/libtorrent/releases/download/%{gtag}/libtorrent-rasterbar-%{version}.tar.gz
Source1:	%{name}-README-renames.Fedora
Source2:	%{name}-COPYING.Boost
Source3:	%{name}-COPYING.zlib
Patch0:		%{name}-1.1.2-system-tommath.patch

BuildRequires:	asio-devel
BuildRequires:	boost-devel
BuildRequires:	libtommath-devel
BuildRequires:	pkgconfig(zlib)
BuildRequires:	pkgconfig(python2)
BuildRequires:	libtool
BuildRequires:  util-linux
BuildRequires:  chrpath

%description
%{name} is a C++ library that aims to be a good alternative to all
the other BitTorrent implementations around. It is a library and not a full
featured client, although it comes with a few working example clients.

Its main goals are to be very efficient (in terms of CPU and memory usage) as
well as being very easy to use both as a user and developer.

%package 	devel
Summary:	Development files for %{name}
Group:		Development/Libraries
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
Group:		Applications/Internet
License:	BSD
Requires:	%{name}%{?_isa} = %{version}-%{release}

%description	examples
The %{name}-examples package contains example clients which intend to
show how to make use of its various features. (Due to potential
namespace conflicts, a couple of the examples had to be renamed. See the
included documentation for more details.)

%package	python2
Summary:	Python bindings for %{name}
Group:		Development/Languages
License:	Boost
BuildRequires:  python2-devel
%if 0%{?fedora} > 22
BuildRequires:	python2-setuptools
%else
BuildRequires:	python-setuptools
%endif
Requires:       %{name}%{?_isa} = %{version}-%{release}
Provides:       %{name}-python
Obsoletes:      %{name}-python < 1.0.9

%description	python2
The %{name}-python2 package contains Python language bindings
(the 'libtorrent' module) that allow it to be used from within
Python applications.

%if %{with python3}
%package	python3
Summary:	Python bindings for %{name}
Group:		Development/Languages
License:	Boost
BuildRequires:  python3-devel
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
%patch0 -p1
rm include/libtorrent/tommath* src/mpi.cpp
sed -i -e 's|include/libtorrent/version.hpp|../include/libtorrent/version.hpp|' configure configure.ac

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

# Build the lib with Python 2 bindings
pushd build
%configure \
	--disable-static \
	--enable-examples \
	--enable-python-binding \
	--with-boost-system=boost_system \
	--with-boost-python=boost_python \
	--with-libiconv \
	--enable-export-all

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
	--with-boost-python=boost_python3 \
	--with-libiconv \
	--enable-export-all

pushd bindings/python
make V=1 %{?_smp_mflags}
%endif # with_python3

%check
pushd build
cp -Rp ../test/mutable_test_torrents ../test/test_torrents ./test/
cp ../test/*.{cpp,hpp,py} ./test/
make %{?_smp_mflags} check
popd

%if %{with python3}
pushd build-python3
cp -Rp ../test/mutable_test_torrents ../test/test_torrents ./test/
cp ../test/*.{cpp,hpp,py} ./test/
make %{?_smp_mflags} check
popd
%endif # with python3

%install
## Ensure that we preserve our timestamps properly.
export CPPROG="%{__cp} -p"

pushd build
%{make_install}
## Do the renaming due to the somewhat limited %%_bindir namespace.
rename client torrent_client %{buildroot}%{_bindir}/*
## Fix rpath
chrpath -d %{buildroot}%{_bindir}/bt_get
chrpath -d %{buildroot}%{_bindir}/simple_torrent_client
chrpath -d %{buildroot}%{_bindir}/dump_torrent
chrpath -d %{buildroot}%{_bindir}/upnp_test
chrpath -d %{buildroot}%{_bindir}/make_torrent
#chrpath -d %{buildroot}%{_bindir}/fuzz_torrent
chrpath -d %{buildroot}%{_bindir}/stats_counters
chrpath -d %{buildroot}%{_bindir}/torrent_client_test
chrpath -d %{buildroot}%{_bindir}/connection_tester
chrpath -d %{buildroot}%{_bindir}/bt_get2
## Install the python binding module.
pushd bindings/python
%{__python2} setup.py install -O1 --skip-build --root %{buildroot}
popd && popd

%if %{with python3}
pushd build-python3/bindings/python
%{__python3} setup.py install -O1 --skip-build --root %{buildroot}
popd
%endif # with python3

install -p -m 0644 %{SOURCE1} ./README-renames.Fedora

## unpackged files
# .la files
rm -fv %{buildroot}%{_libdir}/lib*.la
# static libs
rm -fv %{buildroot}%{_libdir}/lib*.a

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%{!?_licensedir:%global license %doc}
%doc AUTHORS ChangeLog
%license COPYING
%{_libdir}/libtorrent-rasterbar.so.9*

%files	devel
%doc docs/
%license COPYING.Boost COPYING.BSD COPYING.zlib
%{_libdir}/pkgconfig/libtorrent-rasterbar.pc
%{_includedir}/libtorrent/
%{_libdir}/libtorrent-rasterbar.so

%files examples
%doc README-renames.Fedora
%license COPYING
%{_bindir}/*torrent*
%{_bindir}/bt_ge*
%{_bindir}/connection_tester
%{_bindir}/stats_counters
%{_bindir}/upnp_test

%files	python2
%doc AUTHORS ChangeLog
%license COPYING.Boost
%{python2_sitearch}/python_libtorrent-%{version}-py2.?.egg-info
%{python2_sitearch}/libtorrent.so

%if %{with python3}
%files	python3
%doc AUTHORS ChangeLog
%license COPYING.Boost
%{python3_sitearch}/python_libtorrent-%{version}-py3.?.egg-info
%{python3_sitearch}/libtorrent.cpython-*.so
%endif # with python3

%changelog
* Mon Jan 01 2018 Evgeny Lensky <surfernsk@gmail.com> - 1.1.6-1
- update release - 1.1.6

* Wed Nov 15 2017 Evgeny Lensky <surfernsk@gmail.com> - 1.1.5-1
- update release 1.1.5

* Tue Jul 18 2017 Evgeny Lensky <surfernsk@gmail.com> - 1.1.4-1
- update release 1.1.4

* Sun Jul 02 2017 Björn Esser <besser82@fedoraproject.org> - 1.1.2-3
- Fix linking for the Python3 bindings (rhbz#1399390)
- Fix filtering provides
- Clean trailing whitespace

* Mon May 15 2017 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_27_Mass_Rebuild

* Tue Feb 28 2017 Fabio Alessandro Locati <fale@fedoraproject.org> - 1.1.2-1
- Upgrade to 1.1.1

* Fri Feb 17 2017 Jonathan Wakely <jwakely@redhat.com> - 1.1.1-4
- Fix failure test due to asio header order issue

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.1.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Thu Dec 22 2016 Miro Hrončok <mhroncok@redhat.com> - 1.1.1-3
- Rebuild for Python 3.6

* Thu Oct 06 2016 Leigh Scott <leigh123linux@googlemail.com> - 1.1.1-2
- Fix rpath

* Wed Sep 28 2016 Leigh Scott <leigh123linux@googlemail.com> - 1.1.1-1
- Upgrade to 1.1.1

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.0-2
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Mon Apr 11 2016 Fabio Alessandro Locati <fale@fedoraproject.org> - 1.1.0-1
- Upgrade to 1.1.0

* Mon Mar 14 2016 Przemysław Palacz <pprzemal@gmail.com> - 1.0.9-2
- Fix missing Python 3 binding library

* Sat Mar 12 2016 Fabio Alessandro Locati <fale@fedoraproject.org> - 1.0.9-1
- Upgrade to 1.0.9
- Provide -python3 subpackage as well
- Rename -python subpackage as -python2

* Tue Mar 08 2016 Bruno Wolff III <bruno@wolff.to> - 1.0.8-3
- Rebuild for libtommath soname bump

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Tue Jan 26 2016 Fabio Alessandro Locati <fale@fedoraproject.org> - 1.0.8-1
- Upstream release 1.0.8

* Fri Jan 15 2016 Jonathan Wakely <jwakely@redhat.com> - 1.0.7-3
- Rebuilt for Boost 1.60

* Mon Dec 07 2015 Fabio Alessandro Locati <fale@fedoraproject.org> - 1.0.7-2
- Fixes to make it work properly with python2 on F24+
- Remove README since is not shipped any more

* Sat Nov 14 2015 Fabio Alessandro Locati <fale@fedoraproject.org> - 1.0.7-1
- Upstream release 1.0.7

* Sat Oct 17 2015 Ville Skyttä <ville.skytta@iki.fi> - 1.0.6-3
- Link with system tommath, drop bundled one

* Thu Aug 27 2015 Jonathan Wakely <jwakely@redhat.com> - 1.0.6-2
- Rebuilt for Boost 1.59

* Sat Aug 15 2015 Leigh Scott <leigh123linux@googlemail.com> - 1.0.6-1
- Upstream release 1.0.6
- Change source URL
- Install license files properly
- Remove pkgconfig requires
- Clean up requires
- Filter private-shared-object-provides on python sub-package
- Specify version for python buildrequires

* Wed Jul 29 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.5-2
- Rebuilt for https://fedoraproject.org/wiki/Changes/F23Boost159

* Sun Jul 26 2015 Fabio Alessandro Locati <fale@fedoraproject.org> - 1.0.5-1
- Upstream release 1.0.5
- Lint the spec file

* Wed Jul 22 2015 David Tardon <dtardon@redhat.com> - 1.0.4-3
- rebuild for Boost 1.58

* Thu Jun 18 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sat Apr 18 2015 Leigh Scott <leigh123linux@googlemail.com> - 1.0.4-1
- upstream release 1.0.4

* Tue Jan 27 2015 Petr Machata <pmachata@redhat.com> - 1.0.3-2
- Rebuild for boost 1.57.0

* Fri Dec 19 2014 Leigh Scott <leigh123linux@googlemail.com> - 1.0.3-1
- upstream release 1.0.3

* Tue Sep 16 2014 Leigh Scott <leigh123linux@googlemail.com> - 1.0.2-1
- upstream release 1.0.2

* Mon Aug 18 2014 Leigh Scott <leigh123linux@googlemail.com> - 1.0.1-1
- upstream release 1.0.1
- update patches

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.16.17-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Sun Jun 22 2014 Leigh Scott <leigh123linux@googlemail.com> - 0.16.17-1
- upstream release 0.16.17

* Sun Jun 15 2014 Leigh Scott <leigh123linux@googlemail.com> - 0.16.16-4
- patch to stop UPNP from openning port 0

* Sun Jun 08 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.16.16-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Thu May 22 2014 Petr Machata <pmachata@redhat.com> - 0.16.16-2
- Rebuild for boost 1.55.0

* Mon Apr 21 2014 Leigh Scott <leigh123linux@googlemail.com> - 0.16.16-1
- upstream release 0.16.16
- fix source url

* Sun Aug 18 2013 Leigh Scott <leigh123linux@googlemail.com> - 0.16.11-1
- upstream release 0.16.11

* Sun Aug 04 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.16.10-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Sat Jul 27 2013 Petr Machata <pmachata@redhat.com> - 0.16.10-2
- Rebuild for boost 1.54.0
- Change configure invocation to avoid Boost -mt libraries, which are
  not enabled anymore.
- Adjust libtorrent-rasterbar.pc to not mention -mt
  (rb_libtorrent-0.16.10-boost_mt.patch)
- Add a missing Boost.Noncopyable include
  (rb_libtorrent-0.16.10-boost_noncopyable.patch)

* Mon May 13 2013 Rahul Sundaram <sundaram@fedoraproject.org> - 0.16.10-1
- upstream release 0.16.10

* Thu May 09 2013 Rahul Sundaram <sundaram@fedoraproject.org> - 0.16.9-1
- upstream release 0.16.9

* Sun Feb 24 2013 Rahul Sundaram <sundaram@fedoraproject.org> - 0.16.8-1
- upstream release 0.16.8

* Sun Feb 10 2013 Denis Arnaud <denis.arnaud_fedora@m4x.org> - 0.16.7-3
- Rebuild for Boost-1.53.0

* Sat Feb 09 2013 Denis Arnaud <denis.arnaud_fedora@m4x.org> - 0.16.7-2
- Rebuild for Boost-1.53.0

* Wed Jan 23 2013 Leigh Scott <leigh123linux@googlemail.com> - 0.16.7-1
- Update to 0.16.7
- Drop gcc patch

* Sun Sep 30 2012 Leigh Scott <leigh123linux@googlemail.com> - 0.16.4-1
- Update to 0.16.4
- Patch for gcc error

* Mon Aug 20 2012 Leigh Scott <leigh123linux@googlemail.com> - 0.16.3-1
- Update to 0.16.3

* Thu Jul 26 2012 Leigh Scott <leigh123linux@googlemail.com> - 0.16.2-3
- Rebuild for boost-1.50.0

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.16.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sat Jul 14 2012 Leigh Scott <leigh123linux@googlemail.com> - 0.16.2-1
- Update to 0.16.2

* Sun Jun 24 2012 leigh scott <leigh123linux@googlemail.com> - 0.16.1-1
- Update to 0.16.1
- Remove the -DBOOST_FILESYSTEM_VERSION=2 bits from spec
- Remove unused configure options

* Tue Mar 20 2012 leigh scott <leigh123linux@googlemail.com> - 0.15.9-1
- Update to 0.15.9

* Tue Feb 28 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.15.8-4
- Rebuilt for c++ ABI breakage

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.15.8-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Sun Nov 20 2011 Thomas Spura <tomspur@fedoraproject.org> - 0.15.8-2
- rebuild for https://fedoraproject.org/wiki/Features/F17Boost148

* Fri Sep 30 2011 Leigh Scott <leigh123linux@googlemail.com> - 0.15.8-1
- Update to 0.15.8

* Mon Aug 01 2011 Leigh Scott <leigh123linux@googlemail.com> - 0.15.7-1
- Update to 0.15.7

* Thu Jul 21 2011 Rahul Sundaram <sundaram@fedoraproject.org> - 0.15.6-2
- rebuild against boost 1.47.0
- drop defattr, clean stage
- change BR from util-linux-ng to util-linux since former has replaced latter
- drop all patches since none of them are being applied anymore

* Sun Apr 10 2011 Leigh Scott <leigh123linux@googlemail.com> - 0.15.6-1
- Update to 0.15.6

* Wed Apr 06 2011 Leigh Scott <leigh123linux@googlemail.com> - 0.15.5-4
- really build against boost 1.46.1

* Wed Mar 16 2011 Leigh Scott <leigh123linux@googlemail.com> - 0.15.5-3
- rebuild for boost 1.46.1

* Thu Feb 10 2011 Mamoru Tasaka <mtasaka@ioa.s.u-tokyo.ac.jp> - 0.15.5-2
- Add "R: GeoIP-devel" to -devel subpackage

* Thu Feb 10 2011 Mamoru Tasaka <mtasaka@fedoraproject.org> - 0.15.5-1
- Update to 0.15.5 (bug 654807, Leigh Scott)

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.14.11-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Tue Feb 08 2011 Mamoru Tasaka <mtasaka@fedoraproject.org> - 0.14.11-3
- Add -DBOOST_FILESYSTEM_VERSION=2 also in pkgconfig .pc file
  (bug 654807, Leigh Scott)

* Tue Feb 08 2011 Mamoru Tasaka <mtasaka@fedoraproject.org>
- Add -DBOOST_FILESYSTEM_VERSION=2

* Sun Feb 06 2011 Thomas Spura <tomspur@fedoraproject.org> - 0.14.11-2
- rebuild for new boost

* Wed Aug 25 2010 Rex Dieter <rdieter@fedoraproject.org> - 0.14.11-1
- rb_libtorrent-0.14.11
- track lib soname

* Thu Jul 29 2010 Mamoru Tasaka <mtasaka@ioa.s.u-tokyo.ac.jp> - 0.14.10-4
- Patch for python2.7 and g++4.5
- Pass -fno-strict-aliasing for now
- Copy from F-13 branch (F-14 branch still used 0.14.8)

* Fri May 28 2010 Rahul Sundaram <sundaram@fedoraproject.org> - 0.14.10-3
- Patch from Bruno Wolff III to fix DSO linking rhbz565082
- Update spec to match current guidelines

* Fri May 28 2010 Rahul Sundaram <sundaram@fedoraproject.org> - 0.14.10-2
- Fix E-V-R issue that breaks qbittorrent and deluge for upgrades
- Add default attributes to examples

* Sun Apr 04 2010 Leigh Scott <leigh123linux@googlemail.com> - 0.14.10-1
- Update to new upstream release (0.14.10)

* Fri Mar 12 2010 leigh scott <leigh123linux@googlemail.com> - 0.14.9-1
- Update to new upstream release (0.14.9)
- Fix source URL

* Tue Jan 19 2010 Ville Skyttä <ville.skytta@iki.fi> - 0.14.8-2
- Rebuild per
  http://lists.fedoraproject.org/pipermail/devel/2010-January/129500.html

* Tue Jan 12 2010 Leigh Scott <leigh123linux@googlemail.com> - 0.14.8-1
- Update to new upstream release (0.14.8)

* Wed Nov 25 2009 Peter Gordon <peter@thecodergeek.com> - 0.14.7-1
- Update to new upstream release (0.14.7)
- Resolves: #541026 (rb_libtorrent 0.14.6 crashes)

* Sun Sep 27 2009 Peter Gordon <peter@thecodergeek.com> - 0.14.6-1
- Update to new upstream release (0.14.6)
- Build against system GeoIP libraries.

* Fri Aug 21 2009 Tomas Mraz <tmraz@redhat.com> - 0.14.4-3
- rebuilt with new openssl

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.14.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Tue Jun 02 2009 Peter Gordon <peter@thecodergeek.com> - 0.14.4-1
- Update to new upstream release (0.14.4).
- Drop outdated Boost patch.

* Fri May 08 2009 Peter Gordon <peter@thecodergeek.com> - 0.14.3-2
- Rebuild for the Boost 1.39.0 update.

* Mon Apr 27 2009 Peter Gordon <peter@thecodergeek.com> - 0.14.3-1
- Update to new upstream bug-fix release (0.14.3).

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.14.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Fri Feb 20 2009 Peter Gordon <peter@thecodergeek.com> - 0.14.2-1
- Update to new upstream bug-fix release (0.14.2)
- Drop Python 2.6 and configure fix patches (fixed upstream):
  - python26.patch
  - configure-dont-use-locate.patch

* Fri Jan 16 2009 Peter Gordon <peter@thecodergeek.com> - 0.14.1-2
- Rebuild for the soname bump in openssl-0.9.8j

* Mon Jan 05 2009 Peter Gordon <peter@thecodergeek.com> - 0.14.1-1
- Update to new upstream release (0.14.1)
- Add asio-devel as runtime dependency for the devel subpackage (#478589)
- Add patch to build with Python 2.6:
  + python26.patch
- Add patch to make the configure script use the proper python include
  directory instead of calling locate, as that can cause failures in a chroot
  with no db file (and is a bit silly in the first place):
  + configure-dont-use-locate.patch
- Drop manual setup.py for building the python module (fixed upstream):
  - setup.py
- Update Source0 URL back to SourceForge's hosting.
- Reenable the examples, since the Makefiles are fixed.

* Fri Dec 19 2008 Petr Machata <pmachata@redhat.com> - 0.13.1-7
- Rebuild for boost-1.37.0.

* Wed Dec 17 2008 Benjamin Kosnik  <bkoz@redhat.com> - 0.13.1-6
- Rebuild for boost-1.37.0.

* Sat Nov 29 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 0.13.1-5
- Fix locations for Python 2.6

* Sat Nov 29 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 0.13.1-4
- Rebuild for Python 2.6

* Thu Nov 20 2008 Peter Gordon <peter@thecodergeek.com>
- Update Source0 URL, for now.

* Wed Sep  3 2008 Tom "spot" Callaway <tcallawa@redhat.com> - 0.13.1-3
- fix license tag

* Mon Jul 14 2008 Peter Gordon <peter@thecodergeek.com> - 0.13.1-2
- Add python bindings in a -python subpackage.

* Mon Jul 14 2008 Peter Gordon <peter@thecodergeek.com> - 0.13.1-1
- Update to new upstream release (0.13.1): Contains an incompatible ABI/API
  bump.
- Drop GCC 4.3 patch (fixed upstream):
  - gcc43.patch
- Disable building the examples for now. (Attempted builds fail due to missing
  Makefile support.)
- Drop the source permissions and pkgconfig file tweaks (fixed upstream).

* Sat Feb 09 2008 Peter Gordon <peter@thecodergeek.com> - 0.12.1-1
- Update to new upstream bug-fix release (0.12.1)
- Rebuild for GCC 4.3
- Drop security fix patch (merged upstream):
  - svn1968-bdecode_recursive-security-fix.patch
- Add GCC 4.3 build fixes (based on patch from Adel Gadllah, bug 432778):
  + gcc43.patch

* Mon Jan 28 2008 Peter Gordon <peter@thecodergeek.com> - 0.12-3
- Add upstream patch (changeset 1968) to fix potential security vulnerability:
  malformed messages passed through the bdecode_recursive routine could cause
  a potential stack overflow.
  + svn1968-bdecode_recursive-security-fix.patch

* Fri Aug 03 2007 Peter Gordon <peter@thecodergeek.com> - 0.12-2
- Rebuild against new Boost libraries.

* Thu Jun 07 2007 Peter Gordon <peter@thecodergeek.com> - 0.12-1
- Update to new upstream release (0.12 Final)
- Split examples into a subpackage. Applications that use rb_libtorrent
  don't need the example binaries installed; and splitting the package in this
  manner is a bit more friendly to multilib environments.

* Sun Mar 11 2007 Peter Gordon <peter@thecodergeek.com> - 0.12-0.rc1
- Update to new upstream release (0.12 RC).
- Forcibly use the system libtool to ensure that we remove any RPATH hacks.

* Sun Jan 28 2007 Peter Gordon <peter@thecodergeek.com> - 0.11-5
- Fix installed pkgconfig file: Strip everything from Libs except for
  '-ltorrent', as its [libtorrent's] DSO will ensure proper linking to other
  needed libraries such as zlib and boost_thread. (Thanks to Michael Schwendt
  and Mamoru Tasaka; bug #221372)

* Sat Jan 27 2007 Peter Gordon <peter@thecodergeek.com> - 0.11-4
- Clarify potential licensing issues in the -devel subpackage:
  + COPYING.zlib
  + COPYING.Boost
- Add my name in the Fedora-specific documentation (README-renames.Fedora) and
  fix some spacing issues in it.
- Strip the @ZLIB@ (and thus, the extra '-lz' link option) from the installed
  pkgconfig file, as that is only useful when building a statically-linked
  libtorrent binary.
- Fix conflict: The -devel subpackage should conflict with the -devel
  subpackage of libtorrent, not the main package.
- Preserve timestamps in %%install.

* Wed Jan 17 2007 Peter Gordon <peter@thecodergeek.com> - 0.11-3
- Fix License (GPL -> BSD)
- Don't package RST (docs sources) files.
- Only make the -devel subpackage conflict with libtorrent-devel.
- Rename some of the examples more appropriately; and add the
  README-renames.Fedora file to %%doc which explains this.

* Fri Jan 05 2007 Peter Gordon <peter@thecodergeek.com> - 0.11-2
- Add Requires: pkgconfig to the -devel subpackage since it installs a .pc
  file.

* Wed Jan 03 2007 Peter Gordon <peter@thecodergeek.com> - 0.11-1
- Initial packaging for Fedora Extras
