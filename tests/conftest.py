"""Pytest test configuration file."""

import os

## Plugin Register #####################################################################################################
pytest_plugins = [
    ## Third Party Plugins #############################################################################################
    ## Project Plugins #################################################################################################
    "tests.fixtures",
]


def env_plots() -> bool:
    """Determines whether plots are enabled or not in the tests from an environment variable of name
    ``ENABLE_PLOTS``.

    :return: ``True`` if plots are enabled, ``False`` if plots are disabled."""
    return os.environ.get("ENABLE_PLOTS") is not None
