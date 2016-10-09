#!/usr/bin/env python

# started 2009-03-10
# 2009-03-14
# license: WTFPLv2

# TODO handle more exceptions
# TODO support thumbnails smaller than 128x128
# TODO .thumblocal
# TODO allow mtime no-check


"""Generate and retrieve thumbnails according to the `Freedesktop.org thumbnail standard`_.

Summary of the thumbnail standard
=================================
* Thumbnails of any file or URL (should it be an image, a video, a webpage) can be stored in ~/.cache/thumbnails in PNG format
* Two sizes are used for thumbnails : 128x128 and 256x256, stored respectively in ~/.cache/thumbnails/normal and ~/.cache/thumbnails/large
* files or URLs thumbnailed must have a modification time (mtime for short) to detect obsolescence of thumbnails
* additional metadata can be put in thumbnails, as key/value pairs, in the PNG text fields, such as the time length for a video file
* there are two attributes required to be put in the metadata : the source URI and the mtime, to ensure validity of thumbnail
* if a thumbnail can't be generated by an app (e.g. because of an erroneus file or an unsupported format), a "fail-file" can be written in ~/.cache/thumbnails/fail/<appname-version>
* having a failed thumbnail doesn't mean another app cannot succeed (for example because of format support), then the successful thumbnail can be used everywhere

Module functions
================
The module's functions take care of putting the two mandatory attributes in the thumbnail file.

Functions for querying, that do not generate thumbnails, and can be used with files or URLs, that can be non-images:
* build_thumbnail_path
* try_get_thumbnail
* is_thumbnail_failed

Functions that have side effects, which write thumbnails, or "fail-files", they can require local-files (see the function's doc):
* get_thumbnail
* create_thumbnail
* put_thumbnail
* put_fail


Examples
========

Just ask for thumbnails of local images, automatically creating them if necessary::

  import vignette
  thumb_image = vignette.get_thumbnail('/my/file.jpg')
  local_app_display(thumb_image)

Ask for a thumbnail or generate it manually, for example a web-browser generating pages previews,
that this module can't do itself::

  import vignette
  orig_url = 'http://example.com/file.pdf'
  thumb_image = vignette.try_get_thumbnail(orig_url, mtime=0) # mtime is not used in this example

  if not thumb_image:
    thumb_image = vignette.create_temp('large')
    try:
      local_app_make_preview(orig_url, thumb_image)
    except NetworkError:
      vignette.put_fail(orig_url, 'mybrowser-1.0', mtime=0)
    else:
      thumb_image = vignette.put_thumbnail(orig_url, 'large', thumb_image, mtime=0)
    if vignette.is_thumbnail_failed(orig_url, 'mybrowser-1.0'):
      thumb_image = 'error.png'

  local_app_display(thumb_image)


.. _Freedesktop.org thumbnail standard: https://specifications.freedesktop.org/thumbnail-spec/thumbnail-spec-latest.html

"""


import hashlib
import os
import re
import shutil
import sys
import tempfile

if sys.version_info.major > 2:
	from urllib.request import pathname2url
else:
	from urllib import pathname2url


__all__ = (
	'get_thumbnail',
	'try_get_thumbnail',
	'build_thumbnail_path',
	'create_thumbnail',
	'put_thumbnail',
	'put_fail',
	'is_thumbnail_failed',
	'create_temp',
	'makedirs',
	'KEY_WIDTH',
	'KEY_HEIGHT',
	'KEY_SIZE',
	'KEY_MIME',
	'KEY_DOC_PAGES',
	'KEY_MOVIE_LENGTH',
)

if sys.version_info.major == 2:
	bytes, str = str, unicode


KEY_URI = 'Thumb::URI'
KEY_MTIME = 'Thumb::MTime'
KEY_WIDTH = 'Thumb::Image::Width'
KEY_HEIGHT = 'Thumb::Image::Height'
KEY_SIZE = 'Thumb::Size'
KEY_MIME = 'Thumb::Mimetype'
KEY_DOC_PAGES =  'Thumb::Document::Pages'
KEY_MOVIE_LENGTH = 'Thumb::Movie::Length'


def _any2size(size):
	if size in ('normal', 128, '128'):
		return (128, 'normal')
	elif size in ('large', 256, '256'):
		return (256, 'large')
	elif 0 < size <= 128:
		return 128
	elif 128 < size <= 256:
		return 256

	raise ValueError('unsupported size: %r' % size)


