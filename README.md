# thumbnail

thumbnail is a Python lib for creating and fetching image thumbnails following the [Freedesktop specification](http://specifications.freedesktop.org/thumbnail-spec/thumbnail-spec-latest.html).

In a nutshell, the specification says, that thumbnails should be 128x128 or 256x256 and should be cached in ~/.cache/thumbnails. If a thumbnail has already been generated for an URL, it can be fetched from the cache first instead of generating a new one.

# Documentation

The Python module is full of docstrings, but here's a short documentation.

This library has querying functions, that do not generate thumbnails, and can be used with files or URLs, that can be non-images :

* thumbnail_path
* existing_thumbnail_path
* is_thumbnail_failed

It has functions that have side effects, which write thumbnails, or "fail-files" (if a thumbnail couldn't be generated), they can require local-files (see the function's doc) :

* gen_image_thumbnail
* force_gen_image_thumbnail
* put_thumbnail
* put_fail

## Examples

Just ask for thumbnails of local images, automatically creating them if necessary:
```
  thumb_image = gen_image_thumbnail('/my/file.jpg')
  local_app_display(thumb_image)
```

Ask for a thumbnail or generate it manually, for example a web-browser generating pages previews, that this module can't do himself:

```
  orig_url = 'http://example.com/file.pdf'
  thumb_image = existing_thumbnail_path(orig_url, mtime=0) # mtime is not used in this example
  
  if not thumb_image:
    try:
      local_app_make_preview(orig_url, '/tmp/preview.jpg')
    except NetworkError:
      put_fail(orig_url, 'mybrowser-1.0', mtime=0)
    else:
      thumb_image = put_thumbnail(orig_url, '/tmp/preview.jpg', mtime=0)
    if is_thumbnail_failed(orig_url):
      thumb_image = 'error.png'
      
  local_app_display(thumb_image)
```


# License

pyfdthumbnail is licensed under the [WTFPLv2](http://wtfpl.net).
