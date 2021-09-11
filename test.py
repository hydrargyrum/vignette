#!/usr/bin/env pytest

import hashlib
import os
from pathlib import Path
import shutil

import vignette
from pytest import fixture, skip


ALL_THUMBNAIL = vignette.THUMBNAILER_BACKENDS
IMAGE_THUMBNAIL = [vignette.QtBackend(), vignette.PilBackend(), vignette.MagickBackend()]
IMAGE_THUMBNAIL = [b for b in IMAGE_THUMBNAIL if b.is_available()]

ALL_METADATA = vignette.METADATA_BACKENDS
AVAIL_METADATA = [b for b in ALL_METADATA if b.is_available()]

SAMPLES_PATH = Path(__file__).parent / "samples"


@fixture()
def workdir(tmp_path):
	os.environ["XDG_CACHE_HOME"] = str(tmp_path)
	yield tmp_path


@fixture()
def image_src(workdir):
	shutil.copyfile(SAMPLES_PATH / "checkerboard.png", workdir / "test.png")
	src = str(workdir / "test.png")
	yield src


def get_backend_name(backend):
	return type(backend).__name__


@fixture(params=ALL_METADATA, ids=get_backend_name)
def metadata_backend(request):
	if not request.param.is_available():
		skip(f"{request.param} is not available")

	vignette.METADATA_BACKENDS = [request.param]
	vignette.THUMBNAILER_BACKENDS = [request.param]
	yield
	vignette.METADATA_BACKENDS = ALL_METADATA
	vignette.THUMBNAILER_BACKENDS = ALL_THUMBNAIL


def require_pil():
	try:
		import PIL.Image
	except ImportError:
		skip("the test requires PIL for checking correctness")


def get_metadata(path):
	import PIL.Image

	img = PIL.Image.open(path)
	# PIL might not load all metadata without load()
	# in particular, images saved with the magickbackend
	img.load()
	return img.info


def test_at_least_one_backend():
	assert any(backend.is_available() for backend in ALL_METADATA)


def test_hash(image_src, workdir, metadata_backend):
	uri = f"file://{image_src}"
	hash = hashlib.md5(uri.encode("utf-8")).hexdigest()
	dest = workdir / "thumbnails" / "large" / f"{hash}.png"

	assert str(dest) == vignette.build_thumbnail_path(image_src, "large")


def test_metadata(image_src, metadata_backend):
	require_pil()

	dest = vignette.create_thumbnail(image_src, "large")

	assert dest
	info = get_metadata(dest)
	assert info["Thumb::URI"] == f"file://{image_src}"
	assert str(int(os.path.getmtime(image_src))) == info["Thumb::MTime"]
	assert "512" == info["Thumb::Image::Width"]
	assert "512" == info["Thumb::Image::Height"]
	assert str(os.path.getsize(image_src)) == info["Thumb::Size"]


def test_dont_expand(workdir, metadata_backend):
	require_pil()
	import PIL.Image

	src_path = SAMPLES_PATH / "rose.jpg"

	shutil.copy(src_path, workdir)

	thumb_path = vignette.get_thumbnail(str(src_path))
	thumb_img = PIL.Image.open(thumb_path)

	assert thumb_img.size == (70, 46)


def test_shrink(image_src, metadata_backend):
	require_pil()
	import PIL.Image

	thumb_path = vignette.get_thumbnail(str(image_src))
	thumb_img = PIL.Image.open(thumb_path)
	assert thumb_img.size == (256, 256)

	thumb_path = vignette.get_thumbnail(str(image_src), size="normal")
	thumb_img = PIL.Image.open(thumb_path)
	assert thumb_img.size == (128, 128)

	thumb_path = vignette.get_thumbnail(str(image_src), size="x-large")
	thumb_img = PIL.Image.open(thumb_path)
	assert thumb_img.size == (512, 512)

	thumb_path = vignette.get_thumbnail(str(image_src), size="xx-large")
	thumb_img = PIL.Image.open(thumb_path)
	assert thumb_img.size == (512, 512)


def test_basic(image_src, metadata_backend):
	dest = vignette.build_thumbnail_path(image_src, "large")
	assert dest

	assert vignette.try_get_thumbnail(image_src, "large") is None
	assert not os.path.exists(dest)

	assert dest == vignette.get_thumbnail(image_src, "large")
	assert os.path.isfile(dest)

	assert dest == vignette.try_get_thumbnail(image_src, "large")


