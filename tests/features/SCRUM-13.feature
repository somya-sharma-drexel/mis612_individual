Feature: SCRUM-13 Registration page: criteria that the page meets (expected 100% pass)

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

@AC-3 @positive
Scenario: Valid username and long password shows HELLO WORLD
  Given I am on the registration page
  When I enter username "validuser" and password "password123"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-3 @boundary
Scenario: Password of exactly 8 characters shows HELLO WORLD
  Given I am on the registration page
  When I enter username "validuser" and password "pass1234"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-3 @edge
Scenario: Password with special characters of 8+ length shows HELLO WORLD
  Given I am on the registration page
  When I enter username "validuser" and password "P@ss w0rd!#"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-4 @negative
Scenario: Empty username with valid password does not show HELLO WORLD
  Given I am on the registration page
  When I enter password "password123"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-4 @negative
Scenario: Empty password with valid username does not show HELLO WORLD
  Given I am on the registration page
  When I enter username "validuser"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-4 @edge
Scenario: Both fields empty does not show HELLO WORLD
  Given I am on the registration page
  When I click Register
  Then I should not see "HELLO WORLD"

@AC-5 @negative
Scenario: Short password of 3 characters does not show HELLO WORLD
  Given I am on the registration page
  When I enter username "validuser" and password "abc"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-5 @boundary
Scenario: Password of 7 characters does not show HELLO WORLD
  Given I am on the registration page
  When I enter username "validuser" and password "pass123"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-5 @edge
Scenario: Single character password does not show HELLO WORLD
  Given I am on the registration page
  When I enter username "validuser" and password "a"
  And I click Register
  Then I should not see "HELLO WORLD"
