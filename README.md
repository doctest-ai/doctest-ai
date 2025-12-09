# doctest-ai

A pytest plugin that enables testing agentic coding workflows using pytest-bdd.

## What is doctest-ai?

`doctest-ai` allows you to write behavioral tests in natural language using Gherkin syntax (`.feature` files), and have a coding agent execute the `When` step. This is particularly useful for:

- Testing AI-assisted code generation workflows
- Validating that AI can correctly implement framework-specific tasks

`doctest-ai` is intended for testing agentic coding workflows, not for automating testing workflows using AI. You need to define the initial context (`Given` steps) and expected outcome (`Then` steps).

## Prerequisites

Before using `doctest-ai`, ensure you have the following tools installed on your system:

- **Claude Code**: https://code.claude.com/docs/en/setup
- **uv**: https://docs.astral.sh/uv/getting-started/installation/

## Installation

Install `doctest-ai` from PyPI using `uv` or `pip`:

```bash
uv pip install doctest-ai
```

or

```bash
pip install doctest-ai
```

## Quickstart

The `examples/` folder contains several working examples that demonstrate how to use `doctest-ai`:

### Available Examples

- **`examples/dlt/`** - Testing dlt project creation and execution
- **`examples/kedro/`** - Testing Kedro project scaffolding

### Running an Example

1. Navigate to an example directory:

```bash
cd examples/dlt
```

2. Run the test with pytest:

```bash
pytest test_init.py
```

### Example: dlt Project Creation

The `examples/dlt/init.feature` file defines a test scenario:

```gherkin
Feature: New dlt project

  Background:
    Given I have installed dlt

  Scenario: Create a new dlt project
    Given I have configured the following CLI options in Claude Code:
      | allowed_tools | Write,Bash(python pokemon_pipeline.py:*),Edit |
    When I ask Claude to create a dlt project with a single pipeline that loads data from the Pokemon API and stores it in a local directory
    Then the pipeline runs successfully
```

The corresponding `test_init.py` implements the "Then" step:

```python
from doctest_ai.sh_run import run
from pytest_bdd import given, parsers, scenario, then

OK_EXIT_CODE = 0


@scenario("init.feature", "Create a new dlt project")
def test_init():
    pass


@given(parsers.parse("I have installed {package}"))
def install_package(request, package):
    """Install the specified package."""
    run(["uv", "pip", "install", package], check=True, env=request.env)


@then("the pipeline runs successfully")
def run_pipeline(request, tmp_path):
    res = run(["python", "pokemon_pipeline.py"], cwd=tmp_path, env=request.env)
    assert res.returncode == OK_EXIT_CODE, res
```

When you run `pytest test_init.py`, the test will:

1. Install dlt in a temporary virtual environment
2. Configure Claude Code with the specified CLI options
3. Ask Claude to create the dlt project
4. Verify the pipeline runs successfully

## Configuration

### Project Settings

You can configure `doctest-ai` behavior through `pyproject.toml` (under the `[tool.doctest-ai]` section):

- `max_retries`: Number of times to retry if a test fails (enables agentic loop)

### Claude Code Settings

You can specify Claude Code options for your project in `pyproject.toml` (under the `[tool.doctest-ai.claude-code]` section):

```toml
[tool.doctest-ai.claude-code]
model = "claude-3-7-sonnet-20250219"
```

You can also configure Claude Code options in your test scenarios using the `Given` step:

```gherkin
Given I have configured the following CLI options in Claude Code:
  | allowed_tools | Write,Bash,Edit |
  | model         | sonnet          |
```

Configuration at the scenario level overrides overlapping configuration at the project level.
