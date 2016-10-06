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

	def test_reuse(self):
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


if __name__ == '__main__':
	unittest.main()
