# cicada-distributed

[![Main-Test](https://github.com/cicadatesting/cicada-distributed/actions/workflows/main-test.yml/badge.svg)](https://github.com/cicadatesting/cicada-distributed/actions/workflows/main-test.yml)

Cicada Distributed is a framework with the goal of making integration, load, and
stress tests less expensive to build. Cicada is designed to manage vast groups
of users to test your services while making tests easier to build and
understand. To get started, install Cicada through pip:

```bash
pip install cicadad
```

# Example

Create a file called `test.py` with the following:

```python
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
```

Next, run the test:

```bash
cicada-distributed run
```

You should see Cicada run the test and print something like this
in the console:

```bash
========================= Test Complete =========================

Passed:

* my_first_test

====================== 1 passed, 0 failed =======================

--------------------- my_first_test: Passed ---------------------

Time Taken: 2.018773 Seconds
Succeeded: 1 Loop(s)
Failed: 0 Loop(s)
Metrics:
                      my_first_test metrics
 ───────────────────────────────────────────────────────────────
  name                 value
 ───────────────────────────────────────────────────────────────
  runtimes             Min: 0.118, Median: 0.118, Average:
                       0.118, Max: 0.118, Len: 1
  results_per_second
  success_rate         100.0
 ───────────────────────────────────────────────────────────────
```

# Example with Docker

To create a test and Dockerfile, create a directory and initialize the test
scripts:

```bash
mkdir example-tests
cicada-distributed init ./example-tests
```

You should see a couple of files:

```
- example-tests
  - test.py
  - Dockerfile
```

Before running tests, you must start a local backend:

```bash
cicada-distributed start-cluster
```

When you run the command `cicada-distributed run --mode=DOCKER`, Cicada will
build an image for the test and start a test runner. You should see the test
runner create a container for the test, scenario, and users when you run
`docker ps`.

Once tests are complete, stop the cluster:

```bash
cicada-distributed stop-cluster
```

# Documentation

Documentation is available at https://cicadatesting.github.io/cicada-distributed-docs/docs/introduction/installation

Demos are available at https://github.com/cicadatesting/cicada-distributed-demos

Cicada Cloud's homepage is https://cicada-cloud.webflow.io/

# Help

If you have a question, please post it on Stack Overflow with the
`cicada-distribtued` tag:

https://stackoverflow.com/questions/tagged/cicada-distributed.

# Chat

For quick questions, please feel free to post them on the
[Discord server](https://discord.gg/WC2Uk2Uh83).

# Bugs

To report a bug, add it to the project's [GitHub issue tracker](https://github.com/cicadatesting/cicada-distributed/issues).

# License

Copyright Jeremy Herzog, 2021.

Cicada Distributed uses the [Apache 2.0 license](LICENSE).
