from cicadad.core.decorators import scenario
from cicadad.core.engine import Engine

engine = Engine()


@scenario(engine)
def my_first_test(context):
    # Results of previously run scenarios get passed in as context

    # Write the body of your test here
    assert 2 + 2 == 4

    # Anything returned gets saved as a user output
    return "Passed!"


if __name__ == "__main__":
    engine.start()
