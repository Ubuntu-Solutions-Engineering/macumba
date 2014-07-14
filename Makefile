#
# Makefile for cloud-install
#
NAME        = macumba
TOPDIR      := $(shell basename `pwd`)
GIT_REV     := $(shell git log --oneline -n1| cut -d" " -f1)
VERSION     := $(shell python3 setup.py version)

$(NAME)_$(VERSION).orig.tar.gz: clean
	cd .. && tar czf $(NAME)_$(VERSION).orig.tar.gz $(TOPDIR) --exclude-vcs --exclude=debian

tarball: $(NAME)_$(VERSION).orig.tar.gz

.PHONY: install-dependencies
install-dependencies:
	sudo apt-get install devscripts equivs
	sudo mk-build-deps -i debian/control

.PHONY: uninstall-dependencies
uninstall-dependencies:
	sudo apt-get remove macumba-build-deps

clean:
	@debian/rules clean
	@rm -rf debian/macumba
	@rm -rf docs/_build/*
	@rm -rf ../macumba_*.deb ../macumba_*.tar.gz ../macumba_*.dsc ../macumba_*.changes \
		../macumba_*.build ../python3-macumba_*.deb

deb-src: clean update_version tarball
	@debuild -S -us -uc

deb: clean update_version tarball
	@debuild -us -uc -i

sbuild: clean update_version tarball
	@sbuild -d trusty-amd64 -j4

current_version:
	@echo $(VERSION)

git_rev:
	@echo $(GIT_REV)

update_version:
	wrap-and-sort


.PHONY: ci-test pyflakes pep8 test
ci-test: pyflakes pep8 test

pyflakes:
	python3 `which pyflakes` macumba

pep8:
	pep8 cloudinstall

test:
	nosetests -v --with-cover --cover-package=macumba --cover-html test


all: deb
