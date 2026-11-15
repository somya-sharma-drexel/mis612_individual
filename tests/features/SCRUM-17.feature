Feature: SCRUM-17 CLONE - Registration page: criteria that the page does not meet (expected 100% fail)

@AC-1 @positive
Scenario: Empty username and password shows HELLO WORLD
  Given I am on the registration page
  When I enter username "" and password ""
  And I click Register
  Then I should see "HELLO WORLD"

@AC-2 @positive
Scenario: Username alice and 3-character password shows HELLO WORLD
  Given I am on the registration page
  When I enter username "alice" and password "abc"
  And I click Register
  Then I should see "HELLO WORLD"

@AC-3 @positive
Scenario: Empty username with password123 shows HELLO WORLD
  Given I am on the registration page
  When I enter username "" and password "password123"
  And I click Register
  Then I should see "HELLO WORLD"
