"""Tests for signal filters."""

import os

import pytest

from signal_edges.signal import VoltageSignal
from signal_edges.signal.generator import SignalGenerator

from .conftest import env_plots


class TestFilters:
    """A collection of tests for filters."""

    # pylint: disable=no-self-use,too-few-public-methods

    ## Private API #####################################################################################################

    ## Protected API ###################################################################################################

    ## Public API ######################################################################################################
    @pytest.mark.parametrize("adir", ["filter/test_all_filters"], indirect=True)
    @pytest.mark.parametrize("sval", [10, 20])
    def test_all_filters(self, adir: str, sval: int) -> None:
        """Tests the filtering of a signal with different kinds of filters.

        :param adir: The path where the plots will be stored.
        :param sval: Number of values per section in the generated signal."""
        # Create signal generator, with a sampling frequency of 1MHz.
        sfreq = 1.0e6
        gen = SignalGenerator(0.0, 1 / sfreq, 100.0, 0.0, 100.0)

        # Build signal with multiple pulses.
        for _ in range(0, 3):
            gen.add_flat(sval)
            gen.add_edge("falling", 0.0, sval)
            gen.add_flat(sval)
            gen.add_edge("rising", 100.0, sval)

        # Generate signal with noise.
        (signal_x, signal_v) = gen.generate((0, 10))
        signal = VoltageSignal(signal_x, signal_v, "s", "V")

        # Perform Bessel filtering and save to file.
        bessel_signal = signal.filters_bessel(sfreq, 6, sfreq / 6)
        if env_plots():
            signal.filters_plot(os.path.join(adir, "filter_lowpass_bessel.png"), bessel_signal)

        # Perform Butterworth filtering and save to file.
        butterworth_signal = signal.filters_butterworth(sfreq, 6, sfreq / 6)
        if env_plots():
            signal.filters_plot(os.path.join(adir, "filter_lowpass_butterworth.png"), butterworth_signal)

        # Perform Elliptic filtering and save to file.
        elliptic_signal = signal.filters_elliptic(sfreq, 6, sfreq / 6)
        if env_plots():
            signal.filters_plot(os.path.join(adir, "filter_lowpass_elliptic.png"), elliptic_signal)
