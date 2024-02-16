"""The voltage signal class, :class:`.VoltageSignal`, is a specialized signal for timestamps and voltages, shipped
as part of |ProjectName| and used throughout the examples in the documentation. It is also available to use from the
user code."""

from typing import Literal

import numpy as np
import numpy.typing as npt

from ..exceptions import VoltageSignalError
from ..plotter import Units
from .edges import EdgesMixin
from .filters import BesselFiltersMixin, ButterworthFiltersMixin, EllipticFiltersMixin
from .signal import Signal
from .state_levels import StateLevelsMixin


class VoltageSignal(
    ButterworthFiltersMixin,
    EllipticFiltersMixin,
    BesselFiltersMixin,
    StateLevelsMixin,
    EdgesMixin,
    Signal,
):
    """Predefined implementation of a :class:`.Signal` that represents an analog voltage signal as captured,
    for example, by an oscilloscope, data recorder or similar.

    The horizontal axis of the signal contains the timestamps values and the vertical axis of the signal contains
    the voltage values, in miliseconds or seconds and in milivolts or volts respectively."""

    # pylint: disable=too-many-ancestors

    ## Private API #####################################################################################################
    def __init__(
        self,
        timestamps: npt.NDArray[np.float_],
        voltages: npt.NDArray[np.float_],
        timestamp_unit_id: Literal["ms", "s"] | None = None,
        voltage_unit_id: Literal["mV", "V"] | None = None,
    ) -> None:
        """Class constructor.

        :param timestamps: The timestamp values for the signal.
        :param voltages: The voltage values for the signal.
        :param timestamp_unit_id: An identifier for the timestamp units, can be ignored if not plotting.
        :param voltage_unit_id: An identifier for the voltage units, can be ignored if not plotting."""
        super().__init__(
            hvalues=timestamps,
            vvalues=voltages,
            hunits=None if timestamp_unit_id is None else self.__get_timestamp_units(timestamp_unit_id),
            vunits=None if voltage_unit_id is None else self.__get_voltage_units(voltage_unit_id),
        )

    @staticmethod
    def __get_timestamp_units(unit_id: Literal["ms", "s"]) -> Units:
        """Obtains timestamp unit definitions for :class:`.Plotter` from a timestamp unit identifier.

        :param unit_id: The timestamp unit identifier.
        :raise VoltageSignalError: The timestamp unit identifier is not recognized.
        :return: Timestamp units."""
        if unit_id == "ms":
            return Units("Milliseconds", "ms", "Time")
        if unit_id == "s":
            return Units("Seconds", "s", "Time")
        raise VoltageSignalError(f"The timestamp unit identifier '{unit_id}' is not recognized.")

    @staticmethod
    def __get_voltage_units(unit_id: Literal["mV", "V"]) -> Units:
        """Obtains voltage unit definitions for :class:`.Plotter` from a voltage unit identifier.

        :param unit_id: The voltage unit identifier.
        :raise VoltageSignalError: The voltage unit identifier is not recognized.
        :return: Voltage units."""
        if unit_id == "mV":
            return Units("Millivolts", "mV", "Voltage")
        if unit_id == "V":
            return Units("Volts", "v", "Voltage")
        raise VoltageSignalError(f"The voltage unit identifier '{unit_id}' is not recognized.")

    ## Protected API ###################################################################################################

    ## Public API ######################################################################################################
    @property
    def timestamps(self) -> npt.NDArray[np.float_]:
        """Getter for the timestamps.

        :return: The timestamps."""
        return self._hv

    @property
    def voltages(self) -> npt.NDArray[np.float_]:
        """Getter for the voltages

        :return: The voltages."""
        return self._vv

    @property
    def timestamp_units(self) -> Units:
        """Getter for the timestamp units.

        :return: The timestamps units."""
        return self._hunits

    @property
    def voltage_units(self) -> Units:
        """Getter for the voltage units.

        :return: The voltage units."""
        return self._vunits
