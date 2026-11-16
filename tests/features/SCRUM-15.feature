Feature: SCRUM-15 Registration page: some criteria met, some not (expected partial pass)

@AC-1 @positive
Scenario: Page shows username, password and register button
  Given I am on the registration page
  Then I should see the Username field
  And I should see the Password field
  And I should see the Register button

@AC-2 @positive
Scenario: Password field is masked after typing a password
  Given I am on the registration page
  When I enter password "secret123"
  Then the password field should be masked

@AC-2 @edge
Scenario: Password with special characters is masked
  Given I am on the registration page
  When I enter password "P@ss w0rd!#%"
  Then the password field should be masked

@AC-3 @positive
Scenario: Valid username and long password shows HELLO WORLD
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

@AC-4 @positive
Scenario: Password of 4 characters is accepted
  Given I am on the registration page
  When I enter username "alice" and password "abcd"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-4 @boundary
Scenario: Password of 3 characters does not show HELLO WORLD
  Given I am on the registration page
  When I enter username "alice" and password "abc"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-5 @negative
Scenario: Empty username with password does not show HELLO WORLD
  Given I am on the registration page
  When I enter password "password123"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-5 @edge
Scenario: Empty username and empty password does not show HELLO WORLD
  Given I am on the registration page
  When I click Register
  Then I should not see "HELLO WORLD"

@AC-5 @boundary
Scenario: Single character username is not treated as empty
  Given I am on the registration page
  When I enter username "a" and password "password123"
  And I click Register
  Then I should see "HELLO WORLD"
