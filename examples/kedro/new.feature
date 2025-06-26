Feature: New Kedro project

  Background:
    Given I have installed kedro

  Scenario: Create a new kedro project without example code
    When I ask Claude to create a new kedro project named "Project Dummy" without example code
    Then the expected project directories and files should be created
    And I can install the project-specific dependencies
    And the pipeline registry should contain:
      | __default__ |
    And the pipeline registry should not contain:
      | data_processing |
      | data_science    |
      | reporting       |

  Scenario: Create a new kedro project with example code
    When I ask Claude to create a new kedro project named "Project Dummy" with example code
    Then the expected project directories and files should be created
    And I can install the project-specific dependencies
    And the pipeline registry should contain:
      | __default__     |
      | data_processing |
      | data_science    |
      | reporting       |
