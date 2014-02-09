# Pull Requests

Pull requests should be made against the `working` branch.

# Coding Guidelines

In general, I follow strict pep8 and pyflakes.  All code must pass these tests. Since we support python 2.4-3.4, pyflakes reports unknown names in python 3.  pyflakes is run in python 2.7 only in my tests.

# Supported Python Versions

All code needs to support Python 2.4-3.4.

# Permitted Python Modules

Only modules included in the standard library are permitted for use in this application.  This application should not be dependent on any 3rd party modules that would need to be installed external to just Python itself.

# Testing

Currently there are no unit tests, but they are planned.
