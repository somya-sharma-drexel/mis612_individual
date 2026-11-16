Feature: SCRUM-13 Registration page: criteria that the page meets (expected 100% pass)

@AC-1 @positive
Scenario: Page shows username, password and register controls
  Given I am on the registration page
  Then I should see the Username field
  And I should see the Password field
  And I should see the Register button

@AC-2 @positive
Scenario: Password field masks typed characters
  Given I am on the registration page
  When I enter password "secret123"
  Then the password field should be masked

@AC-3 @positive
Scenario: Valid username and password shows HELLO WORLD
  Given I am on the registration page
  When I enter username "alice" and password "password123"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-3 @boundary
Scenario: Password of exactly 8 characters shows HELLO WORLD
  Given I am on the registration page
  When I enter username "alice" and password "abcd1234"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-3 @edge
Scenario: Very long password shows HELLO WORLD
  Given I am on the registration page
  When I enter username "alice" and password "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz0123456789"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-4 @negative
Scenario: Empty username does not show HELLO WORLD
  Given I am on the registration page
  When I enter password "password123"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-4 @negative
Scenario: Empty password does not show HELLO WORLD
  Given I am on the registration page
  When I enter username "alice"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-4 @edge
Scenario: Both fields empty does not show HELLO WORLD
  Given I am on the registration page
  When I click Register
  Then I should not see "HELLO WORLD"

@AC-5 @negative
Scenario: Short password does not show HELLO WORLD
  Given I am on the registration page
  When I enter username "alice" and password "abc"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-5 @boundary
Scenario: Password of 7 characters does not show HELLO WORLD
  Given I am on the registration page
  When I enter username "alice" and password "abcd123"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-5 @edge
Scenario: Single character password does not show HELLO WORLD
  Given I am on the registration page
  When I enter username "alice" and password "a"
  And I click Register
  Then I should not see "HELLO WORLD"
