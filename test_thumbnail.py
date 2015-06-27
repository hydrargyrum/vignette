

import sys, os
import commands
import unittest
import md5

import thumbnail as T


genRose = lambda x: os.system('convert rose: %s' % x)
exists = os.path.exists


class ThumbnailTests(unittest.TestCase):
	def md5(self, p):
		return md5.new(p).hexdigest()
	
	def path(self, m, size):
		return os.path.expanduser('~/.cache/thumbnails/%s/%s.png' % (size, m))
		
	def setUp(self):
		self.rp = '/tmp/rose.png'
		self.ru = 'file:///tmp/rose.png'
		self.rm = self.md5(self.ru)
		self.rt = os.path.expanduser('~/.cache/thumbnails/large/%s.png' % self.rm)
		genRose(self.rp)
		self.rmt = int(os.path.getmtime(self.rp))
		
		self.tp = '/tmp/test.txt'
		self.tu = 'file:///tmp/test.txt'
		self.tm = self.md5(self.tu)
		self.tt = os.path.expanduser('~/.cache/thumbnails/large/%s.png' % self.tm)
		self.tf = os.path.expanduser('~/.cache/thumbnails/fail/test-1.0/%s.png' % self.tm)
		os.system(': > /tmp/test.txt')
		self.tmt = int(os.path.getmtime(self.tp))
		
		self.rmRose()
		self.rmTxt()
		
		
	def rmRose(self):
		try:
			os.unlink(self.rt)
		except Exception:
			pass
	
	def rmTxt(self):
		try:
			os.unlink(self.tf)
		except Exception:
			pass
	
	def testNotExisting(self):
		self.assertFalse(T.is_thumbnail_failed(self.rp, 'test-1.0'))
		self.assertFalse(T.is_thumbnail_failed(self.ru, 'test-1.0'))
		
		self.assertEqual(T.thumbnail_path(self.rp, 'large'), self.rt)
		self.assertEqual(T.thumbnail_path(self.ru, 'large'), self.rt)
		self.assertEqual(T.thumbnail_path(self.rp, 256), self.rt)
		
		self.assertEqual(T.existing_thumbnail_path(self.rp, 'large'), False)
		self.assertEqual(T.existing_thumbnail_path(self.ru, 'large', self.rmt), False)
		self.assertEqual(T.existing_thumbnail_path(self.rp, 256), False)
		self.assertFalse(exists(self.rt))
		
	
	def testMFail(self):
		self.assertFalse(T.is_thumbnail_failed(self.tp, 'test-1.0'))
		self.assertFalse(T.is_thumbnail_failed(self.tu, 'test-1.0'))
		self.assertFalse(exists(self.tf))
		
		T.put_fail(self.tp, 'test-1.0')
		
		self.assert_(T.is_thumbnail_failed(self.tp, 'test-1.0'))
		self.assert_(T.is_thumbnail_failed(self.tu, 'test-1.0'))
		self.assert_(exists(self.tf))
		
		self.rmTxt()
	
	def testAFail(self):
		self.assertFalse(T.is_thumbnail_failed(self.tp, 'test-1.0'))
		self.assertFalse(exists(self.tf))

		T.gen_image_thumbnail(self.tp)
		self.assertFalse(T.is_thumbnail_failed(self.tp, 'test-1.0'))
		self.assertFalse(exists(self.tf))
		
		T.gen_image_thumbnail(self.tp, use_fail_appname='test-1.0')
		self.assert_(T.is_thumbnail_failed(self.tp, 'test-1.0'))
		self.assert_(exists(self.tf))
		
		self.rmTxt()
	
	def testThumb(self):
		self.assertFalse(T.existing_thumbnail_path(self.rp))
		self.assertFalse(exists(self.rt))
		
		T.gen_image_thumbnail(self.rp)
		self.assert_(T.existing_thumbnail_path(self.ru, mtime=self.rmt))
		self.assert_(exists(self.rt))
		
		self.rmRose()
		
		self.assertFalse(T.existing_thumbnail_path(self.ru, mtime=self.rmt))
		self.assertFalse(exists(self.rt))
		
		T.gen_image_thumbnail(self.rp)
		self.assert_(T.existing_thumbnail_path(self.rp))
		self.assert_(exists(self.rt))
		
	def testMod(self):
		T.gen_image_thumbnail(self.rp)
		self.assert_(T.existing_thumbnail_path(self.rp))
		self.assert_(exists(self.rt))
		
		os.system('touch -r / %s' % self.rp)
		self.assertFalse(T.existing_thumbnail_path(self.rp))
		self.assert_(exists(self.rt))
	
	def tearDown(self):
		self.rmRose()
		self.rmTxt()
		
		try:
			os.unlink(self.rp)
		except Exception:
			pass
			
		try:
			os.unlink(self.tp)
		except Exception:
			pass
		


unittest.main()
