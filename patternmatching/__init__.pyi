from collections.abc import Callable, Hashable, Iterable, Iterator, Mapping, Sequence
from contextlib import AbstractContextManager
from re import Pattern as RegexPattern
from types import TracebackType
from typing import Any, TypeVar

_CallableT = TypeVar("_CallableT", bound=Callable[..., Any])

infinity: float
literal_types: tuple[type[Any], ...]
like_errors: tuple[type[Exception], ...]

class Case:
    name: str
    predicate: Callable[[Matcher, Any, Any], bool]
    action: Callable[[Matcher, Any, Any], Any]
    def __init__(
        self,
        name: str,
        predicate: Callable[[Matcher, Any, Any], bool],
        action: Callable[[Matcher, Any, Any], Any],
    ) -> None: ...

class Mismatch(Exception): ...

class APattern(Sequence[Any]):
    def __getitem__(self, index: int | slice) -> Any: ...
    def __len__(self) -> int: ...
    def __add__(self, that: Any) -> Pattern: ...
    def __radd__(self, that: Any) -> Pattern: ...

class Pattern(APattern):
    def __init__(self, *args: Any) -> None: ...

class PatternMixin(APattern):
    def __mul__(self, that: Any) -> PatternMixin: ...

class Anyone(PatternMixin):
    def __init__(self) -> None: ...

anyone: Anyone

class Repeat(PatternMixin):
    pattern: Any
    min: int
    max: int | float
    greedy: bool
    def __init__(
        self,
        pattern: Any = (),
        min: int = 0,
        max: float = infinity,
        greedy: bool = True,
    ) -> None: ...
    def __call__(
        self,
        min: int = 0,
        max: float = infinity,
        greedy: bool = True,
        pattern: Any = (),
    ) -> Repeat: ...

repeat: Repeat
maybe: Repeat
anything: Repeat
something: Repeat
padding: Repeat

class Group(PatternMixin):
    pattern: Any
    name: Hashable | None
    def __init__(self, pattern: Any = (), name: Hashable | None = None) -> None: ...
    def __call__(self, name: Hashable | None = None, pattern: Any = ()) -> Group: ...

group: Group

class Options(PatternMixin):
    def __init__(self, *options: Any) -> None: ...
    def __call__(self, *options: Any) -> Options: ...

class Either(Options): ...
class Exclude(Options): ...

either: Either
exclude: Exclude

class Name:
    value: Hashable
    def __init__(self, value: Hashable) -> None: ...

class Binder:
    any: Anyone
    def __getattr__(self, name: str) -> Name: ...

bind: Binder

class Like:
    pattern: (
        str | bytes | RegexPattern[str] | RegexPattern[bytes] | Callable[[Any], Any]
    )
    name: Hashable | None
    def __init__(
        self,
        pattern: str
        | bytes
        | RegexPattern[str]
        | RegexPattern[bytes]
        | Callable[[Any], Any],
        name: Hashable | None = "match",
    ) -> None: ...

def like(
    pattern: str
    | bytes
    | RegexPattern[str]
    | RegexPattern[bytes]
    | Callable[[Any], Any],
    name: Hashable | None = "match",
) -> Like: ...

class RecordPattern:
    cls: type[Any]
    attributes: tuple[tuple[str, Any], ...]
    def __init__(
        self,
        cls: type[Any],
        patterns: Iterable[Any],
        attributes: Mapping[str, Any],
    ) -> None: ...

def record(cls: type[Any], *patterns: Any, **attributes: Any) -> RecordPattern: ...

class Equal:
    value: Any
    def __init__(self, value: Any) -> None: ...

def equal(value: Any) -> Equal: ...

class Match(Mapping[Hashable, Any]):
    def __init__(
        self,
        bindings: Mapping[Hashable, Any] | Iterable[tuple[Hashable, Any]] = (),
    ) -> None: ...
    def __getattr__(self, attr: str) -> Any: ...
    def __getitem__(self, key: Hashable) -> Any: ...
    def __iter__(self) -> Iterator[Hashable]: ...
    def __len__(self) -> int: ...

class _BoundScope(AbstractContextManager[Bounder]):
    def __enter__(self) -> Bounder: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool: ...
    def __call__(self, func: _CallableT) -> _CallableT: ...

class Bounder:
    limit: int | None
    def __init__(
        self,
        matches: Iterable[Match | Mapping[Hashable, Any]] = (),
        *,
        limit: int | None = 10,
    ) -> None: ...
    def __getattr__(self, attr: str) -> Any: ...
    def __getitem__(self, key: Hashable) -> Any: ...
    def __iter__(self) -> Iterator[Hashable]: ...
    def __len__(self) -> int: ...
    def push(self, match: Match | Mapping[Hashable, Any]) -> Match: ...
    def pop(self) -> Match: ...
    def reset(self) -> None: ...
    def scope(self) -> _BoundScope: ...

class Matcher:
    cases: Iterable[Case]
    bound: Bounder
    native: bool
    def __init__(
        self,
        cases: Iterable[Case] | None = None,
        *,
        bound_limit: int | None = 10,
        native: bool = True,
    ) -> None: ...
    def match(self, value: Any, pattern: Any) -> Match | None: ...
    def fullmatch(self, value: Any, pattern: Any) -> Match | None: ...
    def visit(self, value: Any, pattern: Any) -> Any: ...

matcher: Matcher
bound: Bounder

def match(value: Any, pattern: Any) -> Match | None: ...
def fullmatch(value: Any, pattern: Any) -> Match | None: ...
