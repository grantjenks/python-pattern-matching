from importlib.resources import files

import patternmatching


def test_version():
    assert patternmatching.__version__ == "4.0.0"


def test_typing_marker():
    assert files("patternmatching").joinpath("py.typed").is_file()
