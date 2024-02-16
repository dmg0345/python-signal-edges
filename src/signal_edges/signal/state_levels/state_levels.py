"""The state levels mixin, :class:`.StateLevelsMixin`, can be added to :class:`.Signal` to obtain the levels for
the logical states of a signal using different modes, :class:`~.state_levels.definitions.Mode`, based on histograms.
The resulting values for the state levels are returned as :class:`.StateLevels`.

.. note::

    This implementation mimics `Mathworks statelevels <https://mathworks.com/help/signal/ref/statelevels.html>`_
    or `Octave statelevels <https://octave.sourceforge.io/signal/function/statelevels.html>`_, these links provide
    more information about the inner details.

The code snippet below shows how to add this functionality to a signal:

.. code-block:: python

    import signal_edges.signal as ses

    class ExampleSignal(ses.state_levels.StateLevelsMixin, ses.Signal):
        pass

An example of its usage using :class:`.VoltageSignal` is described below:

.. code-block:: python

    import numpy as np
    import signal_edges.signal as ses

    # Create timestamps for the signal.
    signal_timestamps = np.linspace(start=0, stop=160, num=160, endpoint=False)
    # Create voltages for the signal, and add some noise to them.
    signal_voltages = np.asarray([0, 0, 0, 0, 5, 5, 5, 5, 5, 5] * (160 // 10)) + \\
                      np.random.normal(0, 0.1, 160)
    # Create signal.
    signal = ses.VoltageSignal(signal_timestamps, signal_voltages, "s", "V")
    # Obtain state levels.
    (state_levels, histogram) = signal.state_levels()
    
    # Plot state levels and histogram.
    signal.state_levels_plot("signal.png", state_levels, histogram=histogram)

This code snippet generates the following plot:

.. figure:: ../../.assets/img/004_example_state_levels.png
    :width: 600
    :align: center
    
    The generated signal with the state levels calculated and the histogram."""

try:
    from typing import Literal, Self
except ImportError:
    from typing_extensions import Self, Literal

import logging
from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

from ... import plotter as sep
from ...exceptions import StateLevelsError
from .definitions import Mode, StateLevels


