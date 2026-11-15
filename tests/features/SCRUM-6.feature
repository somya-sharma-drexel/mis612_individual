Feature: SCRUM-6 Testing Ticket

@AC-1 @positive
Scenario: Registration page shows all form elements
  Given I am on the registration page
  Then I should see the Username field
  And I should see the Password field
  And I should see the Register button

@AC-2 @positive
Scenario: Password characters are masked when typed
  Given I am on the registration page
  When I enter password "Secret123"
  Then the password field should be masked

@AC-3 @positive
Scenario: Valid details show HELLO WORLD
  Given I am on the registration page
  When I enter username "user1234" and password "Passw0rd1"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-4 @negative
Scenario: Empty username shows required error
  Given I am on the registration page
  When I enter password "Passw0rd1"
  And I click Register
  Then I should see an error message containing "Username and password are required"
  And I should not see "HELLO WORLD"

@AC-4 @negative
Scenario: Empty password shows required error
  Given I am on the registration page
  When I enter username "user1234"
  And I click Register
  Then I should see an error message containing "Username and password are required"
  And I should not see "HELLO WORLD"

@AC-4 @edge
Scenario: Both fields empty shows required error
  Given I am on the registration page
  When I click Register
  Then I should see an error message containing "Username and password are required"
  And I should not see "HELLO WORLD"

@AC-5 @positive
Scenario: Mixed letters and numbers username is accepted
  Given I am on the registration page
  When I enter username "User1234" and password "Passw0rd1"
  And I click Register
  Then I should not see "Invalid username"

@AC-5 @boundary
Scenario: Username of 4 characters is accepted
  Given I am on the registration page
  When I enter username "abc1" and password "Passw0rd1"
  And I click Register
  Then I should not see "Invalid username"

@AC-5 @boundary
Scenario: Username of 20 characters is accepted
  Given I am on the registration page
  When I enter username "abcdefghij1234567890" and password "Passw0rd1"
  And I click Register
  Then I should not see "Invalid username"

@AC-5 @boundary
Scenario: Username of 3 characters is rejected
  Given I am on the registration page
  When I enter username "ab1" and password "Passw0rd1"
  And I click Register
  Then I should see "Invalid username"
  And I should not see "HELLO WORLD"

@AC-5 @boundary
Scenario: Username of 21 characters is rejected
  Given I am on the registration page
  When I enter username "abcdefghij1234567890a" and password "Passw0rd1"
  And I click Register
  Then I should see "Invalid username"
  And I should not see "HELLO WORLD"

@AC-5 @negative
Scenario: Username with special characters is rejected
  Given I am on the registration page
  When I enter username "user_12!" and password "Passw0rd1"
  And I click Register
  Then I should see "Invalid username"
  And I should not see "HELLO WORLD"

@AC-5 @edge
Scenario: Username containing a space is rejected
  Given I am on the registration page
  When I enter username "user 123" and password "Passw0rd1"
  And I click Register
  Then I should see "Invalid username"
  And I should not see "HELLO WORLD"

@AC-6 @positive
Scenario: Password with letters and a number is accepted
  Given I am on the registration page
  When I enter username "user1234" and password "Passw0rd123"
  And I click Register
  Then I should not see "Invalid password"

@AC-6 @boundary
Scenario: Password of 8 characters with a number is accepted
  Given I am on the registration page
  When I enter username "user1234" and password "abcdefg1"
  And I click Register
  Then I should not see "Invalid password"

@AC-6 @boundary
Scenario: Password of 7 characters with a number is rejected
  Given I am on the registration page
  When I enter username "user1234" and password "abcdef1"
  And I click Register
  Then I should see "Invalid password"
  And I should not see "HELLO WORLD"

@AC-6 @negative
Scenario: Password of 8 letters without a number is rejected
  Given I am on the registration page
  When I enter username "user1234" and password "abcdefgh"
  And I click Register
  Then I should see "Invalid password"
  And I should not see "HELLO WORLD"

@AC-6 @edge
Scenario: Password of only numbers is accepted
  Given I am on the registration page
  When I enter username "user1234" and password "12345678"
  And I click Register
  Then I should not see "Invalid password"