URI_RE = re.compile(r'[a-z][a-z0-9.+-]*:', re.I)


def _any2uri(sth):
	"""Get an URI from the parameter

	If it's already an URI, return it, else return a file:// URL of it
	"""

	if URI_RE.match(sth):
		return sth
	else:
		return 'file://' + pathname2url(os.path.abspath(sth))


def _any2mtime(origname, mtime=None):
	if mtime is None:
		return int(os.path.getmtime(origname))
	else:
		return mtime


def _info_dict(d, mtime=None, src=None):
	d = dict(d or {})

	if mtime is not None or src is not None:
		d.setdefault(KEY_MTIME, str(_any2mtime(src, mtime)))
	if src is not None:
		d.setdefault(KEY_URI, _any2uri(src))

	return d


def _mkstemp(dest):
	fd, path = tempfile.mkstemp(suffix='.png', dir=os.path.dirname(dest))
	os.close(fd)
	os.chmod(path, 0o600)
	return path


def create_temp(size):
	"""Create a temporary file in the parent directory.

	Return the name of a file with a random name (with ".png" suffix) in the parent directory
	of `dest`. Should be used by backends to provide UNIX atomic-rename semantics.
	"""
	size = _any2size(size)[1]
	dir = os.path.join(_thumb_path_prefix(), size)
	os.makedirs(dir)
	return _mkstemp(os.path.join(dir, 'ignored'))


def makedirs():
	"""Create cache directories."""

	root = _thumb_path_prefix()
	os.makedirs(os.path.join(root, 'normal'), 0o700)
	os.makedirs(os.path.join(root, 'large'), 0o700)
	os.makedirs(os.path.join(root, 'fail'), 0o700)


def _thumb_path_prefix():
	xdgcache = os.getenv('XDG_CACHE_HOME', os.path.expanduser('~/.cache'))
	xdgcache = os.path.normpath(xdgcache)
	return os.path.join(xdgcache, 'thumbnails')


def hash_name(src):
	uri = _any2uri(src)
	if isinstance(uri, str):
		uri = uri.encode('utf-8')

	return hashlib.md5(uri).hexdigest()


def is_thumbnail_failed(src, appname, mtime=None):
	"""Is the thumbnail for `name` failed with `appname`?

	:param src: the URL or path of the source file.
	:type src: str
	"""

	prefix = _thumb_path_prefix()
	apppath = os.path.join(prefix, 'fail', appname)
	uri = _any2uri(src)
	mtime = _any2mtime(src, mtime)
	md5uri = hash_name(src)
	thumb = os.path.join(apppath, '%s.png' % md5uri)
	return os.path.exists(thumb) and is_thumbnail_valid(thumb, uri, mtime)


def put_thumbnail(src, size, thumb, mtime=None, moreinfo=None):
	"""Put a thumbnail into the store.

	This method is typically used for thumbnailing non-image files (like PDFs, videos) or
	non-local files.

	The application creates the thumbnail image on its own, and pushes the thumbnail to the
	store with this function. The thumbnail is moved to the correct place and the mandatory
	metadata is set.

	:param src: the URL or path of the source file being thumbnailed.
	:type src: str
	:param size: desired size of thumbnail. Can be any of 'large', 256 for large
	             thumbnails or 'normal', 128 for small thumbnails.
	:param thumb: path of the thumbnail created by the app. This file will be moved to the
	              target. It is advised to use :any:`create_temp` for obtaining a file path.
	:param mtime: the modification time of the file thumbnailed. If `mtime` is None, `src`
	              has to be a local file and its mtime will be read.
	:param moreinfo: additional optional key/values to store in the thumbnail file.
	:type moreinfo: dict
	:returns: the path where the thumbnail has been moved.
	:rtype: str
	"""

	dest = build_thumbnail_path(src, size)

	if dest == thumb:
		# thumb in final place, use a temp file anyway
		tmp = _mkstemp(dest)
		os.rename(dest, tmp)
	elif os.path.dirname(dest) == os.path.dirname(thumb):
		# thumb in the final dir
		tmp = thumb
	else:
		# thumb in any other dir
		tmp = _mkstemp(dest)
		shutil.move(thumb, tmp)

	moreinfo = _info_dict(moreinfo, mtime=mtime, src=src)
	get_backend().update_metadata(tmp, moreinfo)
	os.chmod(tmp, 0o600)
	os.rename(tmp, dest)

	return dest