def test_reuse_thumbnail(image_src, metadata_backend):
	dest = vignette.get_thumbnail(image_src, "large")
	assert dest

	st = os.stat(dest)
	assert dest == vignette.get_thumbnail(image_src, "large")
	assert st == os.stat(dest)
	assert dest == vignette.create_thumbnail(image_src, "large")
	assert st != os.stat(dest)


def test_direct_thumbnail(image_src, metadata_backend):
	dest = vignette.get_thumbnail(image_src, "large")
	assert dest
	assert os.path.isfile(dest)
	assert dest == vignette.try_get_thumbnail(dest, "large")


def test_mtime_validity(image_src, metadata_backend):
	dest = vignette.get_thumbnail(image_src, "large")
	assert dest

	os.utime(image_src, (0, 0))
	assert vignette.try_get_thumbnail(image_src, "large") is None
	assert os.path.isfile(dest)

	assert dest == vignette.get_thumbnail(image_src, "large")
	assert dest == vignette.try_get_thumbnail(image_src, "large")


def test_multisize(image_src, metadata_backend):
	dest = vignette.get_thumbnail(image_src, "large")
	assert dest
	assert dest == vignette.try_get_thumbnail(image_src, "large")
	assert vignette.try_get_thumbnail(image_src, "normal") is None
	assert dest == vignette.try_get_thumbnail(image_src)

	os.remove(dest)
	dest = vignette.get_thumbnail(image_src, "normal")
	assert dest
	assert dest == vignette.try_get_thumbnail(image_src, "normal")
	assert vignette.try_get_thumbnail(image_src, "large") is None
	assert dest == vignette.try_get_thumbnail(image_src)


def test_fail(workdir, metadata_backend):
	src = workdir / "empty"
	src.touch()
	src = str(src)

	assert vignette.get_thumbnail(src, "large") is None
	assert not (workdir / "thumbnails" / "fail").exists()
	assert not vignette.is_thumbnail_failed(src, "foo")

	assert vignette.get_thumbnail(src, "large", use_fail_appname="foo") is None
	assert (workdir / "thumbnails" / "fail" / "foo").exists()
	assert vignette.is_thumbnail_failed(src, "foo")
	assert not vignette.is_thumbnail_failed(src, "bar")


def test_fail_mtime_validity(workdir, metadata_backend):
	src = workdir / "empty"
	src.touch()
	src = str(src)

	assert vignette.get_thumbnail(src, "large", use_fail_appname="foo") is None
	assert vignette.is_thumbnail_failed(src, "foo")

	os.utime(src, (0, 0))
	assert not vignette.is_thumbnail_failed(src, "foo")


def test_put_thumbnail(image_src, metadata_backend):
	uri = "http://example.com"
	tmp = vignette.create_temp("large")
	shutil.copyfile(image_src, tmp)
	vignette.put_thumbnail(uri, "large", tmp, mtime=42)
	assert vignette.try_get_thumbnail(uri, "large", mtime=42)
	assert vignette.try_get_thumbnail(uri, "large", mtime=1) is None


def test_put_fail(image_src, metadata_backend):
	# force a "failure"
	vignette.put_fail(image_src, "foo")

	assert vignette.is_thumbnail_failed(image_src, "foo")
	assert not vignette.is_thumbnail_failed(image_src, "bar")
	# check the failure is found instead of creating a thumbnail
	assert vignette.get_thumbnail(image_src, use_fail_appname="foo") is None

	# create the thumbnail
	dest = vignette.get_thumbnail(image_src, use_fail_appname="bar")
	assert dest

	# check the failure is now ignored
	assert dest == vignette.get_thumbnail(image_src, use_fail_appname="foo")


def test_orientation(workdir, metadata_backend):
	require_pil()
	import PIL.Image

	correct_src = SAMPLES_PATH / "rose.jpg"
	oriented_src = SAMPLES_PATH / "rose-oriented.jpg"

	shutil.copy(correct_src, workdir)
	shutil.copy(oriented_src, workdir)

	correct_dst = vignette.get_thumbnail(str(correct_src))
	correct_img = PIL.Image.open(correct_dst)

	oriented_dst = vignette.get_thumbnail(str(oriented_src))
	oriented_img = PIL.Image.open(oriented_dst)

	assert correct_img.size == oriented_img.size


def test_moreinfo(image_src, metadata_backend):
	require_pil()

	moreinfo = {"foo": "bar", "Thumb::URI": "bad", "Thumb::MTime": "bad"}
	dest = vignette.create_thumbnail(image_src, "large", moreinfo=moreinfo)
	assert dest
	info = get_metadata(dest)

	assert info["foo"] == "bar"
	assert info["Thumb::URI"] != "bad"
	assert info["Thumb::MTime"] != "bad"
