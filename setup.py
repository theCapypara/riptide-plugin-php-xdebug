__version__ = '0.9.0'

# README read-in
from os import path

from setuptools import setup, find_packages

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()
# END README read-in

setup(
    name='riptide-plugin-php-xdebug',
    version=__version__,
    packages=find_packages(),
    description='Tool to manage development environments for web applications using containers - PHP Xdebug integration',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/theCapypara/riptide-plugin-php-xdebug/',
    author='Marco "theCapypara" Köpcke',
    license='MIT',
    install_requires=[
        'riptide-lib >= 0.9, < 0.10',
        'riptide-cli >= 0.9, < 0.10',
        'Click >= 7.0, < 9.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    entry_points='''
        [riptide.plugin]
        php-xdebug=riptide_plugin_php_xdebug.plugin:PhpXdebugPlugin
    ''',
)
