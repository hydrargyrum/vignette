# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
- default to python 3

## [4.5.2] - 2019-08-17
### Fixed
- add missing "handled_types" attributes and new FILETYPE_MISC type

## [4.5.1] - 2019-08-17
### Fixed
- add __version__ attribute because setup.cfg refered to it

## [4.5.0] - 2019-08-17
### Added
- backends: add oggThumb support for ogg videos
- backends: add exe-thumbnailer support for .exe icons
- backends: add evince-thumbnailer support for PDFs (and atril)
- detect appropriate thumbnail backends using libmagic
- and only call ThumbnailBackends that are appropriate for an input file
- group thumbnailers in categories so they can be enabled selectively

### Fixed
- QtBackend: get accepted mimes list from Qt itself
- QtBackend: test availability
- __main__ should return a non-zero value in case of failure

## [4.4.0] - 2018-05-07
### Added
- use GNOME thumbnailers from /usr/share/thumbnailers
- added a thumbnail dir linter tool

### Fixed
- put_thumbnail: don't set width/height in thumbnail metadata if missing

## [4.3.3] - 2017-01-21
### Fixed
- add VERSION.txt to source

## [4.3.2] - 2016-12-11
### Fixed
- fix ooo-thumbnailer backend seemingly returning an error
- do not ignore some MetadataBackend.update_backend errors

### Added
- add a __main__.py file for running with "-m vignette"

## [4.3.1] - 2016-12-03
### Fixed
- mention backends in module doc and package

## [4.3.0] - 2016-11-29
### Added
- add poppler backend
- add OOo backend
- add FFMpegBackend
- separate backend in 2 types: metadata and thumbnailing

### Fixed
- use unicode literals for closer Python 3 behavior
- backends get_info() method should return None in case of failure

## [4.2.1] - 2016-11-16
### Fixed
- don't fail if directories already exist
- convert floating point numbers MTime to int

### Security
- restrict thumbnail dirs permissions

## [4.2.0] - 2016-11-09
### Added
- add a PyQt backend for generating thumbnails
- more documentation

## [4.1.0] - 2016-10-13
### Added
- MagickBackend adds image dimensions in metadata
- more documentation
