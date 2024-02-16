"""The signal generator, :class:`.SignalGenerator`, can be used to generate different kinds arrays suitable to create
signals for testing. A code snippet of its use along with :class:`.VoltageSignal` is shown below:

.. code-block:: python

    import signal_edges.signal as ses

    # Create generator with initial values.
    generator = ses.generator.SignalGenerator(0, 0.001, 100, 0, 100)

    # Build signal with multiple pulses.
    for _ in range(0, 4):
        generator.add_flat(10)
        generator.add_edge("falling", 0.0, 10)
        generator.add_flat(10)
        generator.add_edge("rising", 100.0, 10)

    # Generate signal with some noise.
    (signal_x, signal_y) = generator.generate(noise=(0, 5))
    signal = ses.VoltageSignal(signal_x, signal_y, "s", "V")
    
    # Plot signal.
    signal.signal_plot("signal.png")
    
This code snippet generates the following plot:

.. figure:: ../../.assets/img/008_example_generated_signal.png
    :width: 600
    :align: center
    
    The generated signal."""

from typing import Literal

import numpy as np
import numpy.typing as npt

from ...definitions import get_logger
from ...exceptions import SignalError


class SignalGenerator:
    """Generates arrays for the horizontal axis and vertical axis of :class:`.Signal` derived classes."""

    ## Private API #####################################################################################################
    def __init__(self, hinit: float, hstep: float, vhigh: float, vlow: float, vinit: float) -> None:
        """Class constructor.

        :param hinit: Initial value on the horizontal axis.
        :param hstep: Step between values of the horizontal axis, created automatically as values on the vertical axis
            are added.
        :param vhigh: The highest value on the vertical axis, used to calculate the full range of the signal.
        :param vlow: The lowest value on the vertical axis, used to calculate the full range of the signal.
        :param vinit: The initial value of the vertical axis, as a percentage of the full range, ``vhigh`` - ``vlow``.
        :raise SignalError: At least one of the parameters given is invalid."""
        # pylint: disable=too-many-arguments

        # Check for valid arguments.
        if any([vhigh <= vlow, hstep <= 0, vinit < 0, vinit > 100]):
            raise SignalError("The parameters passed to the signal generator constructor are invalid.")

        #: Logger.
        self._logger = get_logger()
        #: The step between values of the signal in the horizontal axis.
        self._hstep = hstep
        #: The highest value of the signal in the vertical axis.
        self._vhigh = vhigh
        #: The lowest value of the signal in the vertical axis.
        self._vlow = vlow
        #: Full range of the signal, derived from t1he highest and lowest values on the vertical axis.
        self._vrange = np.absolute(self._vhigh - self._vlow)
        #: Accumulated values on the horizontal axis.
        self.__hv: npt.NDArray[np.float_] = np.full((1, 1), hinit)[0]
        #: Accumulated values on the vertical axis.
        self.__vv: npt.NDArray[np.float_] = np.full((1, 1), self._vvalue(vinit))[0]

    ## Protected API ###################################################################################################
    def _vvalue(self, percentage: float) -> np.float_:
        """Calculates a value for the vertical axis from a percentage.

        :param percentage: The percentage value of the full range.
        :raise SignalError: The target value must be a percentage value.
        :return: The absolute value."""
        # Ensure that the target value is a percentage value.
        if any([percentage < 0, percentage > 100]):
            raise SignalError(f"The target percentage '{percentage}%' is not a value in the range zero to one hundred.")
        return self._vlow + self._vrange * (percentage / 100)

    ## Public API ######################################################################################################
    def add_flat(self, values: int) -> "SignalGenerator":
        """Adds a flat section, using the last value on the vertical axis as reference.

        :param values: Number of values to add to both horizontal and vertical axes.
        :raise SignalError: The number of values must be larger than zero.
        :return: Instance of the class."""
        # Ensure that the number of values to add is largen than zero.
        if values <= 0:
            raise SignalError(f"The number of values, '{values}', must be a positive number.")

        # Get the initial for the beginning of the section.
        hval = self.__hv[-1]
        vval = self.__vv[-1]

        # Generate the sections.
        hsect = np.linspace(hval, hval + self._hstep * values, num=values + 1, endpoint=True)
        vsect = np.full((1, values), vval)[0]

        # Generate samples.
        self.__hv = np.concatenate([self.__hv, hsect[1:]])
        self.__vv = np.concatenate([self.__vv, vsect])

        return self

    def add_edge(self, edge_type: Literal["rising", "falling"], vtarget: float, values: int) -> "SignalGenerator":
        """Adds a rising or falling edge.

        :param edge_type: The type of edge to add.
        :param values: Number of values to add to both horizontal and vertical axes.
        :param vtarget: The target value on the vertical axis at the end of the edge, as a percentage of the full range.
        :raise SignalError: The number of values must be larger than zero.
        :raise SignalError: The type of edge is not valid.
        :raise SignalError: The target value must be higher than the current value for a rising edge.
        :raise SignalError: The target value must be lower than the current value for a falling edge.
        :return: Instance of the class."""
        # Ensure that the number of values to add is largen than zero.
        if values <= 0:
            raise SignalError(f"The number of values, {values}, must be a positive number.")
        # The type of edge is not recognized.
        if edge_type not in ("rising", "falling"):
            raise SignalError("The type of the edge provided is not valid.")

        # Update target value to absolute number.
        vtarget_val = self._vvalue(vtarget)

        # Ensure the target value is higher than the current value for rising edges.
        if edge_type == "rising" and vtarget_val <= self.__vv[-1]:
            raise SignalError("Target value is below the current value of the signal, can't add rising edge.")
        # Ensure the target value is lower than the current value for falling edges.
        if edge_type == "falling" and self.__vv[-1] <= vtarget_val:
            raise SignalError("Target value is above the current value of the signal, can't add falling edge.")

        # Get the initial for the beginning of the section.
        hval = self.__hv[-1]
        vval = self.__vv[-1]

        # Generate the sections.
        hsect = np.linspace(hval, hval + self._hstep * values, num=values + 1, endpoint=True)
        vsect = np.linspace(vval, vtarget_val, num=values + 1, endpoint=True)

        # Generate values.
        self.__hv = np.concatenate([self.__hv, hsect[1:]])
        self.__vv = np.concatenate([self.__vv, vsect[1:]])

        return self

    def repeat(self, count: int = 1) -> "SignalGenerator":
        """Repeats the current pattern the specified number of times.

        :param count: The number of times to repeat the signal.
        :raise SignalError: The number of times to repeat the signal not one or higher.
        :return: Instance of the class."""
        # Ensure the number of times to repeat the signal is valid.
        if count < 1:
            raise SignalError(f"The number of times to repeat, {count}, the signal must be 1 or higher.")

        # Generate the horizontal section.
        hval = self.__hv[-1]
        values = len(self.__hv) * count
        hsect = np.linspace(hval, hval + self._hstep * values, num=values + 1, endpoint=True)

        # Generate the vertical section.
        vsect = np.tile(self.__vv, count)

        # Generate values.
        self.__hv = np.concatenate([self.__hv, hsect[1:]])
        self.__vv = np.concatenate([self.__vv, vsect])

        return self

    def generate(
        self, noise: tuple[float, float] | None = None, hdecs: int | None = None, vdecs: int | None = None
    ) -> tuple[npt.NDArray[np.float_], npt.NDArray[np.float_]]:
        """Obtains the values for the generated signal, optionally adding Gaussian noise.

        :param noise: Gaussian noise to add, `mean` and `stddev` respectively, defaults to no noise.
        :param hdecs: Number of decimals to round the horizontal axis values to, defaults to no rounding.
        :param vdecs: Number of decimals to round the vertical axis values to, defaults to no rounding.
        :return: The values of the horizontal axis and the values of the vertical axis."""
        # Create copies of the arrays.
        hvalues = np.copy(self.__hv)
        vvalues = np.copy(self.__vv)

        # Add noise if requested.
        if noise is not None:
            vvalues = vvalues + np.random.normal(noise[0], noise[1], len(vvalues))
        # Round horizontal axis values if requested.
        if hdecs is not None:
            hvalues = np.round(hvalues, hdecs)
        # Round vertical axis values if requested.
        if vdecs is not None:
            vvalues = np.round(vvalues, vdecs)

        return (hvalues, vvalues)

    @property
    def count(self) -> int:
        """Number of values in the signal.

        :return: Number of values currently in the signal."""
        return len(self.__hv)
