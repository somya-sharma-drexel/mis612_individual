"""Loads the feature file named by QA_FEATURE_FILE and binds it to the step definitions."""
import os

from pytest_bdd import scenarios

from tests_runtime.steps.registration_steps import *

scenarios(os.environ["QA_FEATURE_FILE"])
