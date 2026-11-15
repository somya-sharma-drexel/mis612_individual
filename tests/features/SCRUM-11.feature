Feature: SCRUM-11 CLONE - Registration page: email sign-up flow

@AC-2 @positive
Scenario: Submit button is labeled Sign Up
  Given I am on the registration page
  Then I should see "Sign Up"

@AC-3 @positive
Scenario: Valid details show Registration successful
  Given I am on the registration page
  When I enter username "user@example.com" and password "Passw0rd!"
  And I click Register
  Then I should see "Registration successful"

@AC-4 @negative
Scenario: Email without @ shows Invalid email
  Given I am on the registration page
  When I enter username "userexample.com" and password "Passw0rd!"
  And I click Register
  Then I should see an error message containing "Invalid email"
  And I should not see "Registration successful"

@AC-4 @positive
Scenario: Email containing @ does not show Invalid email
  Given I am on the registration page
  When I enter username "user@example.com" and password "Passw0rd!"
  And I click Register
  Then I should not see "Invalid email"

@AC-4 @boundary
Scenario: Email consisting only of @ does not show Invalid email
  Given I am on the registration page
  When I enter username "@" and password "Passw0rd!"
  And I click Register
  Then I should not see "Invalid email"

@AC-6 @negative
Scenario: Sign up without ticking Terms checkbox is not successful
  Given I am on the registration page
  When I enter username "user@example.com" and password "Passw0rd!"
  And I click Register
  Then I should not see "Registration successful"
