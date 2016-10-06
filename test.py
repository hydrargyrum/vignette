#!/usr/bin/env python

import md5
import os
import shutil
import tempfile
import unittest

import thumbnail



class ThumbnailTests(unittest.TestCase):
	def setUp(self):
		self.dir = os.environ['XDG_CACHE_HOME'] = tempfile.mkdtemp()
		self.filename = os.path.join(os.environ['XDG_CACHE_HOME'], 'test.png')
		shutil.copyfile('test.png', self.filename)

	def tearDown(self):
		shutil.rmtree(self.dir)

	def test_hash(self):
		uri = 'file://%s' % self.filename
		dest = os.path.join(self.dir, 'thumbnails', 'large', md5.new(uri).hexdigest()) + '.png'
		self.assertEqual(dest, thumbnail.build_thumbnail_path(self.filename, 'large'))

	def test_basic(self):
		dest = thumbnail.build_thumbnail_path(self.filename, 'large')
		assert dest

		self.assertIsNone(thumbnail.try_get_thumbnail(self.filename, 'large'))
		assert not os.path.exists(dest)

		self.assertEqual(dest, thumbnail.get_thumbnail(self.filename, 'large'))
		assert os.path.isfile(dest)

		self.assertEqual(dest, thumbnail.try_get_thumbnail(self.filename, 'large'))

	def test_reuse_thumbnail(self):
		dest = thumbnail.get_thumbnail(self.filename, 'large')
		assert dest
		st = os.stat(dest)
		self.assertEqual(dest, thumbnail.get_thumbnail(self.filename, 'large'))
		self.assertEqual(st, os.stat(dest))
		self.assertEqual(dest, thumbnail.create_thumbnail(self.filename, 'large'))
		self.assertNotEqual(st, os.stat(dest))

	def test_direct_thumbnail(self):
		dest = thumbnail.get_thumbnail(self.filename, 'large')
		assert dest
		assert os.path.isfile(dest)
		self.assertEqual(dest, thumbnail.try_get_thumbnail(dest, 'large'))

	def test_mtime_validity(self):
		dest = thumbnail.get_thumbnail(self.filename, 'large')
		assert dest

		os.utime(self.filename, (0, 0))
		self.assertIsNone(thumbnail.try_get_thumbnail(self.filename, 'large'))
		assert os.path.isfile(dest)

		self.assertEqual(dest, thumbnail.get_thumbnail(self.filename, 'large'))
		self.assertEqual(dest, thumbnail.try_get_thumbnail(self.filename, 'large'))

	def test_multisize(self):
		dest = thumbnail.get_thumbnail(self.filename, 'large')
		assert dest
		self.assertEqual(dest, thumbnail.try_get_thumbnail(self.filename, 'large'))
		self.assertIsNone(thumbnail.try_get_thumbnail(self.filename, 'normal'))
		self.assertEqual(dest, thumbnail.try_get_thumbnail(self.filename))

		os.remove(dest)
		dest = thumbnail.get_thumbnail(self.filename, 'normal')
		assert dest
		self.assertEqual(dest, thumbnail.try_get_thumbnail(self.filename, 'normal'))
		self.assertIsNone(thumbnail.try_get_thumbnail(self.filename, 'large'))
		self.assertEqual(dest, thumbnail.try_get_thumbnail(self.filename))

	def test_fail(self):
		self.filename = os.path.join(self.dir, 'failing.txt')
		open(self.filename, 'w').close()

		self.assertIsNone(thumbnail.get_thumbnail(self.filename, 'large'))
		assert not os.path.exists(os.path.join(self.dir, 'thumbnails', 'fail'))
		assert not thumbnail.is_thumbnail_failed(self.filename, 'foo')

		self.assertIsNone(thumbnail.get_thumbnail(self.filename, 'large', use_fail_appname='foo'))
		assert os.path.exists(os.path.join(self.dir, 'thumbnails', 'fail', 'foo'))
		assert thumbnail.is_thumbnail_failed(self.filename, 'foo')
		assert not thumbnail.is_thumbnail_failed(self.filename, 'bar')

	def test_fail_mtime_validity(self):
		self.filename = os.path.join(self.dir, 'failing.txt')
		open(self.filename, 'w').close()

		self.assertIsNone(thumbnail.get_thumbnail(self.filename, 'large', use_fail_appname='foo'))
		assert thumbnail.is_thumbnail_failed(self.filename, 'foo')

		os.utime(self.filename, (0, 0))
		assert not thumbnail.is_thumbnail_failed(self.filename, 'foo')


if __name__ == '__main__':
	unittest.main()
