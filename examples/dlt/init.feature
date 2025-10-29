Feature: New dlt project

  Background:
    Given I have installed dlt

  Scenario: Create a new dlt project
    Given I have configured the following CLI options in Claude Code:
      | allowed_tools | Write,Bash(python pokemon_pipeline.py:*),Edit |
    When I ask Claude to create a dlt project with a single pipeline that loads data from the Pokemon API and stores it in a local directory
    Then the pipeline runs successfully
