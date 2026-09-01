import asyncio
from collections import namedtuple
from dataclasses import dataclass
from typing import ClassVar

import pytest

import patternmatching as pm


def test_match_result_and_failure():
    result = pm.match([1, 2], [pm.bind.first, pm.bind.second])

    assert isinstance(result, pm.Match)
    assert result == {"first": 1, "second": 2}
    assert result.first == 1
    assert result["second"] == 2
    assert dict(result) == {"first": 1, "second": 2}
    assert pm.match(1, 1) == {}
    assert bool(pm.Match())
    assert pm.match(1, 2) is None


def test_match_is_immutable():
    result = pm.Match({"value": 1})

    with pytest.raises(TypeError):
        result["value"] = 2
    with pytest.raises(AttributeError):
        result.value = 2


def test_bound_history_limit_and_reset():
    matcher = pm.Matcher(bound_limit=3)

    for value in range(5):
        matcher.match(value, pm.bind.value)

    assert len(matcher.bound) == 3
    assert matcher.bound.value == 4
    assert matcher.bound.pop().value == 4
    assert matcher.bound.value == 3
    assert matcher.bound.reset() is None
    assert len(matcher.bound) == 0
    with pytest.raises(LookupError):
        matcher.bound.pop()
    with pytest.raises(TypeError):
        matcher.bound.reset(lambda: None)


def test_bound_limit_validation():
    with pytest.raises(ValueError):
        pm.Bounder(limit=0)
    assert pm.Bounder(limit=None).limit is None


def test_bound_scope_context_manager_and_decorator():
    matcher = pm.Matcher()
    matcher.match("outer", pm.bind.value)

    with matcher.bound.scope():
        matcher.match("inner", pm.bind.value)
        assert matcher.bound.value == "inner"
    assert matcher.bound.value == "outer"

    @matcher.bound.scope()
    def run():
        matcher.match("decorated", pm.bind.value)
        return matcher.bound.value

    assert run() == "decorated"
    assert matcher.bound.value == "outer"

    scope = matcher.bound.scope()
    with scope:
        matcher.match("first", pm.bind.value)
        with scope:
            matcher.match("second", pm.bind.value)
            assert matcher.bound.value == "second"
        assert matcher.bound.value == "first"
    assert matcher.bound.value == "outer"


def test_bound_scope_async_decorator_and_task_isolation():
    matcher = pm.Matcher()
    matcher.match("outer", pm.bind.value)

    @matcher.bound.scope()
    async def scoped():
        await asyncio.sleep(0)
        matcher.match("inner", pm.bind.value)
        await asyncio.sleep(0)
        return matcher.bound.value

    async def worker(value):
        matcher.match(value, pm.bind.value)
        await asyncio.sleep(0)
        return matcher.bound.value

    async def run():
        assert await scoped() == "inner"
        return await asyncio.gather(worker("left"), worker("right"))

    assert asyncio.run(run()) == ["left", "right"]
    assert matcher.bound.value == "outer"


@dataclass
class Point:
    x: int
    y: int


class User:
    __match_args__ = ("name",)

    def __init__(self, name, active):
        self.name = name
        self.active = active


def test_record_dataclass_positional_and_keyword_patterns():
    result = pm.match(Point(2, 3), pm.record(Point, pm.bind.x, y=int))

    assert result == {"x": 2}
    assert repr(pm.record(Point, int, y=3)) == "record(Point, int, y=3)"
    assert pm.match(Point(2, 3), pm.record(Point, 2, y=4)) is None
    assert pm.match(Point(2, 3), pm.record(User, name=str)) is None


def test_record_supports_regular_attribute_objects():
    user = User("Ada", True)

    result = pm.match(user, pm.record(User, pm.bind.name, active=True))

    assert result == {"name": "Ada"}
    assert pm.match(user, pm.record(User, missing=pm.anyone)) is None

    Pair = namedtuple("Pair", "left right")
    assert pm.match(Pair(1, 2), pm.record(Pair, 1, pm.bind.right)) == {"right": 2}


def test_record_and_mapping_bindings_are_transactional():
    record_pattern = pm.either(
        pm.record(Point, x=pm.bind.leaked, y=0),
        pm.record(Point, x=pm.bind.kept, y=3),
    )
    mapping_pattern = pm.either(
        {"x": pm.bind.leaked, "y": 0},
        {"x": pm.bind.kept, "y": 3},
    )

    assert pm.match([Point(2, 3)], record_pattern) == {"kept": 2}
    assert pm.match([{"x": 2, "y": 3}], mapping_pattern) == {"kept": 2}


def test_record_rejects_invalid_construction():
    with pytest.raises(TypeError):
        pm.record(Point, int, int, int)
    with pytest.raises(TypeError):
        pm.record(Point, int, x=int)
    with pytest.raises(TypeError):
        pm.record(object())

    class Invalid:
        __match_args__: ClassVar = ["value"]

    with pytest.raises(TypeError):
        pm.record(Invalid, int)


def test_mapping_patterns_are_recursive_subsets():
    value = {
        "user": {"name": "Ada", "roles": ["admin", "author"]},
        "request_id": 42,
    }
    pattern = {
        "user": {"name": pm.bind.name, "roles": [str, pm.bind.role]},
    }

    result = pm.match(value, pattern)

    assert result == {"name": "Ada", "role": "author"}
    assert pm.match(value, {"missing": pm.anyone}) is None


def test_equal_forces_ordinary_mapping_equality():
    value = {"name": "Ada", "active": True}

    assert pm.match(value, {"name": "Ada"})
    assert pm.match(value, pm.equal({"name": "Ada"})) is None
    assert pm.match(value, pm.equal(value)) == {}
    assert repr(pm.equal(value)) == "equal({'name': 'Ada', 'active': True})"


def test_fullmatch_requires_complete_sequence_consumption():
    pattern = "ab" * pm.group("prefix")

    assert pm.match("abc", pattern) == {"prefix": "ab"}
    assert pm.fullmatch("abc", pattern) is None
    assert pm.fullmatch("ab", pattern) == {"prefix": "ab"}

    list_pattern = [1] + pm.anything
    assert pm.fullmatch([1, 2, 3], list_pattern) == {}
    assert pm.fullmatch([2, 3], list_pattern) is None


def test_custom_matcher_bound_limit_and_native_switch():
    assert pm.Matcher(bound_limit=2).bound.limit == 2
    assert pm.Matcher(native=False).native is False
