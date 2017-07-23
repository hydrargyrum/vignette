#!/usr/bin/env python3

"""Tool to clean obsolete thumbnails in ~/.cache/thumbnails
"""

import re
import os
from urllib.request import url2pathname
from urllib.parse import urlparse

import vignette


DELETE_EXTRA = True
COUNT = 0
SIZE = 0

def remove(t):
	global COUNT, SIZE

	COUNT += 1
	SIZE += os.path.getsize(t)
	os.unlink(t)


def do_dir(d):
	global COUNT

	fn_template = re.compile('%s/[0-9a-fA-F]{32}.png$' % re.escape(d))

	for f in os.listdir(d):
		f = os.path.join(d, f)

		if not fn_template.match(f):
			if DELETE_EXTRA:
				print('Extra file %r' % f)
				remove(f)
			continue

		info = vignette.thumbnail_info(f)
		if not info:
			print('Error parsing thumbnail %r' % f)
			remove(f)
			continue

		if not info.get('uri'):
			print('Invalid URI in thumbnail %r' % f)
			remove(f)
			continue

		uri_info = urlparse(info['uri'])
		if uri_info.scheme != 'file':
			continue

		target = url2pathname(uri_info.path)

		if not os.path.isfile(target):
			print('Missing file %r' % target)
			remove(f)
			continue

		if int(os.path.getmtime(target)) != info['mtime']:
			print('Different mtime of %r' % target)
			remove(f)
			continue


if __name__ == '__main__':
	for d in ('large', 'normal'):
		d = os.path.join(vignette._thumb_path_prefix(), d)
		if os.path.isdir(d):
			do_dir(d)
	print('Removed %d files (%d bytes)' % (COUNT, SIZE))
