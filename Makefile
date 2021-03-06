VERSION ?= $(shell python -c "import scrapy; print '.'.join(map(str, scrapy.version_info[:2]))")
DEBREV ?= 1
HGREV ?= $(shell hg log -l1 --template '{rev}')
FULL_VERSION ?= $(VERSION)~r$(HGREV)
BUILDBASE ?= $(shell pwd)/build/deb
BUILDDIR ?= $(BUILDBASE)/scrapy_$(FULL_VERSION).orig
BUILDTAR ?= $(BUILDBASE)/scrapy_$(FULL_VERSION).orig.tar.gz

help:
	@echo 'Available targets:'
	@echo '  deb-binary   - build debian binary package'
	@echo '  deb-source   - build debian source package'
	@echo '  deb-all      - build source and binary debian packages'
	@echo '  tarball      - build source tarball'
	@echo '  sign         - sign release'

deb-binary: deb-prepare
	cd $(BUILDDIR); debuild -i -us -uc -b

deb-source: deb-prepare
	cd $(BUILDDIR); debuild -i -us -uc -S

deb-all: deb-prepare
	cd $(BUILDDIR); debuild -i -us -uc

deb-prepare:
	@if [ -d $(BUILDBASE) ]; then \
		rm -rf $(BUILDBASE); \
	fi;
	mkdir -p $(BUILDBASE)
	hg archive -t tgz -X .hgtags $(BUILDTAR)
	tar zxf $(BUILDTAR) -C $(BUILDBASE)
	rm -f $(BUILDDIR)/Makefile # to avoid confusing dh_auto_build
	cp -r debian $(BUILDDIR)
	cd $(BUILDDIR); debchange -m -D unstable --force-distribution -v $(FULL_VERSION)-$(DEBREV) "Automatic build"

tarball:
	hg purge --all
	python setup.py sdist

sign:
	md5sum dist/Scrapy-* > dist/MD5SUMS
	sha1sum dist/Scrapy-* > dist/SHA1SUMS
	gpg -ba dist/MD5SUMS
	gpg -ba dist/SHA1SUMS
