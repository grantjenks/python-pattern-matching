import re

import patternmatching as pm
import pytest


TEXT_CASES = [
    ("a" + pm.anything + "c", "axyzc"),
    ("a" + pm.anything + "c", "ac"),
    ("a" + pm.anyone * pm.repeat(min=2, max=3) + "c", "abbc"),
    (pm.padding + "ab" * pm.either + "c", "zzabc-tail"),
    ("a" + "bc" * pm.exclude + "d", "aed"),
    ("a" + "bc" * pm.exclude + "d", "abd"),
    ("a.b" * pm.group("literal"), "a.b!"),
    ("a" + pm.anyone + "c", "a\nc"),
    (pm.Pattern(pm.bind.item, pm.bind.item), "xx"),
    (pm.Pattern(pm.bind.item, pm.bind.item), "xy"),
]


@pytest.mark.parametrize(("pattern", "value"), TEXT_CASES)
@pytest.mark.parametrize("full", [False, True])
def test_native_matches_generic_text_semantics(pattern, value, full):
    native = pm.Matcher(native=True)
    generic = pm.Matcher(native=False)
    method = "fullmatch" if full else "match"

    native_result = getattr(native, method)(value, pattern)
    generic_result = getattr(generic, method)(value, pattern)

    assert native_result == generic_result
    assert (native_result is None) == (generic_result is None)


BYTES_CASES = [
    (pm.Pattern(97) + pm.anything + 99, b"axyzc"),
    (pm.Pattern(97) + pm.anyone + 99, b"a\nc"),
    (pm.Pattern(97) + (b"bc" * pm.group("middle")), b"abc!"),
    (pm.Pattern(pm.bind.item, pm.bind.item), b"zz"),
    (pm.Pattern(pm.bind.item, pm.bind.item), b"zy"),
]


@pytest.mark.parametrize(("pattern", "value"), BYTES_CASES)
@pytest.mark.parametrize("full", [False, True])
def test_native_matches_generic_bytes_semantics(pattern, value, full):
    native = pm.Matcher(native=True)
    generic = pm.Matcher(native=False)
    method = "fullmatch" if full else "match"

    native_result = getattr(native, method)(value, pattern)
    generic_result = getattr(generic, method)(value, pattern)

    assert native_result == generic_result
    assert (native_result is None) == (generic_result is None)


def test_native_compiler_is_used_for_supported_patterns():
    pattern = "a" + pm.anything + ("bc" * pm.group("tail"))
    first = pm._compile_native(pattern, str)
    second = pm._compile_native(pattern, str)

    assert first is not None
    assert first is second
    assert isinstance(first.regex, re.Pattern)
    assert pm.match("axyzbc!", pattern) == {"tail": "bc"}


def test_native_compiler_falls_back_as_a_unit():
    pattern = pm.Pattern(pm.like(lambda value: value == "a", name=None), "b")

    assert pm._compile_native(pattern, str) is None
    assert pm.match("ab", pattern) == {}
    assert pm.fullmatch("ab", pattern) == {}


def test_native_exclude_without_options_matches_one_item():
    pattern = "a" + pm.exclude + "c"

    assert pm._compile_native(pattern, str) is not None
    assert pm.fullmatch("abc", pattern) == {}


def test_like_supports_text_bytes_and_compiled_patterns():
    text = pm.match("item-42", pm.like(r"item-(\d+)"))
    binary = pm.match(b"item-42", pm.like(rb"item-(\d+)"))
    compiled = pm.match("ABC", pm.like(re.compile("[a-z]+", re.IGNORECASE)))

    assert text.match.group(1) == "42"
    assert binary.match.group(1) == b"42"
    assert compiled.match.group() == "ABC"
    assert pm.match("item-42", pm.like(rb"item-(\d+)")) is None
