%define binutils 2.24.51.0.1
%define glibc 2.18
%define gcc linaro-4.8-2013.11
%define kernel 3.12.2
%define arches armv6l-openmandriva-linux-gnueabi armv6b-openmandriva-linux-gnueabi armv7l-openmandriva-linux-gnueabi armv7hl-openmandriva-linux-gnueabi aarch64-openmandriva-linux-gnu

Name: toolchain
Version: 2013.11
Release: 1
Source0: http://ftp.kernel.org/pub/linux/devel/binutils/binutils-%{binutils}.tar.xz
Source1: http://cbuild.validation.linaro.org/snapshots/gcc-%{gcc}.tar.xz
Source2: http://ftp.gnu.org/pub/gnu/glibc/glibc-%{glibc}.tar.xz 
Source3: http://ftp.kernel.org/pub/linux/kernel/v3.x/linux-%{kernel}.tar.xz
Source100: cross-tools-package
# Patches for glibc
Patch0: glibc-2.18-make-4.0.patch
# see https://sourceware.org/ml/libc-alpha/2013-11/msg00291.html
Patch1: glibc-2.18-fix-build-with-gcc-4.8.3.patch
Summary: The toolchain (binutils, gcc, glibc) all-in-one for crosscompiling
URL: http://toolchain.sf.net/
License: GPL
Group: Development/Other

%description
The toolchain (binutils, gcc, glibc) all-in-one for crosscompiling

%{expand:%(for arch in %{arches}; do %SOURCE100 $arch; done)}

%prep
%setup -q -c -a 1 -a 2 -a 3
cd glibc-%{glibc}
%patch0 -p1 -b .make40~
%patch1 -p1 -b .buildfix~
cd ..

# No %%build because we need to use stuff in %{buildroot}
# while building other components

%install
ln -s %_bindir/ld.bfd ld
export PATH="%{buildroot}%{_bindir}:`pwd`:$PATH"
for arch in %{arches}; do
	case `echo $arch |cut -d- -f1` in
	aarch64*)
		KERNELARCH=arm64
		;;
	arm*)
		KERNELARCH=arm
		;;
	i?86|pentium?|athlon*|x86_64|amd64|intel64)
		KERNELARCH=x86
		;;
	mips*)
		KERNELARCH=mips
		;;
	ppc*)
		KERNELARCH=powerpc
		;;
	*)
		KERNELARCH=`echo $arch |cut -d- -f1`
		;;
	esac
	SYSROOT="%{_prefix}/$arch/sys-root"
	mkdir -p build/binutils-$arch build/gcc-$arch/stage1 build/glibc-$arch/stage1 build/gcc-$arch/stage2 build/glibc-$arch/stage2 build/gcc-$arch/stage3
	cd build/binutils-$arch
	GOLD="--disable-gold" # For now, FIXME
	../../binutils-%{binutils}/configure --prefix=%{_prefix} --target=$arch --with-sysroot="$SYSROOT" --with-build-sysroot=%{buildroot}"$SYSROOT" --enable-plugins --enable-threads $GOLD
	%make
	%makeinstall_std
	cd ../gcc-$arch/stage1
	../../../gcc-%{gcc}/configure --prefix=%{_prefix} --libexecdir=%{_libexecdir} --target=$arch --with-sysroot="$SYSROOT" --with-build-sysroot=%{buildroot}"$SYSROOT" --enable-languages=c,c++ --disable-multilib --disable-__cxa_atexit --disable-libmudflap --disable-libssp --disable-threads --disable-tls --disable-decimal-float --disable-libgomp --disable-libquadmath --disable-libsanitizer --disable-libatomic --disable-shared --disable-libstdc__-v3 --disable-sjlj-exceptions --disable-libitm --disable-libquadmath --with-newlib
	%make
	%makeinstall_std
	cd ../../../linux-%{kernel}
	make ARCH=$KERNELARCH CROSS_COMPILE=$arch- defconfig
	make ARCH=$KERNELARCH CROSS_COMPILE=$arch- prepare0 prepare1 prepare2 prepare3
	make ARCH=$KERNELARCH CROSS_COMPILE=$arch- INSTALL_HDR_PATH="%{buildroot}$SYSROOT%{_prefix}" headers_install
	make mrproper
	cd ../build/glibc-$arch/stage1
	../../../glibc-%{glibc}/configure --prefix=%{_prefix} --target=$arch --host=$arch --with-sysroot="$SYSROOT" --with-build-sysroot=%{buildroot}"$SYSROOT" --enable-add-ons=ports,nptl,libidn --with-headers=%{buildroot}"$SYSROOT"%{_includedir} --disable-profile --without-gd --without-cvs --enable-omitfp --enable-oldest-abi=2.12 --enable-kernel=2.6.24 --enable-experimental-malloc --disable-systemtap --enable-bind-now --disable-selinux --without-tls --disable-tls
	%make install-headers install_root=%{buildroot}"$SYSROOT" install-bootstrap-headers=yes
	mkdir -p %{buildroot}"$SYSROOT"%{_prefix}/lib
	%make csu/subdir_lib
	cp csu/crt1.o csu/crti.o csu/crtn.o %{buildroot}"$SYSROOT"%{_prefix}/lib/
	$arch-gcc -nostdlib -nostartfiles -shared -x c /dev/null -o %{buildroot}"$SYSROOT"%{_prefix}/lib/libc.so
	[ -e %{buildroot}"$SYSROOT"%{_includedir}/gnu/stubs.h ] || touch %{buildroot}"$SYSROOT"%{_includedir}/gnu/stubs.h
	cd ../../gcc-$arch/stage2
	../../../gcc-%{gcc}/configure --prefix=%{_prefix} --libexecdir=%{_libexecdir} --target=$arch --with-sysroot="$SYSROOT" --with-build-sysroot=%{buildroot}"$SYSROOT" --enable-languages=c,c++ --disable-libssp --disable-libgomp --disable-libmudflap --disable-libquadmath --disable-multilib --disable-libstdc__-v3 --disable-libatomic --disable-libitm --disable-libsanitizer --enable-shared
	%make
	%makeinstall_std
	cd ../../glibc-$arch/stage2
	../../../glibc-%{glibc}/configure --prefix=$SYSROOT%{_prefix} --target=$arch --host=$arch --with-sysroot="$SYSROOT" --with-build-sysroot=%{buildroot}"$SYSROOT" --enable-add-ons=ports,nptl,libidn --with-headers=%{buildroot}"$SYSROOT"%{_includedir} --disable-profile --without-gd --without-cvs --enable-omitfp --enable-oldest-abi=2.12 --enable-kernel=2.6.24 --enable-experimental-malloc --disable-systemtap --enable-bind-now --disable-selinux
	%make
	%makeinstall_std
	cd ../../gcc-$arch/stage3
	../../../gcc-%{gcc}/configure --prefix=%{_prefix} --libexecdir=%{_libexecdir} --target=$arch --with-sysroot="$SYSROOT" --with-build-sysroot=%{buildroot}"$SYSROOT" --enable-__cxa_atexit --disable-libssp --disable-libmudflap --disable-libquadmath --disable-multilib --disable-libgomp --enable-languages=c,c++,ada,objc,obj-c++,lto
	cd ../../..
done

# Get rid of the stuff we're getting from the native toolchain
# (unless and until we start building native toolchains here too)
rm -rf %{buildroot}%{_libdir}/libiberty.a
rm -rf %{buildroot}%{_datadir}/locale
rm -rf %{buildroot}%{_mandir}/man7
rm -rf %{buildroot}%{_infodir}