class StateLevelsMixin:
    """State levels mixin :class:`.Signal` that implements calculation of state levels based on histograms."""

    ## Private API #####################################################################################################
    def __init__(self, *args, **kwargs) -> None:
        """Class constructor."""
        super().__init__(*args, **kwargs)

        # Relevant members of Signal class, make them available here for type checks and the like.
        self._logger: logging.Logger
        self._hv: npt.NDArray[np.float_]
        self._vv: npt.NDArray[np.float_]
        self._hunits: sep.Units
        self._vunits: sep.Units

    ## Protected API ###################################################################################################

    ## Public API ######################################################################################################
    def state_levels(
        self,
        mode: Mode = Mode.HISTOGRAM_MODE,
        nbins: int = 100,
        bounds: tuple[float, float] | None = None,
        high_ref: float = 90.0,
        high_runt_ref: float = 70.0,
        intermediate_ref: float = 50.0,
        low_runt_ref: float = 30.0,
        low_ref: float = 10.0,
    ) -> tuple[StateLevels, tuple[npt.NDArray[np.float_], npt.NDArray[np.float_]]]:
        """Finds the state levels of a signal using histograms.

        :param mode: The histogram mode used to calculate the state levels.
        :param nbins: Number of bins to use in the histogram.
        :param bounds: The lower and upper bounds of the signal, defaults to minimum and maximum peak values.
        :param high_ref: A percentage reference value of the full range for the ``high`` level.
        :param high_runt_ref: A percentage reference value of the full range for the ``low runt`` level.
        :param intermediate_ref: A percentage reference value of the full range for the ``intermediate`` level.
        :param low_runt_ref: A percentage reference value of the full range for the ``low runt`` level.
        :param low_ref: A percentage reference value of the full range for the ``low`` level.
        :raise StateLevelsError: The reference values must be in the range `0 <= x <= 100`.
        :raise StateLevelsError: The reference values must satisfy
            `low_ref < low_runt_ref < intermediate_ref < high_runt_ref < high_ref`.
        :raise StateLevelsError: The bounds provided must satisfy `bounds[0] <= bounds[1]`.
        :raise StateLevelsError: The minimum number of bins is two.
        :return: The state levels and the values for the horizontal and vertical axes of the histogram."""
        # pylint: disable=too-many-arguments,too-many-locals

        # Verify the levels are in the range 0 to 100.
        if not all(0 <= i <= 100 for i in (high_ref, high_runt_ref, intermediate_ref, low_runt_ref, low_ref)):
            raise StateLevelsError("Reference values must be in the range 0 <= ref <= 100.")
        # Verify the levels are ordered properly.
        if not low_ref < low_runt_ref < intermediate_ref < high_runt_ref < high_ref:
            raise StateLevelsError("Reference values must satisfy low < low_runt < intermediate < high_runt < high.")
        # If the bounds were provided, ensure they are consistent.
        if bounds is not None and bounds[1] < bounds[0]:
            raise StateLevelsError("Bounds when user provided must satisfy upper bound < lower bound.")
        # Verify the number of bins.
        if nbins <= 1:
            raise StateLevelsError("The number of bins when user provided must be greater than one.")

        # Obtain the maximum and minimum amplitudes, either user provided or from the data.
        if bounds is not None:
            lower_bound = bounds[0]
            upper_bound = bounds[1]
        else:
            lower_bound = np.subtract(np.min(self._vv), np.finfo(np.float_).eps)
            upper_bound = np.add(np.max(self._vv), np.finfo(np.float_).eps)

        # Compute histogram.
        hist_x = lower_bound + (np.arange(1, nbins + 1) - 0.5) * (upper_bound - lower_bound) / nbins
        (hist_y, _) = np.histogram(self._vv, nbins, (lower_bound, upper_bound))

        # Get the lowest-indexed histogram bin with non-zero count.
        idx_lowest = np.where(hist_y > 0)[0][0] + 1
        # Get the highest-indexed histogram bin with non-zero count.
        idx_highest = np.where(hist_y > 0)[0][-1] + 1

        idx_low_low = idx_lowest
        idx_low_high = idx_lowest + np.int_(np.floor((idx_highest - idx_lowest) / 2))
        idx_upper_low = idx_low_high
        idx_upper_high = idx_highest

        # Calculate lower histogram.
        low_hist = hist_y[idx_low_low - 1 : idx_low_high]
        # Calculate upper histogram.
        upper_hist = hist_y[idx_upper_low - 1 : idx_upper_high]

        # Calculate amplitude to ratio.
        amp_ratio = (upper_bound - lower_bound) / len(hist_y)

        # Calculate low and high values, using the mode specified.
        if mode is Mode.HISTOGRAM_MODE:
            idx_max = np.add(np.argmax(low_hist), 1)
            idx_min = np.add(np.argmax(upper_hist), 1)
            lowest_value = lower_bound + amp_ratio * (idx_low_low + idx_max - 1.5)
            highest_value = lower_bound + amp_ratio * (idx_upper_low + idx_min - 1.5)
        else:
            lowest_value = lower_bound + amp_ratio * np.dot(
                np.arange(idx_low_low, idx_low_high + 1) - 0.5, low_hist
            ) / np.sum(low_hist)
            highest_value = lower_bound + amp_ratio * np.dot(
                np.arange(idx_upper_low, idx_upper_high + 1) - 0.5, upper_hist
            ) / np.sum(upper_hist)

        # Calculate full range, and from it, the remaining values based on the percentages.
        full_range = np.abs(highest_value - lowest_value)
        high_value = lowest_value + (high_ref / 100) * full_range
        high_runt_value = lowest_value + (high_runt_ref / 100) * full_range
        intermediate_value = lowest_value + (intermediate_ref / 100) * full_range
        low_runt_value = lowest_value + (low_runt_ref / 100) * full_range
        low_value = lowest_value + (low_ref / 100) * full_range

        return (
            StateLevels(
                highest=highest_value,
                high=high_value,
                high_runt=high_runt_value,
                intermediate=intermediate_value,
                low_runt=low_runt_value,
                low=low_value,
                lowest=lowest_value,
            ),
            (hist_x, hist_y),
        )

    def state_levels_to_array(
        self,
        levels: StateLevels,
        array_id: Literal["highest", "high", "high_runt", "intermediate", "low_runt", "low", "lowest"],
    ) -> tuple[npt.NDArray[np.float_], npt.NDArray[np.float_]]:
        """Convert the specified level from the state levels provided to an array of the same length as the number
        of values in the signal.

        :param levels: State levels with the values to convert to arrays.
        :param array_id: The array identifier used to identify the state level to convert.
        :raise StateLevelsError: The array identifier provided is not valid.
        :return: The values of the horizontal axis and the values on the vertical axis for the level specified."""
        # pylint: disable=too-many-return-statements

        if array_id == "highest":
            return (np.copy(self._hv), np.full_like(self._vv, levels.highest))
        if array_id == "high":
            return (np.copy(self._hv), np.full_like(self._vv, levels.high))
        if array_id == "high_runt":
            return (np.copy(self._hv), np.full_like(self._vv, levels.high_runt))
        if array_id == "intermediate":
            return (np.copy(self._hv), np.full_like(self._vv, levels.intermediate))
        if array_id == "low_runt":
            return (np.copy(self._hv), np.full_like(self._vv, levels.low_runt))
        if array_id == "low":
            return (np.copy(self._hv), np.full_like(self._vv, levels.low))
        if array_id == "lowest":
            return (np.copy(self._hv), np.full_like(self._vv, levels.lowest))

        raise StateLevelsError(f"State level array identifier '{array_id}' is invalid.")

    def state_levels_plot(
        self,
        path: str,
        state_levels: StateLevels,
        *args,
        begin: float | None = None,
        end: float | None = None,
        munits: float = 0,
        levels: Sequence[Literal["highest", "high", "high_runt", "intermediate", "low_runt", "low", "lowest"]] = (),
        histogram: tuple[npt.NDArray[np.float_], npt.NDArray[np.float_]] | None = None,
        **kwargs,
    ) -> Self:
        """Performs a plot of the signal with the specified levels and optionally the histogram.

        :param path: The path where to store the plot, see :meth:`.Plotter.plot`.
        :param state_levels: The state levels to plot.
        :param args: Additional arguments to pass to the plotting function, see :meth:`.Plotter.plot`.
        :param begin: The begin value of the horizontal axis where the plot starts, see :meth:`.Plotter.plot`.
        :param end: The end value of the horizontal axis where the plot ends, see :meth:`.Plotter.plot`.
        :param munits: Margin units for the plot, see :meth:`.Plotter.plot`.
        :param levels: The levels to plot, defaults to all levels.
        :param histogram: The horizontal and vertical axes values of the histogram, defaults to no histogram.
        :param kwargs: Additional keyword arguments to pass to the plotting function, see :meth:`.Plotter.plot`.
        :return: Instance of the class."""
        # pylint: disable=too-many-locals

        # Create plotter.
        plotter = sep.Plotter(sep.Mode.LINEAR, rows=2 if histogram is not None else 1, columns=1)

        # Adjust begin and end values if not provided.
        begin = begin if begin is not None else float(self._hv[0])
        end = end if end is not None else float(self._hv[-1])

        # Create plot for the signal.
        spl = sep.Subplot("Signal", self._hv, self._hunits, self._vv, self._vunits, begin, end, munits, "red")
        plotter.add_plot(0, 0, spl)

        # Add 'highest' state level.
        for level in ("highest", "high", "high_runt", "intermediate", "low_runt", "low", "lowest"):
            levels_dict = {
                "highest": "Highest State Level",
                "high": "High State Level",
                "high_runt": "High State Level (Runt)",
                "intermediate": "Intermediate State Level",
                "low_runt": "Low State Level (Runt)",
                "low": "Low State Level",
                "lowest": "Lowest State Level",
            }

            if len(levels) == 0 or level in levels:
                (level_x, level_y) = self.state_levels_to_array(state_levels, level)
                subplot = sep.Subplot(
                    levels_dict[level],
                    level_x,
                    self._hunits,
                    level_y,
                    self._vunits,
                    begin,
                    end,
                    munits,
                    "#7F7F7F",
                    linestyle="dotted",
                    marker="none",
                )
                plotter.add_plot(0, 0, subplot)

        # Plot histogram if provided.
        if histogram is not None:
            (hist_x, hist_y) = histogram
            spl = sep.Subplot(
                "Histogram",
                hist_x,
                self._vunits,
                hist_y,
                sep.Units("N/A", "N/A", "Frequency"),
                hist_x[0],
                hist_x[-1],
                0,
                "red",
                linestyle="dotted",
            )
            plotter.add_plot(1, 0, spl)

        # Create plot.
        plotter.plot(path, *args, **kwargs)

        return self
