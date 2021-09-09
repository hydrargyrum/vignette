#!/usr/bin/env pytest

import hashlib
import os
import shutil

import vignette
from pytest import fixture, skip


ALL_THUMBNAIL = vignette.THUMBNAILER_BACKENDS
IMAGE_THUMBNAIL = [vignette.QtBackend(), vignette.PilBackend(), vignette.MagickBackend()]
IMAGE_THUMBNAIL = [b for b in IMAGE_THUMBNAIL if b.is_available()]

ALL_METADATA = vignette.METADATA_BACKENDS
AVAIL_METADATA = [b for b in ALL_METADATA if b.is_available()]


@fixture()
def workdir(tmp_path):
	os.environ["XDG_CACHE_HOME"] = str(tmp_path)
	yield tmp_path


@fixture()
def image_src(workdir):
	shutil.copyfile("test.png", workdir / "test.png")
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


def test_at_least_one_backend():
	assert any(backend.is_available() for backend in ALL_METADATA)


def test_hash(image_src, workdir, metadata_backend):
	uri = f"file://{image_src}"
	hash = hashlib.md5(uri.encode("utf-8")).hexdigest()
	dest = workdir / "thumbnails" / "large" / f"{hash}.png"

	assert str(dest) == vignette.build_thumbnail_path(image_src, "large")


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
