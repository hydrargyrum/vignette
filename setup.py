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
	long_description='''
Vignette is a library to create and manage thumbnails following the FreeDesktop standard.

Thumbnails are stored in a shared directory so other apps following the standard can reuse
them without having to generate their own thumbnails.

Vignette can typically be used in file managers, image browsers, etc.

Thumbnails are not limited to image files on disk but can be generated for other file types,
for example videos or documents but also for any URL, for example a web browser could store
thumbnails for recently visited pages or bookmarks.

Vignette by itself can only generate thumbnails for local image files but can retrieve
thumbnail for any file or URL, if another app generated a thumbnail for it. An app can also
generate a thumbnail by its own means and use vignette to push that thumbnail to the store.
	''',
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
	keywords='freedesktop xdg image thumbnail thumbnails cache',

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
