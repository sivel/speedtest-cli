# Pull Requests

## Pull requests should be

1. Made against the `devel` branch.
1. Made from a git feature branch.

## Pull requests will not be accepted that

1. Are not made against the `devel` branch
1. Are submitted from a branch named `devel`
1. Do not pass pep8/pyflakes/flake8
1. Do not work with Python 2.4-3.4 or pypy
1. Add python modules not included with the Python standard library
1. Are made by editing files via the GitHub website

# Coding Guidelines

In general, I follow strict pep8 and pyflakes. All code must pass these tests. Since we support python 2.4-3.4 and pypy, pyflakes reports unknown names in python 3.  pyflakes is run in python 2.7 only in my tests.

## Some other points

1. Do not use `\` for line continuations, long strings should be wrapped in `()`.  Imports should start a brand new line in the form of `from foo import...`
1. String quoting should be done with single quotes `'`, except for situations where you would otherwise have to escape an internal single quote
1. Docstrings should use three double quotes `"""`
1. All functions, classes and modules should have docstrings following both the PEP257 and PEP8 standards
1. Inline comments should only be used on code where it is not immediately obvious what the code achieves

# Supported Python Versions

All code needs to support Python 2.4-3.4 and pypy.

# Permitted Python Modules

Only modules included in the standard library are permitted for use in this application.  This application should not be dependent on any 3rd party modules that would need to be installed external to just Python itself.

# Testing

Currently there are no unit tests, but they are planned.
