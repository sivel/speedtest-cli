# Pull Requests

Pull requests should be made against the `devel` branch. Pull requests should be made from a git feature branch. Pull requests will not be accepted that:

1. Are not made against the `devel` branch
1. Are submitted from a branch named `devel`
1. Don't pass pep8/pyflakes/flake8
1. Do not work with Python 2.4-3.4 or pypy
1. Add python modules not included with the Python standard library

# Coding Guidelines

In general, I follow strict pep8 and pyflakes. All code must pass these tests. Since we support python 2.4-3.4 and pypy, pyflakes reports unknown names in python 3.  pyflakes is run in python 2.7 only in my tests.

# Supported Python Versions

All code needs to support Python 2.4-3.4 and pypy.

# Permitted Python Modules

Only modules included in the standard library are permitted for use in this application.  This application should not be dependent on any 3rd party modules that would need to be installed external to just Python itself.

# Testing

Currently there are no unit tests, but they are planned.