def put_fail(src, appname, mtime=None, moreinfo=None):
	"""Create a failed thumbnail info file.

	Creates directories if they don't exist.

	When the app tries to generate the thumbnail on its own (to use with :any:`put_thumbnail`)
	and it fails, the app should use this function to indicate the generation failed and it
	should not retry (unless the file has been modified).

	:param src: the URL or path of the file thumbnailed.
	:type src: str
	:param mtime: the modification time of the file thumbnailed. If `mtime` is None, `src`
	              has to be a local file and its mtime will be read.
	:param moreinfo: additional optional key/values to store in the thumbnail file.
	:type moreinfo: dict
	:returns: path of the failed info file
	"""

	prefix = os.path.join(_thumb_path_prefix(), 'fail', appname)
	if not os.path.isdir(prefix):
		os.makedirs(prefix, 0o700)

	md5uri = hash_name(src)
	dest = os.path.join(prefix, '%s.png' % md5uri)

	moreinfo = _info_dict(moreinfo, mtime=mtime, src=src)
	return get_backend().create_fail(dest, moreinfo)


class PilBackend(object):
	@classmethod
	def is_available(cls):
		try:
			import PIL.Image
			import PIL.PngImagePlugin
		except ImportError:
			return False

		cls.mod = PIL.Image
		cls.png = PIL.PngImagePlugin
		return True

	def _pnginfo(self, moreinfo=None):
		outinfo = self.png.PngInfo()

		if moreinfo:
			for k in moreinfo:
				outinfo.add_text(k, str(moreinfo[k]))

		return outinfo

	def create_thumbnail(self, src, dest, size, moreinfo=None):
		try:
			img = self.mod.open(src)
		except IOError:
			return None

		outinfo = self._pnginfo(moreinfo)
		outinfo.add_text(KEY_WIDTH, str(img.size[0]))
		outinfo.add_text(KEY_HEIGHT, str(img.size[1]))

		img.thumbnail((size, size), self.mod.ANTIALIAS)

		tmppath = _mkstemp(dest)

		img.save(tmppath, pnginfo=outinfo)
		img.close()
		os.rename(tmppath, dest)
		return dest

	def create_fail(self, dest, moreinfo=None):
		outinfo = self._pnginfo(moreinfo)

		img = self.mod.new('RGBA', (1, 1))
		tmp = _mkstemp(dest)
		img.save(tmp, pnginfo=outinfo)
		img.close()
		os.rename(tmp, dest)
		return dest

	def get_info(self, path):
		img = self.mod.open(path)
		mtime = int(img.info[KEY_MTIME])

		res = {
			'mtime': mtime,
			'uri': img.info[KEY_URI],
		}
		img.close()
		return res

	def update_metadata(self, dest, moreinfo=None):
		img = self.mod.open(dest)
		outinfo = self._pnginfo(moreinfo)

		tmp = _mkstemp(dest)
		img.save(tmp, pnginfo=outinfo)
		img.close()
		os.rename(tmp, dest)
		return dest


class MagickBackend(object):
	@classmethod
	def is_available(cls):
		try:
			import PythonMagick
		except ImportError:
			return False
		cls.mod = PythonMagick
		return True

	@staticmethod
	def setattributes(img, moreinfo):
		for k in moreinfo or {}:
			v = str(moreinfo[k]).encode('utf-8')
			img.attribute(k, v)

	def create_thumbnail(self, src, dest, size, moreinfo=None):
		try:
			img = self.mod.Image(src)
		except RuntimeError:
			return

		geom = self.mod.Geometry(size, size)
		img.resize(geom)
		self.setattributes(img, moreinfo)

		tmp = _mkstemp(dest)
		img.write(tmp)
		os.rename(tmp, dest)
		return dest

	def update_metadata(self, dest, moreinfo=None):
		try:
			img = self.mod.Image(dest)
		except RuntimeError:
			return
		self.setattributes(img, moreinfo)

		tmp = _mkstemp(dest)
		img.write(tmp)
		os.rename(tmp, dest)
		return dest

	def create_fail(self, dest, moreinfo=None):
		geom = self.mod.Geometry(1, 1)
		color = self.mod.Color()

		img = self.mod.Image(geom, color)
		self.setattributes(img, moreinfo)

		tmp = _mkstemp(dest)
		img.write(tmp)
		os.rename(tmp, dest)
		return dest

	def get_info(self, path):
		try:
			img = self.mod.Image(path)
		except RuntimeError:
			return

		return {
			'mtime': int(img.attribute(KEY_MTIME) or 0),
			'uri': img.attribute(KEY_URI),
		}


