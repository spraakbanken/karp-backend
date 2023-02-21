# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## Latest Changes

* changed: use camelCase in all api interactions. PR [#225](https://github.com/spraakbanken/karp-backend/pull/225) by [@kod-kristoff](https://github.com/kod-kristoff).
* Added: Generic Commands. PR [#224](https://github.com/spraakbanken/karp-backend/pull/224) by [@kod-kristoff](https://github.com/kod-kristoff).
* added: cmdtype tags. PR [#223](https://github.com/spraakbanken/karp-backend/pull/223) by [@kod-kristoff](https://github.com/kod-kristoff).
* fix: enable cli resource update again. PR [#222](https://github.com/spraakbanken/karp-backend/pull/222) by [@kod-kristoff](https://github.com/kod-kristoff).
* Simpler workspace. PR [#221](https://github.com/spraakbanken/karp-backend/pull/221) by [@kod-kristoff](https://github.com/kod-kristoff).
* make a monorepo: Use polylith. PR [#220](https://github.com/spraakbanken/karp-backend/pull/220) by [@kod-kristoff](https://github.com/kod-kristoff).
## 6.1.4
* refactor: remove and factor out code. PR [#219](https://github.com/spraakbanken/karp-backend/pull/219) by [@kod-kristoff](https://github.com/kod-kristoff).
* Use Prefix for ES everywhere. PR [#218](https://github.com/spraakbanken/karp-backend/pull/218) by [@kod-kristoff](https://github.com/kod-kristoff).
* Add elasticsearch prefix. PR [#217](https://github.com/spraakbanken/karp-backend/pull/217) by [@kod-kristoff](https://github.com/kod-kristoff).
## 6.1.1

- Use sqlalchemy mypy plugin. PR [#211](https://github.com/spraakbanken/karp-backend/pull/211) by [@kod-kristoff](https://github.com/kod-kristoff).

## 6.1.0

- Use entity id instead. PR [#216](https://github.com/spraakbanken/karp-backend/pull/216) by [@kod-kristoff](https://github.com/kod-kristoff).
- Add mkdocs. PR [#215](https://github.com/spraakbanken/karp-backend/pull/215) by [@kod-kristoff](https://github.com/kod-kristoff).
- Enable lint checks for some modules. PR [#214](https://github.com/spraakbanken/karp-backend/pull/214) by [@kod-kristoff](https://github.com/kod-kristoff).

## 6.0.21

### Added

- Add import entries in cli. PR [#210](https://github.com/spraakbanken/karp-backend/pull/210) by [@kod-kristoff](https://github.com/kod-kristoff).

### Changed

- Rename cli 'entries import' to 'entries add'. PR [#208](https://github.com/spraakbanken/karp-backend/pull/208) by [@kod-kristoff](https://github.com/kod-kristoff).
- Both delete entries routes should return 204. PR [#206](https://github.com/spraakbanken/karp-backend/pull/206) by [@kod-kristoff](https://github.com/kod-kristoff).
- add cli command `entries validate`. PR [#203](https://github.com/spraakbanken/karp-backend/pull/203) by [@kod-kristoff](https://github.com/kod-kristoff).
- Make docs clearer. PR [#202](https://github.com/spraakbanken/karp-backend/pull/202) by [@kod-kristoff](https://github.com/kod-kristoff).

* Fix query-dsl not handling not queries according spec. PR [#201](https://github.com/spraakbanken/karp-backend/pull/201) by [@kod-kristoff](https://github.com/kod-kristoff).
* Handle sort parameters to query correct. PR [#199](https://github.com/spraakbanken/karp-backend/pull/199) by [@kod-kristoff](https://github.com/kod-kristoff).
* Fix cli export and add chunked cli import. PR [#198](https://github.com/spraakbanken/karp-backend/pull/198) by [@kod-kristoff](https://github.com/kod-kristoff).
* fix: handle long_string in transforming. PR [#197](https://github.com/spraakbanken/karp-backend/pull/197) by [@kod-kristoff](https://github.com/kod-kristoff).
* various fixes

## 6.0.20

### Changed

- Return result from commandbus. PR [#196](https://github.com/spraakbanken/karp-backend/pull/196) by [@kod-kristoff](https://github.com/kod-kristoff).
- Add support for discarding entry-repositories. PR [#195](https://github.com/spraakbanken/karp-backend/pull/195) by [@kod-kristoff](https://github.com/kod-kristoff).
- Avoid name clashes in SqlEntryRepository. PR [#194](https://github.com/spraakbanken/karp-backend/pull/194) by [@kod-kristoff](https://github.com/kod-kristoff).
- Fix correct fetching from repos. PR [#193](https://github.com/spraakbanken/karp-backend/pull/193) by [@kod-kristoff](https://github.com/kod-kristoff).

## 6.0.17

### Changed

- Use cache in github actions. PR [#192](https://github.com/spraakbanken/karp-backend/pull/192) by [@kod-kristoff](https://github.com/kod-kristoff).

## 6.0.15

### Changed

- Fix logging error in auth_infrastructure. PR [#191](https://github.com/spraakbanken/karp-backend/pull/191) by [@kod-kristoff](https://github.com/kod-kristoff).
- Handle 'long_string' in entry json schema. PR [#189](https://github.com/spraakbanken/karp-backend/pull/189) by [@kod-kristoff](https://github.com/kod-kristoff).

## 6.0.13

### Added

- Add simple query possibility from cli. PR [#187](https://github.com/spraakbanken/karp-backend/pull/187) by [@kod-kristoff](https://github.com/kod-kristoff).

## 6.0.8

### Changed

- Fix transform error when indexing. PR [#185](https://github.com/spraakbanken/karp-backend/pull/185) by [@kod-kristoff](https://github.com/kod-kristoff).

## 6.0.7
