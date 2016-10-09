#!/usr/bin/env python
# this project is licensed under the WTFPLv2, see COPYING.txt for details

from setuptools import setup, find_packages

import glob

with open('VERSION.txt') as fd:
	version = fd.read().strip()

setup(
	name='vignette',
	version=version,

	description='Library to create FreeDesktop-compatible thumbnails',
	url='https://github.com/hydrargyrum/vignette',
	author='Hg',
	author_email='dev+pip@indigo.re',
	license='WTFPLv2',
	classifiers=[
		'Development Status :: 4 - Beta',

		'Intended Audience :: Developers',

		'License :: Public Domain',

		'Topic :: Desktop Environment',
		'Topic :: Multimedia :: Graphics',
		'Topic :: Software Development :: Libraries :: Python Modules',
		'Topic :: Utilities',

		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.2',
		'Programming Language :: Python :: 3.3',
		'Programming Language :: Python :: 3.4',
		'Programming Language :: Python :: 3.5',
		'Programming Language :: Python :: 3.6',
	],
	keywords='freedesktop xdg image thumbnail',

	extras_require={
		'Pillow': ['Pillow'],
		'PythonMagick': ['PythonMagick'],
	},

	zip_safe=True,
	packages=find_packages(),
	test_suite='test',
	entry_points={
		'console_scripts': [
			'vignette=vignette:main'
		]
	}
)
