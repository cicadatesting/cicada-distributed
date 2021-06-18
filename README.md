# cicada-distributed

<!-- FEATURE: build status badges -->

Cicada Distributed is a framework with the goal of making integration, load, and
stress tests less expensive to build. Cicada is designed to manage vast groups
of users to test your services while making tests easier to build and
understand. To get started, install Cicada through pip:

```bash
pip install cicadad
```

You will also need to install Docker in order to use Cicada locally. To install
Docker, visit https://docs.docker.com/get-docker/.

# Example

Before running tests, you must start `redis`, `datastore-client`, and the `container-service`
containers. To start the cluster, run:

```bash
cicada-distributed start-cluster
```

To create a simple test, create a directory and initialize the test scripts:

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

Inside the `test.py`, there will be a basic test:

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

Cicada will build an image for the test and start a test runner. You should see
the test runner collect the scenario and successfully complete.

Finally, stop the cluster:

```bash
cicada-distributed stop-cluster
```

# Documentation

Documentation is available at https://cicadatesting.github.io/cicada-distributed-docs/

Demos are available at https://github.com/cicadatesting/cicada-distributed-demos

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
