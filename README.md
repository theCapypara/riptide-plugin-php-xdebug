# ![Riptide](https://riptide-docs.readthedocs.io/en/latest/_images/logo.png)

[<img src="https://img.shields.io/github/actions/workflow/status/theCapypara/riptide-plugin-php-xdebug/build.yml" alt="Build Status">](https://github.com/theCapypara/riptide-plugin-php-xdebug/actions)
[<img src="https://readthedocs.org/projects/riptide-docs/badge/?version=latest" alt="Documentation Status">](https://riptide-docs.readthedocs.io/en/latest/)
[<img src="https://img.shields.io/pypi/v/riptide-plugin-php-xdebug" alt="Version">](https://pypi.org/project/riptide-plugin-php-xdebug/)
[<img src="https://img.shields.io/pypi/dm/riptide-plugin-php-xdebug" alt="Downloads">](https://pypi.org/project/riptide-plugin-php-xdebug/)
<img src="https://img.shields.io/pypi/l/riptide-plugin-php-xdebug" alt="License (MIT)">
<img src="https://img.shields.io/pypi/pyversions/riptide-plugin-php-xdebug" alt="Supported Python versions">

Riptide is a set of tools to manage development environments for web applications.
It's using container virtualization tools, such as [Docker](https://www.docker.com/)
to run all services needed for a project.

Its goal is to be easy to use by developers.
Riptide abstracts the virtualization in such a way that the environment behaves exactly
as if you were running it natively, without the need to install any other requirements
the project may have.

Riptide consists of a few repositories, find the
entire [overview](https://riptide-docs.readthedocs.io/en/latest/development.html) in the documentation.

## Plugin: PHP Xdebug

This plugin allows users to toggle the use of Xdebug for PHP based services or commands.

Usage via CLI:

```
riptide xdebug [on/off]
```

Sets the flag `php-xdebug.enabled`, which can be read from Riptide configuration files to
enable or disable Xdebug.

## Documentation

The complete documentation for Riptide can be found at [Read the Docs](https://riptide-docs.readthedocs.io/en/latest/).
