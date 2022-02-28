import os

from cicadad.core.decorators import dependency, scenario, tag
from cicadad.core.engine import Engine

os.environ["LC_ALL"] = "C.UTF-8"
os.environ["LANG"] = "C.UTF-8"


engine = Engine()


@scenario(engine)
@tag("run")
def test_a(context):
    print("context:", context)
    assert True
    return 42


@scenario(engine)
@tag("run")
def test_b(context):
    print("context:", context)
    assert False


@scenario(engine)
@tag("run")
@dependency(test_a)
def test_c(context):
    print("context:", context)
    assert True


@scenario(engine)
@tag("run")
@dependency(test_b)
def test_d(context):
    print("context:", context)
    assert False


@scenario(engine)
@tag("dont-run")
def test_e(context):
    print("context:", context)
    assert False


if __name__ == "__main__":
    engine.start()
