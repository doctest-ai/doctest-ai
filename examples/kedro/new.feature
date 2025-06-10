Feature: New Kedro project

  Scenario: Create a new kedro project without example code
    When I ask Claude to create a new kedro project named "Project Dummy" without example code
    Then the expected project directories and files should be created
