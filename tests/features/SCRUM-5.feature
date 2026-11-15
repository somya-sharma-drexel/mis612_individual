Feature: SCRUM-5 User can register with a username and password

@AC-1 @positive
Scenario: Page shows username, password and register button
  Given I am on the registration page
  Then I should see the Username field
  And I should see the Password field
  And I should see the Register button

@AC-2 @positive
Scenario: Password field masks typed characters
  Given I am on the registration page
  When I enter password "secret123"
  Then the password field should be masked

@AC-2 @edge
Scenario: Password field masks special characters and spaces
  Given I am on the registration page
  When I enter password "P@ss w0rd!#"
  Then the password field should be masked

@AC-3 @positive
Scenario: Valid username and password shows HELLO WORLD
  Given I am on the registration page
  When I enter username "alice" and password "secret123"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-3 @boundary
Scenario: Password of exactly 8 characters shows HELLO WORLD
  Given I am on the registration page
  When I enter username "alice" and password "abcd1234"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-3 @edge
Scenario: Long password with special characters shows HELLO WORLD
  Given I am on the registration page
  When I enter username "alice" and password "L0ng!Passw0rd#With$Many%Characters^1234567890"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-4 @negative
Scenario: Empty username is rejected
  Given I am on the registration page
  When I enter password "secret123"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-4 @negative
Scenario: Empty password is rejected
  Given I am on the registration page
  When I enter username "alice"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-4 @edge
Scenario: Both fields empty is rejected
  Given I am on the registration page
  When I click Register
  Then I should not see "HELLO WORLD"

@AC-5 @negative
Scenario: Short password is rejected
  Given I am on the registration page
  When I enter username "alice" and password "abc"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-5 @boundary
Scenario: Password of 7 characters is rejected
  Given I am on the registration page
  When I enter username "alice" and password "abcd123"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-5 @edge
Scenario: Single character password is rejected
  Given I am on the registration page
  When I enter username "alice" and password "a"
  And I click Register
  Then I should not see "HELLO WORLD"
