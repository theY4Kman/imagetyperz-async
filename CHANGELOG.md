# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).


## [Unreleased]


## [0.3.2] — 2023-01-09
### Fixed
 - Resolve `INVALID_REQUEST` with newer versions of httpx, as our auth class improperly handled bytestrings when adding the access token to requests, resulting in url-encoded `b'stuff'`


## [0.3.1] — 2021-11-21
### Fixed
 - DOC: Fix note in README about only supporting reCAPTCHAs (image CAPTCHAs are now also supported)


## [0.3.0] — 2021-11-21
### Added
 - Add image CAPTCHA support (`complete_image`)
 - Allow HTTP client timeouts to be configured


## [0.2.0] - 2020-10-03
### Added
 - Allow usage as async contextmanager to automatically close httpx session


## [0.1.0] - 2020-10-02
### Added
 - Add async ImageTyperz client with reCAPTCHA support
