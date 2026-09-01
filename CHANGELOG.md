# Changelog

## 4.0.0 — 2026-09-01

- Return an immutable, always-truthy `Match` mapping from successful `match()`
  and `fullmatch()` calls; return `None` for mismatches while retaining ambient
  access through `bound`.
- Make `bound` history context-local, cap it at ten results by default, and add
  `bound.scope()` as a synchronous/asynchronous context manager and decorator.
- Remove the decorator behavior from `bound.reset()`; it now only clears the
  current context's history.
- Add `record()` patterns for dataclasses, named tuples, and arbitrary attribute
  objects using `__match_args__` plus keyword attributes.
- Match bare mappings recursively with subset semantics and add `equal()` to
  force ordinary equality.
- Add `fullmatch()` for complete generic-sequence consumption.
- Support strings, bytes, and compiled patterns in `like()`.
- Accelerate fully translatable helper patterns over `str` and `bytes` with a
  cached, semantics-preserving native `re` backend and conservative whole-pattern
  fallback.
- Ship inline typing metadata and comprehensive v4 documentation and tests.

## 3.1.0 — 2026-08-30

- Support and test Python 3.10 through Python 3.14.
- Replace the legacy setuptools, tox, Pylint, Flake8, Blue, and Sphinx setup
  with `pyproject.toml`, Nox, uv, and GitHub Actions.
- Publish releases from GitHub Actions with PyPI trusted publishing.
- Document composable object patterns, bindings, predicates, custom patterns,
  and regular-expression-style matching over Python sequences.
- Preserve the matching behavior and existing public API from 3.0.1.

## 3.0.1 — 2019-01-12

- Consolidate the package around the function-based pattern matching API.
- Support bindings, predicates, custom patterns, and generic sequence patterns.
