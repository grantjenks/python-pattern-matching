# Changelog

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
