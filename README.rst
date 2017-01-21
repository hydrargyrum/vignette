Vignette
========

Vignette is a Python library to create and manage thumbnails following the FreeDesktop standard.

Thumbnails are stored in a shared directory so other apps following the standard can reuse
them without having to generate their own thumbnails.

Vignette can typically be used in file managers, image browsers, etc.

Thumbnails are not limited to image files on disk but can be generated for other file types,
for example videos or documents but also for any URL, for example a web browser could store
thumbnails for recently visited pages or bookmarks.

Vignette by itself can only generate thumbnails for local image files but can retrieve
thumbnail for any file or URL, if another app generated a thumbnail for it. An app can also
generate a thumbnail by its own means and use vignette to push that thumbnail to the store.

Documentation
=============

The documentation can be `read online <https://vignette.readthedocs.io/>`_.

This library has querying functions, that do not generate thumbnails, and can be used with files or URLs, that can be non-images:

* build_thumbnail_path
* try_get_thumbnail
* is_thumbnail_failed

It has functions that have side effects, which write thumbnails, or "fail-files" (if a thumbnail couldn't be generated), they can require local-files (see the function's doc):

* get_thumbnail
* create_thumbnail
* put_thumbnail
* put_fail

Examples
--------

Just ask for thumbnails of local images, automatically creating them if necessary::

  import vignette

  thumb_image = vignette.get_thumbnail('/my/file.jpg')
  local_app_display(thumb_image)


Ask for a thumbnail or generate it manually, for example a web-browser generating pages previews, that this module can't do itself::

  import vignette

  orig_url = 'http://example.com/file.pdf'
  thumb_image = vignette.try_get_thumbnail(orig_url, mtime=0) # mtime is not used in this example

  if not thumb_image:
    thumb_image = vignette.build_thumbnail_path(orig_url, 'large')
    try:
      local_app_make_preview(orig_url, thumb_image)
    except NetworkError:
      vignette.put_fail(orig_url, 'mybrowser-1.0', mtime=0)
    else:
      thumb_image = vignette.put_thumbnail(orig_url, 'large', mtime=0)
    if is_thumbnail_failed(orig_url):
      thumb_image = 'error.png'

  local_app_display(thumb_image)

Requirements
============

Vignette works with both Python 2 and Python 3.

Vignette requires at least one image backend to work properly.
See the backends section below.

Backends
========

Vignette does not contain image format code. In order to generate a thumbnail from an image or
update metadata as required by the Freedestkop standard, vignette uses external libraries.
The dependencies are "lazy" though: if an external library is missing, vignette ignores it and
falls back on other equivalent libs.

Backends are divided in 2 types:

* thumbnail backends, which create a thumbnail image from a source image file, a source video
  file, or another input URL
* metadata backends, which are used internally in vignette to manage the metadata of thumbnails

Vignette currently has thumbnail/metadata backends supporting:

* Python Imaging Library (PIL)
* PyQt
* PythonMagick

One of these libraries is required for vignette to work in basic cases (thumbnailing local images).

Vignette has thumbnail backends to support these tools:

* `ffmpegthumbnailer <https://github.com/dirkvdb/ffmpegthumbnailer/>`_, supporting video files
* pdftocairo from `poppler-utils <https://poppler.freedesktop.org/>`_, supporting PDF documents
* `ooo-thumbnailer <https://launchpad.net/ooo-thumbnailer>`_, supporting OpenOffice documents

If a lib is not present, vignette continues to operate but thumbnails for certain file formats
may not be generated.

License
=======

Vignette is licensed under the `WTFPLv2 <http://wtfpl.net>`_.

Version
=======

Vignette is currently at version 4.3.3 and uses `Semantic Versioning <http://semver.org/>`_.
