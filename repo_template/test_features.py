"""Runs every .feature file in tests/features against the registration page."""
from pytest_bdd import scenarios

from tests.steps.registration_steps import *  # noqa: F403  (registers the steps)

scenarios("features")
