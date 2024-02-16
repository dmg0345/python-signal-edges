"""Tests for signal state levels."""

import os

import numpy as np
import pytest

from signal_edges.signal import VoltageSignal
from signal_edges.signal.state_levels import Mode

from .conftest import env_plots


class TestStateLevels:
    """A collection of tests for signal state levels."""

    # pylint: disable=no-self-use,too-few-public-methods

    ## Private API #####################################################################################################

    ## Protected API ###################################################################################################

    ## Public API ######################################################################################################
    @pytest.mark.parametrize("adir", ["state_level/test_histogram"], indirect=True)
    def test_histogram(self, adir: str) -> None:
        """Tests the state levels calculated with histogram mode and mean on a signal.

        :param adir: The path where the plots will be stored."""
        # Create signal.
        timestamps = np.arange(0.0, 20.0).astype(np.float_)
        voltages = np.asarray([-10, -10, 10, 10] * 5).astype(np.float_)
        signal = VoltageSignal(timestamps, voltages)

        # Calculate and plot histogram mode results.
        (levels, (hist_x, hist_y)) = signal.state_levels(Mode.HISTOGRAM_MODE)
        if env_plots():
            signal.state_levels_plot(os.path.join(adir, "mode.png"), levels, histogram=(hist_x, hist_y))

        assert np.isclose(levels.highest, 9.9)
        assert np.isclose(levels.high, -9.9 + (9.9 - -9.9) * 0.90)
        assert np.isclose(levels.high_runt, -9.9 + (9.9 - -9.9) * 0.70)
        assert np.isclose(levels.intermediate, -9.9 + (9.9 - -9.9) * 0.50)
        assert np.isclose(levels.low_runt, -9.9 + (9.9 - -9.9) * 0.30)
        assert np.isclose(levels.low, -9.9 + (9.9 - -9.9) * 0.10)
        assert np.isclose(levels.lowest, -9.9)

        # Calculate and plot histogram mean results.
        (levels, (hist_x, hist_y)) = signal.state_levels(Mode.HISTOGRAM_MEAN)
        if env_plots():
            signal.state_levels_plot(os.path.join(adir, "mean.png"), levels, histogram=(hist_x, hist_y))

        assert np.isclose(levels.highest, 9.9)
        assert np.isclose(levels.high, -9.9 + (9.9 - -9.9) * 0.90)
        assert np.isclose(levels.high_runt, -9.9 + (9.9 - -9.9) * 0.70)
        assert np.isclose(levels.intermediate, -9.9 + (9.9 - -9.9) * 0.50)
        assert np.isclose(levels.low_runt, -9.9 + (9.9 - -9.9) * 0.30)
        assert np.isclose(levels.low, -9.9 + (9.9 - -9.9) * 0.10)
        assert np.isclose(levels.lowest, -9.9)
