#!/usr/bin/env python

import hashlib
from functools import wraps
import logging
import os
import shutil
import tempfile
import unittest

import vignette


ALL_THUMBNAIL = vignette.THUMBNAILER_BACKENDS
IMAGE_THUMBNAIL = [vignette.QtBackend(), vignette.PilBackend(), vignette.MagickBackend()]
IMAGE_THUMBNAIL = [b for b in IMAGE_THUMBNAIL if b.is_available()]

ALL_METADATA = vignette.METADATA_BACKENDS
AVAIL_METADATA = [b for b in ALL_METADATA if b.is_available()]


class ThumbnailTests(unittest.TestCase):
	def __init__(self, metadata=None, thumbnail=None, *args, **kwargs):
		super(ThumbnailTests, self).__init__(*args, **kwargs)
		self.metadata_backends = metadata
		self.thumbnail_backends = thumbnail

	def setUp(self):
		self.dir = os.environ['XDG_CACHE_HOME'] = tempfile.mkdtemp()
		self.filename = os.path.join(os.environ['XDG_CACHE_HOME'], 'test.png')
		shutil.copyfile('test.png', self.filename)

		if self.metadata_backends is None:
			vignette.METADATA_BACKENDS = ALL_METADATA
		else:
			vignette.METADATA_BACKENDS = self.metadata_backends

		if self.thumbnail_backends is None:
			vignette.THUMBNAILER_BACKENDS = ALL_THUMBNAIL
		else:
			vignette.THUMBNAILER_BACKENDS = self.thumbnail_backends

	def tearDown(self):
		shutil.rmtree(self.dir)

	def test_hash(self):
		uri = u'file://%s' % self.filename
		dest = os.path.join(self.dir, 'thumbnails', 'large', hashlib.md5(uri.encode('utf-8')).hexdigest()) + '.png'
		self.assertEqual(dest, vignette.build_thumbnail_path(self.filename, 'large'))

	def test_basic(self):
		dest = vignette.build_thumbnail_path(self.filename, 'large')
		assert dest

		self.assertIsNone(vignette.try_get_thumbnail(self.filename, 'large'))
		assert not os.path.exists(dest)

		self.assertEqual(dest, vignette.get_thumbnail(self.filename, 'large'))
		assert os.path.isfile(dest)

		self.assertEqual(dest, vignette.try_get_thumbnail(self.filename, 'large'))

	def test_reuse_thumbnail(self):
		dest = vignette.get_thumbnail(self.filename, 'large')
		assert dest
		st = os.stat(dest)
		self.assertEqual(dest, vignette.get_thumbnail(self.filename, 'large'))
		self.assertEqual(st, os.stat(dest))
		self.assertEqual(dest, vignette.create_thumbnail(self.filename, 'large'))
		self.assertNotEqual(st, os.stat(dest))

	def test_direct_thumbnail(self):
		dest = vignette.get_thumbnail(self.filename, 'large')
		assert dest
		assert os.path.isfile(dest)
		self.assertEqual(dest, vignette.try_get_thumbnail(dest, 'large'))

	def test_mtime_validity(self):
		dest = vignette.get_thumbnail(self.filename, 'large')
		assert dest

		os.utime(self.filename, (0, 0))
		self.assertIsNone(vignette.try_get_thumbnail(self.filename, 'large'))
		assert os.path.isfile(dest)

		self.assertEqual(dest, vignette.get_thumbnail(self.filename, 'large'))
		self.assertEqual(dest, vignette.try_get_thumbnail(self.filename, 'large'))

	def test_multisize(self):
		dest = vignette.get_thumbnail(self.filename, 'large')
		assert dest
		self.assertEqual(dest, vignette.try_get_thumbnail(self.filename, 'large'))
		self.assertIsNone(vignette.try_get_thumbnail(self.filename, 'normal'))
		self.assertEqual(dest, vignette.try_get_thumbnail(self.filename))

		os.remove(dest)
		dest = vignette.get_thumbnail(self.filename, 'normal')
		assert dest
		self.assertEqual(dest, vignette.try_get_thumbnail(self.filename, 'normal'))
		self.assertIsNone(vignette.try_get_thumbnail(self.filename, 'large'))
		self.assertEqual(dest, vignette.try_get_thumbnail(self.filename))

	def test_fail(self):
		self.filename = os.path.join(self.dir, 'empty')
		open(self.filename, 'w').close()

		self.assertIsNone(vignette.get_thumbnail(self.filename, 'large'))
		assert not os.path.exists(os.path.join(self.dir, 'thumbnails', 'fail'))
		assert not vignette.is_thumbnail_failed(self.filename, 'foo')

		self.assertIsNone(vignette.get_thumbnail(self.filename, 'large', use_fail_appname='foo'))
		assert os.path.exists(os.path.join(self.dir, 'thumbnails', 'fail', 'foo'))
		assert vignette.is_thumbnail_failed(self.filename, 'foo')
		assert not vignette.is_thumbnail_failed(self.filename, 'bar')

	def test_fail_mtime_validity(self):
		self.filename = os.path.join(self.dir, 'empty')
		open(self.filename, 'w').close()

		self.assertIsNone(vignette.get_thumbnail(self.filename, 'large', use_fail_appname='foo'))
		assert vignette.is_thumbnail_failed(self.filename, 'foo')

		os.utime(self.filename, (0, 0))
		assert not vignette.is_thumbnail_failed(self.filename, 'foo')

	def test_put_thumbnail(self):
		uri = 'http://example.com'
		tmp = vignette.create_temp('large')
		shutil.copyfile(self.filename, tmp)
		vignette.put_thumbnail(uri, 'large', tmp, mtime=42)
		assert vignette.try_get_thumbnail(uri, 'large', mtime=42)
		self.assertIsNone(vignette.try_get_thumbnail(uri, 'large', mtime=1))

	def test_put_fail(self):
		vignette.put_fail(self.filename, 'foo')
		assert vignette.is_thumbnail_failed(self.filename, 'foo')
		assert not vignette.is_thumbnail_failed(self.filename, 'bar')

		self.assertIsNone(vignette.get_thumbnail(self.filename, use_fail_appname='foo'))
		dest = vignette.get_thumbnail(self.filename, use_fail_appname='bar')
		assert dest
		self.assertEqual(dest, vignette.get_thumbnail(self.filename, use_fail_appname='foo'))


class MultiBackendsLoader(unittest.TestLoader):
	def loadTestsFromTestCase(self, testCaseClass):
		testCaseNames = self.getTestCaseNames(testCaseClass)
		tests = []
		for name in testCaseNames:
			tests.append(testCaseClass(methodName=name))
			for b in AVAIL_METADATA:
				tests.append(testCaseClass(metadata=[b], methodName=name))

			for b in IMAGE_THUMBNAIL:
				tests.append(testCaseClass(thumbnail=[b], methodName=name))

		loaded_suite = self.suiteClass(tests)
		return loaded_suite


if __name__ == '__main__':
	logging.basicConfig()
	unittest.main(testLoader=MultiBackendsLoader())
