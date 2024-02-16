"""Tests for signal edges."""

import os
from typing import Literal

import pytest

from signal_edges.signal import VoltageSignal
from signal_edges.signal.edges import IntPointPolicy, Type
from signal_edges.signal.generator import SignalGenerator
from signal_edges.signal.state_levels import StateLevels

from .conftest import env_plots


class TestEdges:
    """A collection of tests for signal edges."""

    # pylint: disable=no-self-use

    ## Private API #####################################################################################################

    ## Protected API ###################################################################################################
    def _get_signal_gen(self, vinit: float) -> SignalGenerator:
        """Creates a signal generator for testing.

        :param vinit: The initial value.
        :return: The signal generator."""
        return SignalGenerator(0.0, 1.0, 50, -50, vinit)

    def _get_state_levels(self) -> StateLevels:
        """Generates a predefined state levels for testing.

        :return: State levels for testing."""
        return StateLevels(
            highest=50.0,
            high=40.0,
            high_runt=20.0,
            intermediate=0.0,
            low_runt=-20.0,
            low=-40.0,
            lowest=-50.0,
        )

    def _v(self, value_id: Literal["high", "int_high_0", "int_high_1", "int_low_0", "int_low_1", "low"]) -> float:
        """Returns a fixed value from a given value identifier, as described below.

        A ``high`` value is in the ``high`` threshold.
        A ``int_high_1`` value is in the ``int_high`` and ``runt_high`` thresholds.
        A ``int_high_0`` value is in the ``int_high``, ``runt_low`` and ``runt_high`` thresholds.
        A ``int_low_0`` value is in the ``int_low``, ``runt_low`` and ``runt_high`` thresholds.
        A ``int_low_1`` value is in the ``int_low`` and ``runt_low`` thresholds.
        A ``low`` value is in the ``low`` threshold.

        :param value_id: The value identifier.
        :param offset: An optional offset to apply to the values, keep it in the range [-4, 4].
        :return: Fixed value within the specified threshold."""
        if value_id == "high":
            return 95.0
        if value_id == "int_high_1":
            return 70.0
        if value_id == "int_high_0":
            return 60.0
        if value_id == "int_low_0":
            return 40.0
        if value_id == "int_low_1":
            return 30.0
        if value_id == "low":
            return 5.0

        raise RuntimeError(f"The value identifier '{value_id}' is invalid.")

    ## Public API ######################################################################################################
    @pytest.mark.parametrize("adir", ["edges/test_falling_and_rising_edges"], indirect=True)
    @pytest.mark.parametrize("sval", [1, 2, 3, 8])
    @pytest.mark.parametrize("ipol", list(IntPointPolicy))
    def test_falling_and_rising_edges(self, adir: str, sval: int, ipol: IntPointPolicy) -> None:
        """Tests a signal with falling and rising edges.

        :param adir: The path where the plots will be stored.
        :param sval: Number of values per section in the generated signal.
        :param ipol: The intermediate point policy to use."""
        # Create signal generator.
        gen = self._get_signal_gen(self._v("high"))

        # Build signal.
        gen.add_flat(sval)
        gen.add_edge("falling", self._v("low"), sval)
        gen.add_flat(sval)
        gen.add_edge("rising", self._v("high"), sval)
        gen.add_flat(sval)
        gen.add_edge("falling", self._v("low"), sval)
        gen.add_flat(sval)
        gen.add_edge("rising", self._v("high"), sval)
        gen.add_flat(sval)

        # Generate signal and get edges.
        signal = VoltageSignal(*gen.generate())
        edges = signal.edges(self._get_state_levels(), ipol)

        # Plot to file.
        if env_plots():
            signal.edges_plot(os.path.join(adir, f"sval{sval}_ipol{ipol}.png"), edges)

        # Perform assertions on edges.
        assert len(edges) == 4

        # Perform assertions on edge #0.
        assert edges[0]["edge_type"] is Type.FALLING
        assert edges[0]["ibegin"] == sval * 1
        assert edges[0]["iend"] == sval * 2
        assert edges[0]["ibegin"] <= edges[0]["iintermediate"] <= edges[0]["iend"]

        # Perform assertions on edge #1.
        assert edges[1]["edge_type"] is Type.RISING
        assert edges[1]["ibegin"] == sval * 3
        assert edges[1]["iend"] == sval * 4
        assert edges[1]["ibegin"] <= edges[1]["iintermediate"] <= edges[1]["iend"]

        # Perform assertions on edge #2.
        assert edges[2]["edge_type"] is Type.FALLING
        assert edges[2]["ibegin"] == sval * 5
        assert edges[2]["iend"] == sval * 6
        assert edges[2]["ibegin"] <= edges[2]["iintermediate"] <= edges[2]["iend"]

        # Perform assertions on edge #3.
        assert edges[3]["edge_type"] is Type.RISING
        assert edges[3]["ibegin"] == sval * 7
        assert edges[3]["iend"] == sval * 8
        assert edges[3]["ibegin"] <= edges[3]["iintermediate"] <= edges[3]["iend"]

    @pytest.mark.parametrize("adir", ["edges/test_runt_falling_and_rising_edges"], indirect=True)
    @pytest.mark.parametrize("sval", [1, 2, 3, 8])
    @pytest.mark.parametrize("ipol", list(IntPointPolicy))
    @pytest.mark.parametrize("rint", [0, 1])
    def test_runt_falling_and_rising_edges(self, adir: str, sval: int, ipol: IntPointPolicy, rint: int) -> None:
        """Tests a signal with runt falling and rising edges.

        :param adir: The path where the plots will be stored.
        :param sval: Number of values per section in the generated signal.
        :param ipol: The intermediate point policy to use.
        :param rint: Whether to use ``int_low_0`` or ``int_low_1`` values."""
        # Create signal generator.
        gen = self._get_signal_gen(self._v("high"))

        # Build signal.
        gen.add_flat(sval)
        gen.add_edge("falling", self._v("int_low_1" if rint == 1 else "int_low_0"), sval)
        gen.add_flat(sval)
        gen.add_edge("rising", self._v("high"), sval)
        gen.add_flat(sval)
        gen.add_edge("falling", self._v("int_low_1" if rint == 1 else "int_low_0"), sval)
        gen.add_flat(sval)
        gen.add_edge("rising", self._v("high"), sval)
        gen.add_flat(sval)

        # Generate signal and get edges.
        signal = VoltageSignal(*gen.generate())
        edges = signal.edges(self._get_state_levels(), ipol)

        # Plot to file.
        if env_plots():
            signal.edges_plot(os.path.join(adir, f"rint_{rint}_sval{sval}_ipol{ipol}.png"), edges)

        # Perform assertions on edges.
        assert len(edges) == 4

        # Perform assertions on edge #0.
        assert edges[0]["edge_type"] is Type.FALLING_RUNT
        assert edges[0]["ibegin"] == sval * 1
        assert edges[0]["iend"] == sval * 2
        assert edges[0]["ibegin"] <= edges[0]["iintermediate"] <= edges[0]["iend"]

        # Perform assertions on edge #1.
        assert edges[1]["edge_type"] is Type.RISING_RUNT
        assert edges[1]["ibegin"] == sval * 3
        assert edges[1]["iend"] == sval * 4
        assert edges[1]["ibegin"] <= edges[1]["iintermediate"] <= edges[1]["iend"]

        # Perform assertions on edge #2.
        assert edges[2]["edge_type"] is Type.FALLING_RUNT
        assert edges[2]["ibegin"] == sval * 5
        assert edges[2]["iend"] == sval * 6
        assert edges[2]["ibegin"] <= edges[2]["iintermediate"] <= edges[2]["iend"]

        # Perform assertions on edge #3.
        assert edges[3]["edge_type"] is Type.RISING_RUNT
        assert edges[3]["ibegin"] == sval * 7
        assert edges[3]["iend"] == sval * 8
        assert edges[3]["ibegin"] <= edges[3]["iintermediate"] <= edges[3]["iend"]

    @pytest.mark.parametrize("adir", ["edges/test_rising_and_falling_edges"], indirect=True)
    @pytest.mark.parametrize("sval", [1, 2, 3, 8])
    @pytest.mark.parametrize("ipol", list(IntPointPolicy))
    def test_rising_and_falling_edges(self, adir: str, sval: int, ipol: IntPointPolicy) -> None:
        """Tests a signal with rising and falling edges.

        :param adir: The path where the plots will be stored.
        :param sval: Number of values per section in the generated signal.
        :param ipol: The intermediate point policy to use."""
        # Create signal generator.
        gen = self._get_signal_gen(self._v("low"))

        # Build signal.
        gen.add_flat(sval)
        gen.add_edge("rising", self._v("high"), sval)
        gen.add_flat(sval)
        gen.add_edge("falling", self._v("low"), sval)
        gen.add_flat(sval)
        gen.add_edge("rising", self._v("high"), sval)
        gen.add_flat(sval)
        gen.add_edge("falling", self._v("low"), sval)
        gen.add_flat(sval)

        # Generate signal and get edges.
        signal = VoltageSignal(*gen.generate())
        edges = signal.edges(self._get_state_levels(), ipol)

        # Plot to file.
        if env_plots():
            signal.edges_plot(os.path.join(adir, f"sv{sval}_ip{ipol}.png"), edges)

        # Perform assertions on edges.
        assert len(edges) == 4

        # Perform assertions on edge #0.
        assert edges[0]["edge_type"] is Type.RISING
        assert edges[0]["ibegin"] == sval * 1
        assert edges[0]["iend"] == sval * 2
        assert edges[0]["ibegin"] <= edges[0]["iintermediate"] <= edges[0]["iend"]

        # Perform assertions on edge #1.
        assert edges[1]["edge_type"] is Type.FALLING
        assert edges[1]["ibegin"] == sval * 3
        assert edges[1]["iend"] == sval * 4
        assert edges[1]["ibegin"] <= edges[1]["iintermediate"] <= edges[1]["iend"]

        # Perform assertions on edge #2.
        assert edges[2]["edge_type"] is Type.RISING
        assert edges[2]["ibegin"] == sval * 5
        assert edges[2]["iend"] == sval * 6
        assert edges[2]["ibegin"] <= edges[2]["iintermediate"] <= edges[2]["iend"]

        # Perform assertions on edge #3.
        assert edges[3]["edge_type"] is Type.FALLING
        assert edges[3]["ibegin"] == sval * 7
        assert edges[3]["iend"] == sval * 8
        assert edges[3]["ibegin"] <= edges[3]["iintermediate"] <= edges[3]["iend"]

    @pytest.mark.parametrize("adir", ["edges/test_runt_rising_and_falling_edges"], indirect=True)
    @pytest.mark.parametrize("sval", [1, 2, 3, 8])
    @pytest.mark.parametrize("ipol", list(IntPointPolicy))
    @pytest.mark.parametrize("rint", [0, 1])
    def test_runt_rising_and_falling_edges(self, adir: str, sval: int, ipol: IntPointPolicy, rint: int) -> None:
        """Tests a signal with runt rising and falling edges.

        :param adir: The path where the plots will be stored.
        :param sval: Number of values per section in the generated signal.
        :param ipol: The intermediate point policy to use.
        :param rint: Whether to use ``int_high_0`` or ``int_high_1`` values."""
        # Create signal generator.
        gen = self._get_signal_gen(self._v("low"))

        # Build signal.
        gen.add_flat(sval)
        gen.add_edge("rising", self._v("int_high_1" if rint == 1 else "int_high_0"), sval)
        gen.add_flat(sval)
        gen.add_edge("falling", self._v("low"), sval)
        gen.add_flat(sval)
        gen.add_edge("rising", self._v("int_high_1" if rint == 1 else "int_high_0"), sval)
        gen.add_flat(sval)
        gen.add_edge("falling", self._v("low"), sval)
        gen.add_flat(sval)

        # Generate signal and get edges.
        signal = VoltageSignal(*gen.generate())
        edges = signal.edges(self._get_state_levels(), ipol)

        # Plot to file.
        if env_plots():
            signal.edges_plot(os.path.join(adir, f"rint_{rint}_sval{sval}_ipol{ipol}.png"), edges)

        # Perform assertions on edges.
        assert len(edges) == 4

        # Perform assertions on edge #0.
        assert edges[0]["edge_type"] is Type.RISING_RUNT
        assert edges[0]["ibegin"] == sval * 1
        assert edges[0]["iend"] == sval * 2
        assert edges[0]["ibegin"] <= edges[0]["iintermediate"] <= edges[0]["iend"]

        # Perform assertions on edge #1.
        assert edges[1]["edge_type"] is Type.FALLING_RUNT
        assert edges[1]["ibegin"] == sval * 3
        assert edges[1]["iend"] == sval * 4
        assert edges[1]["ibegin"] <= edges[1]["iintermediate"] <= edges[1]["iend"]

        # Perform assertions on edge #2.
        assert edges[2]["edge_type"] is Type.RISING_RUNT
        assert edges[2]["ibegin"] == sval * 5
        assert edges[2]["iend"] == sval * 6
        assert edges[2]["ibegin"] <= edges[2]["iintermediate"] <= edges[2]["iend"]

        # Perform assertions on edge #3.
        assert edges[3]["edge_type"] is Type.FALLING_RUNT
        assert edges[3]["ibegin"] == sval * 7
        assert edges[3]["iend"] == sval * 8
        assert edges[3]["ibegin"] <= edges[3]["iintermediate"] <= edges[3]["iend"]

    @pytest.mark.parametrize("adir", ["edges/test_special_edges"], indirect=True)
    @pytest.mark.parametrize("sval", [1, 2, 3, 8])
    def test_special_edges(self, adir: str, sval: int) -> None:
        """Tests special cases that do not fit anywhere else.

        :param adir: The path where the plots will be stored.
        :param sval: Number of values per section in the generated signal."""
        # pylint: disable=too-many-statements

        signal_num = 0

        ##
        ## Signal without valid low or high values that oscillates in intermediate values.
        ##

        # Create signal generator.
        gen = self._get_signal_gen(self._v("int_high_0"))

        # Build signal.
        gen.add_flat(sval)
        gen.add_edge("falling", self._v("int_low_0"), sval)
        gen.add_flat(sval)
        gen.add_edge("rising", self._v("int_high_0"), sval)
        gen.add_flat(sval)
        gen.add_edge("falling", self._v("int_low_0"), sval)
        gen.add_flat(sval)

        # Generate signal.
        signal = VoltageSignal(*gen.generate())
        edges = signal.edges(self._get_state_levels())

        # Plot to file.
        if env_plots():
            signal.edges_plot(os.path.join(adir, f"{signal_num:03}_sval{sval}.png"), edges)
            signal_num += 1

        # Perform assertions on edges.
        assert len(edges) == 0

        ##
        ## Signal that settles at runt low after going low.
        ##

        # Create signal generator.
        gen = self._get_signal_gen(self._v("high"))

        # Build signal.
        gen.add_flat(sval)
        gen.add_edge("falling", self._v("low"), sval)
        gen.add_flat(sval)
        gen.add_edge("rising", self._v("int_low_0"), sval)
        gen.add_flat(sval)

        # Generate signal.
        signal = VoltageSignal(*gen.generate())
        edges = signal.edges(self._get_state_levels())

        # Plot to file.
        if env_plots():
            signal.edges_plot(os.path.join(adir, f"{signal_num:03}_sval{sval}.png"), edges)
            signal_num += 1

        # Perform assertions on edges.
        assert len(edges) == 1
        assert edges[0]["edge_type"] is Type.FALLING

        ##
        ## Signal that settles at runt high after going high.
        ##

        # Create signal generator.
        gen = self._get_signal_gen(self._v("low"))

        # Build signal.
        gen.add_flat(sval)
        gen.add_edge("rising", self._v("high"), sval)
        gen.add_flat(sval)
        gen.add_edge("falling", self._v("int_high_0"), sval)
        gen.add_flat(sval)

        # Generate signal.
        signal = VoltageSignal(*gen.generate())
        edges = signal.edges(self._get_state_levels())

        # Plot to file.
        if env_plots():
            signal.edges_plot(os.path.join(adir, f"{signal_num:03}_sval{sval}.png"), edges)
            signal_num += 1

        # Perform assertions on edges.
        assert len(edges) == 1
        assert edges[0]["edge_type"] is Type.RISING

        ##
        ## Signal that settles at runt low and then goes high and low.
        ##

        # Create signal generator.
        gen = self._get_signal_gen(self._v("high"))

        # Build signal.
        gen.add_flat(sval)
        gen.add_edge("falling", self._v("int_low_0"), sval)
        gen.add_flat(sval)
        gen.add_edge("rising", self._v("high"), sval)
        gen.add_flat(sval)
        gen.add_edge("falling", self._v("low"), sval)
        gen.add_flat(sval)

        # Generate signal.
        signal = VoltageSignal(*gen.generate())
        edges = signal.edges(self._get_state_levels())

        # Plot to file.
        if env_plots():
            signal.edges_plot(os.path.join(adir, f"{signal_num:03}_sval{sval}.png"), edges)
            signal_num += 1

        # Perform assertions on edges.
        assert len(edges) == 3
        assert edges[0]["edge_type"] is Type.FALLING_RUNT
        assert edges[1]["edge_type"] is Type.RISING_RUNT
        assert edges[2]["edge_type"] is Type.FALLING

        ##
        ## Signal that settles at runt high and then goes low and high.
        ##

        # Create signal generator.
        gen = self._get_signal_gen(self._v("low"))

        # Build signal.
        gen.add_flat(sval)
        gen.add_edge("rising", self._v("int_high_0"), sval)
        gen.add_flat(sval)
        gen.add_edge("falling", self._v("low"), sval)
        gen.add_flat(sval)
        gen.add_edge("rising", self._v("high"), sval)
        gen.add_flat(sval)

        # Generate signal.
        signal = VoltageSignal(*gen.generate())
        edges = signal.edges(self._get_state_levels())

        # Plot to file.
        if env_plots():
            signal.edges_plot(os.path.join(adir, f"{signal_num:03}_sval{sval}.png"), edges)
            signal_num += 1

        # Perform assertions on edges.
        assert len(edges) == 3
        assert edges[0]["edge_type"] is Type.RISING_RUNT
        assert edges[1]["edge_type"] is Type.FALLING_RUNT
        assert edges[2]["edge_type"] is Type.RISING
