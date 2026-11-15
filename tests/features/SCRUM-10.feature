Feature: SCRUM-10 CLONE - Registration page: core registration and validation

@AC-1 @positive
Scenario: Registration form shows all required controls
  Given I am on the registration page
  Then I should see the Username field
  And I should see the Password field
  And I should see the Register button

@AC-2 @positive
Scenario: Password field masks typed characters
  Given I am on the registration page
  When I enter password "Passw0rd1"
  Then the password field should be masked

@AC-3 @positive
Scenario: Valid username and password shows HELLO WORLD
  Given I am on the registration page
  When I enter username "User1234" and password "Passw0rd1"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-4 @negative
Scenario: Empty username shows required message
  Given I am on the registration page
  When I enter password "Passw0rd1"
  And I click Register
  Then I should see an error message containing "Username and password are required"
  And I should not see "HELLO WORLD"

@AC-4 @negative
Scenario: Empty password shows required message
  Given I am on the registration page
  When I enter username "User1234"
  And I click Register
  Then I should see an error message containing "Username and password are required"
  And I should not see "HELLO WORLD"

@AC-4 @edge
Scenario: Both fields empty shows required message
  Given I am on the registration page
  When I click Register
  Then I should see an error message containing "Username and password are required"
  And I should not see "HELLO WORLD"

@AC-5 @positive
Scenario: Alphanumeric username within length is accepted
  Given I am on the registration page
  When I enter username "Abc123" and password "Passw0rd1"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-5 @boundary
Scenario: Username of 4 characters is accepted
  Given I am on the registration page
  When I enter username "abcd" and password "Passw0rd1"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-5 @boundary
Scenario: Username of 20 characters is accepted
  Given I am on the registration page
  When I enter username "abcde12345abcde12345" and password "Passw0rd1"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-5 @boundary
Scenario: Username of 3 characters is rejected
  Given I am on the registration page
  When I enter username "abc" and password "Passw0rd1"
  And I click Register
  Then I should see an error message containing "Invalid username"
  And I should not see "HELLO WORLD"

@AC-5 @boundary
Scenario: Username of 21 characters is rejected
  Given I am on the registration page
  When I enter username "abcde12345abcde123456" and password "Passw0rd1"
  And I click Register
  Then I should see an error message containing "Invalid username"
  And I should not see "HELLO WORLD"

@AC-5 @negative
Scenario: Username with special characters is rejected
  Given I am on the registration page
  When I enter username "user_name!" and password "Passw0rd1"
  And I click Register
  Then I should see an error message containing "Invalid username"
  And I should not see "HELLO WORLD"

@AC-5 @edge
Scenario: Username containing a space is rejected
  Given I am on the registration page
  When I enter username "user name" and password "Passw0rd1"
  And I click Register
  Then I should see an error message containing "Invalid username"
  And I should not see "HELLO WORLD"

@AC-6 @positive
Scenario: Password with letters and a number is accepted
  Given I am on the registration page
  When I enter username "User1234" and password "LongerPass99"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-6 @boundary
Scenario: Password of 8 characters with a number is accepted
  Given I am on the registration page
  When I enter username "User1234" and password "abcdefg1"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-6 @boundary
Scenario: Password of 7 characters with a number is rejected
  Given I am on the registration page
  When I enter username "User1234" and password "abcdef1"
  And I click Register
  Then I should see an error message containing "Invalid password"
  And I should not see "HELLO WORLD"

@AC-6 @negative
Scenario: Password of 8 letters without a number is rejected
  Given I am on the registration page
  When I enter username "User1234" and password "abcdefgh"
  And I click Register
  Then I should see an error message containing "Invalid password"
  And I should not see "HELLO WORLD"

@AC-6 @edge
Scenario: Password of only digits and 8 characters is accepted
  Given I am on the registration page
  When I enter username "User1234" and password "12345678"
  And I click Register
  Then I should see "HELLO WORLD"
