"""Step definitions for the fixed vocabulary in agent_app/services/gherkin.py.

Each step is registered for Given, When and Then (stacked decorators; pytest-bdd binds them to this
module) so the keyword a scenario uses never matters.
Selectors use the AUT's data-testid attributes (AUT-4).
"""
import re

from playwright.sync_api import expect
from pytest_bdd import given, parsers, then, when


def _tid(page, name):
    return page.get_by_test_id(name)


@given(parsers.re(r"I am on the registration page"))
@when(parsers.re(r"I am on the registration page"))
@then(parsers.re(r"I am on the registration page"))
def open_page(page, aut_url):
    page.goto(aut_url)


@given(parsers.re(r'I enter username "(?P<value>[^"]*)" and password "(?P<password>[^"]*)"'))
@when(parsers.re(r'I enter username "(?P<value>[^"]*)" and password "(?P<password>[^"]*)"'))
@then(parsers.re(r'I enter username "(?P<value>[^"]*)" and password "(?P<password>[^"]*)"'))
def enter_both(page, value, password):
    _tid(page, "username").fill(value)
    _tid(page, "password").fill(password)


@given(parsers.re(r'I enter username "(?P<value>[^"]*)"'))
@when(parsers.re(r'I enter username "(?P<value>[^"]*)"'))
@then(parsers.re(r'I enter username "(?P<value>[^"]*)"'))
def enter_username(page, value):
    _tid(page, "username").fill(value)


@given(parsers.re(r'I enter password "(?P<value>[^"]*)"'))
@when(parsers.re(r'I enter password "(?P<value>[^"]*)"'))
@then(parsers.re(r'I enter password "(?P<value>[^"]*)"'))
def enter_password(page, value):
    _tid(page, "password").fill(value)


@given(parsers.re(r"I click Register"))
@when(parsers.re(r"I click Register"))
@then(parsers.re(r"I click Register"))
def click_register(page):
    _tid(page, "register").click()


@given(parsers.re(r'I should see an error message containing "(?P<text>[^"]+)"'))
@when(parsers.re(r'I should see an error message containing "(?P<text>[^"]+)"'))
@then(parsers.re(r'I should see an error message containing "(?P<text>[^"]+)"'))
def see_error_containing(page, text):
    expect(_tid(page, "error")).to_be_visible()
    expect(_tid(page, "error")).to_contain_text(re.compile(re.escape(text), re.IGNORECASE))


@given(parsers.re(r"I should not see an error message"))
@when(parsers.re(r"I should not see an error message"))
@then(parsers.re(r"I should not see an error message"))
def no_error(page):
    expect(_tid(page, "error")).to_be_hidden()


@given(parsers.re(r'I should see "(?P<text>[^"]+)"'))
@when(parsers.re(r'I should see "(?P<text>[^"]+)"'))
@then(parsers.re(r'I should see "(?P<text>[^"]+)"'))
def see_text(page, text):
    # Visible elements only: text in a hidden element must not count as "seen".
    expect(page.get_by_text(text).locator("visible=true").first).to_be_visible()


@given(parsers.re(r'I should not see "(?P<text>[^"]+)"'))
@when(parsers.re(r'I should not see "(?P<text>[^"]+)"'))
@then(parsers.re(r'I should not see "(?P<text>[^"]+)"'))
def not_see_text(page, text):
    expect(page.get_by_text(text).locator("visible=true")).to_have_count(0)


@given(parsers.re(r"the password field should be masked"))
@when(parsers.re(r"the password field should be masked"))
@then(parsers.re(r"the password field should be masked"))
def password_masked(page):
    expect(_tid(page, "password")).to_have_attribute("type", "password")


@given(parsers.re(r"I should see the (?P<element>Username field|Password field|Register button)"))
@when(parsers.re(r"I should see the (?P<element>Username field|Password field|Register button)"))
@then(parsers.re(r"I should see the (?P<element>Username field|Password field|Register button)"))
def see_element(page, element):
    name = {"Username field": "username", "Password field": "password", "Register button": "register"}[element]
    expect(_tid(page, name)).to_be_visible()
