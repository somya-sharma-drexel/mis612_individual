Feature: SCRUM-5 User can register with a username and password

@AC-1 @positive
Scenario: Registration page shows all form elements
  Given I am on the registration page
  Then I should see the Username field
  And I should see the Password field
  And I should see the Register button

@AC-2 @positive
Scenario: Password field is masked when a password is typed
  Given I am on the registration page
  When I enter password "secret123"
  Then the password field should be masked

@AC-2 @edge
Scenario: Password field is masked for special characters
  Given I am on the registration page
  When I enter password "P@ss w0rd!#"
  Then the password field should be masked

@AC-3 @positive
Scenario: Valid username and long password shows HELLO WORLD
  Given I am on the registration page
  When I enter username "alice" and password "secret12345"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-3 @boundary
Scenario: Password of exactly 8 characters shows HELLO WORLD
  Given I am on the registration page
  When I enter username "alice" and password "abcd1234"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-3 @edge
Scenario: Password with special characters shows HELLO WORLD
  Given I am on the registration page
  When I enter username "alice" and password "P@ss!w0rd#"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-4 @negative
Scenario: Empty username blocks registration
  Given I am on the registration page
  When I enter password "secret123"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-4 @negative
Scenario: Empty password blocks registration
  Given I am on the registration page
  When I enter username "alice"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-4 @edge
Scenario: Both fields empty blocks registration
  Given I am on the registration page
  When I click Register
  Then I should not see "HELLO WORLD"

@AC-5 @negative
Scenario: Short 3-character password blocks registration
  Given I am on the registration page
  When I enter username "alice" and password "abc"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-5 @boundary
Scenario: Password of 7 characters blocks registration
  Given I am on the registration page
  When I enter username "alice" and password "abcd123"
  And I click Register
  Then I should not see "HELLO WORLD"

@AC-5 @edge
Scenario: Single-character password blocks registration
  Given I am on the registration page
  When I enter username "alice" and password "a"
  And I click Register
  Then I should not see "HELLO WORLD"