BACKENDS = [MagickBackend(), PilBackend()]

def get_backend():
	for backend in BACKENDS:
		if backend.is_available():
			return backend


def create_thumbnail(src, size, moreinfo=None, use_fail_appname=None):
	"""Generate a thumbnail for `filename`, even if the thumbnail existed.

	Returns the path of the thumbnail generated. Creates directories if they don't exist.

	If the thumbnail cannot be generated and `use_fail_appname` is given, a failure info file
	will be generated, associated to the given app name so it is not retried too often.

	:param src: path of the source file. Must be an image file. Cannot be a URL.
	:type src: str
	:param moreinfo: additional optional key/values to store in the thumbnail file.
	:type moreinfo: dict
	:param use_fail_appname: app name to use when creating a failure info.
	:type use_fail_appname: str
	"""

	size = _any2size(size)[0]
	filesize = os.path.getsize(src)
	dest = build_thumbnail_path(src, size)

	moreinfo = _info_dict(moreinfo, src=src)
	moreinfo[KEY_SIZE] = str(filesize)

	if not os.path.isdir(os.path.dirname(dest)):
		os.makedirs(os.path.dirname(dest), 0o700)

	if get_backend().create_thumbnail(src, dest, size, moreinfo):
		return dest

	if use_fail_appname is not None:
		put_fail(src, use_fail_appname)


def build_thumbnail_path(src, size):
	"""Get the path of the potential thumbnail.

	The thumbnail file may or may not exist.

	:param src: path or URI of the source file.
	:type src: str
	:param size: desired size of thumbnail. Can be any of 'large', 256 for large
	             thumbnails or 'normal', 128 for small thumbnails.
	"""

	sizename = _any2size(size)[1]
	prefix = os.path.join(_thumb_path_prefix(), sizename)
	if src.startswith(prefix + '/'):
		return src

	md5uri = hash_name(src)
	return os.path.join(prefix, '%s.png' % md5uri)


def is_thumbnail_valid(thumbnail, uri, mtime):
	info = get_backend().get_info(thumbnail)
	return info['uri'] == uri and info['mtime'] == mtime


def try_get_thumbnail(src, size=None, mtime=None):
	"""Get the path of the thumbnail or None if it doesn't exist.

	:param src: path or URI of the source file.
	:type src: str
	:param size: desired size of thumbnail. Can be 'large', 256 or 'normal', 128. If None,
	             tries with the large thumbnail size first, then with the normal size.
	"""

	if size is None:
		sizes = ['large', 'normal']
	else:
		sizes = [size]

	mtime = _any2mtime(src, mtime)
	uri = _any2uri(src)

	for size in sizes:
		thumb = build_thumbnail_path(src, size)
		if os.path.exists(thumb):
			if src == thumb:
				return src # bypass checks, the URI won't match
			elif is_thumbnail_valid(thumb, uri, mtime):
				return thumb


def get_thumbnail(src, size=None, use_fail_appname=None):
	"""Get the path of the thumbnail and create it if necessary.

	Returns None if an error occured. Creates directories if they don't exist.

	If the thumbnail cannot be found, and a previous failure info file had been created with
	the given app name, the thumbnail generation is not attempted and None is returned.

	:param src: path of the source file. Must be an image file. Cannot be a URL.
	:type src: str
	:param size: desired size of thumbnail. Can be any of 'large', 256 for large
	             thumbnails or 'normal', 128 for small thumbnails. If None, searches for any size.
	:param moreinfo: additional optional key/values to store in the thumbnail file, if the thumbnail did not exist.
	:type moreinfo: dict
	:param use_fail_appname: app name to use when creating a failure info.
	:type use_fail_appname: str
	"""

	thumb = try_get_thumbnail(src, size)
	if thumb is not None:
		return thumb

	if use_fail_appname is not None:
		mtime = _any2mtime(src)
		if is_thumbnail_failed(src, use_fail_appname, mtime):
			return None

	if size is None:
		size = 'large'
	return create_thumbnail(src, size, use_fail_appname=use_fail_appname)


def main():
	print(get_thumbnail(sys.argv[1]))


if __name__ == '__main__':
	main()
