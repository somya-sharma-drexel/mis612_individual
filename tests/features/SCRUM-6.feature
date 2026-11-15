Feature: SCRUM-6 Testing Ticket

@AC-1 @positive
Scenario: Username, Password and Register button are displayed
  Given I am on the registration page
  Then I should see the Username field
  And I should see the Password field
  And I should see the Register button

@AC-2 @positive
Scenario: Password field masks typed characters
  Given I am on the registration page
  When I enter password "Secret123"
  Then the password field should be masked

@AC-3 @positive
Scenario: Valid details show HELLO WORLD
  Given I am on the registration page
  When I enter username "user1234" and password "Password1"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-4 @negative
Scenario: Empty username shows required error
  Given I am on the registration page
  When I enter password "Password1"
  And I click Register
  Then I should see "Username and password are required"
  And I should not see "HELLO WORLD"

@AC-4 @negative
Scenario: Empty password shows required error
  Given I am on the registration page
  When I enter username "user1234"
  And I click Register
  Then I should see "Username and password are required"
  And I should not see "HELLO WORLD"

@AC-4 @negative
Scenario: Both fields empty shows required error
  Given I am on the registration page
  When I click Register
  Then I should see "Username and password are required"
  And I should not see "HELLO WORLD"

@AC-5 @positive
Scenario: Mixed-case alphanumeric username is accepted
  Given I am on the registration page
  When I enter username "UserName99" and password "Password1"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-5 @boundary
Scenario: 4-character username is accepted
  Given I am on the registration page
  When I enter username "abcd" and password "Password1"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-5 @boundary
Scenario: 20-character username is accepted
  Given I am on the registration page
  When I enter username "abcdefghij0123456789" and password "Password1"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-5 @boundary
Scenario: 3-character username shows Invalid username
  Given I am on the registration page
  When I enter username "abc" and password "Password1"
  And I click Register
  Then I should see "Invalid username"
  And I should not see "HELLO WORLD"

@AC-5 @boundary
Scenario: 21-character username shows Invalid username
  Given I am on the registration page
  When I enter username "abcdefghij01234567890" and password "Password1"
  And I click Register
  Then I should see "Invalid username"
  And I should not see "HELLO WORLD"

@AC-5 @negative
Scenario: Username with special character shows Invalid username
  Given I am on the registration page
  When I enter username "user_123" and password "Password1"
  And I click Register
  Then I should see "Invalid username"
  And I should not see "HELLO WORLD"

@AC-5 @edge
Scenario: Username containing a space shows Invalid username
  Given I am on the registration page
  When I enter username "user 123" and password "Password1"
  And I click Register
  Then I should see "Invalid username"
  And I should not see "HELLO WORLD"

@AC-6 @positive
Scenario: Password with letters and a number is accepted
  Given I am on the registration page
  When I enter username "user1234" and password "Password123"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-6 @boundary
Scenario: 8-character password with a number is accepted
  Given I am on the registration page
  When I enter username "user1234" and password "abcdefg1"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-6 @boundary
Scenario: 7-character password shows Invalid password
  Given I am on the registration page
  When I enter username "user1234" and password "abcdef1"
  And I click Register
  Then I should see "Invalid password"
  And I should not see "HELLO WORLD"

@AC-6 @negative
Scenario: 8-character password without a number shows Invalid password
  Given I am on the registration page
  When I enter username "user1234" and password "abcdefgh"
  And I click Register
  Then I should see "Invalid password"
  And I should not see "HELLO WORLD"

@AC-6 @edge
Scenario: All-digit 8-character password is accepted
  Given I am on the registration page
  When I enter username "user1234" and password "12345678"
  And I click Register
  Then I should see "HELLO WORLD"
