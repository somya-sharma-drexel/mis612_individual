Feature: SCRUM-12 CLONE - Registration page: enhanced validation

@AC-1 @positive
Scenario: Username field, Password field and Register button are shown
  Given I am on the registration page
  Then I should see the Username field
  And I should see the Password field
  And I should see the Register button

@AC-2 @positive
Scenario: Valid username and password shows HELLO WORLD
  Given I am on the registration page
  When I enter username "User123" and password "Pass@123"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-2 @negative
Scenario: Empty form does not show HELLO WORLD
  Given I am on the registration page
  When I click Register
  Then I should not see "HELLO WORLD"

@AC-3 @boundary
Scenario: 4-character username is accepted
  Given I am on the registration page
  When I enter username "Abcd" and password "Pass!word"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-3 @boundary
Scenario: 20-character username is accepted
  Given I am on the registration page
  When I enter username "abcdefghij0123456789" and password "Pass!word"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-3 @boundary
Scenario: 3-character username shows Invalid username
  Given I am on the registration page
  When I enter username "Abc" and password "Pass!word"
  And I click Register
  Then I should see an error message containing "Invalid username"
  And I should not see "HELLO WORLD"

@AC-3 @boundary
Scenario: 21-character username shows Invalid username
  Given I am on the registration page
  When I enter username "abcdefghij01234567890" and password "Pass!word"
  And I click Register
  Then I should see an error message containing "Invalid username"
  And I should not see "HELLO WORLD"

@AC-3 @negative
Scenario: Username with special character shows Invalid username
  Given I am on the registration page
  When I enter username "user_name1" and password "Pass!word"
  And I click Register
  Then I should see an error message containing "Invalid username"
  And I should not see "HELLO WORLD"

@AC-3 @negative
Scenario: Username with a space shows Invalid username
  Given I am on the registration page
  When I enter username "user name" and password "Pass!word"
  And I click Register
  Then I should see an error message containing "Invalid username"
  And I should not see "HELLO WORLD"

@AC-3 @edge
Scenario: Empty username shows Invalid username
  Given I am on the registration page
  When I enter password "Pass!word"
  And I click Register
  Then I should see an error message containing "Invalid username"
  And I should not see "HELLO WORLD"

@AC-3 @edge
Scenario: Numbers-only username is accepted
  Given I am on the registration page
  When I enter username "123456" and password "Pass!word"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-4 @positive
Scenario: Password with exclamation mark is accepted
  Given I am on the registration page
  When I enter username "User123" and password "Pass!word"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-4 @negative
Scenario: Password without special character shows Invalid password
  Given I am on the registration page
  When I enter username "User123" and password "Password1"
  And I click Register
  Then I should see an error message containing "Invalid password"
  And I should not see "HELLO WORLD"

@AC-4 @boundary
Scenario: Password with exactly one special character at the end is accepted
  Given I am on the registration page
  When I enter username "User123" and password "Passw0rd@"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-4 @edge
Scenario: Empty password shows Invalid password
  Given I am on the registration page
  When I enter username "User123"
  And I click Register
  Then I should see an error message containing "Invalid password"
  And I should not see "HELLO WORLD"

@AC-4 @edge
Scenario: Password made only of a special character is accepted
  Given I am on the registration page
  When I enter username "User123" and password "@"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-6 @negative
Scenario: Registration with empty Email does not show HELLO WORLD
  Given I am on the registration page
  When I enter username "User123" and password "Pass@123"
  And I click Register
  Then I should not see "HELLO WORLD"
