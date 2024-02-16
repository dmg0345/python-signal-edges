"""The signal class, :class:`.Signal`, is the base class from which specialized signals can be created and to which
mixins with additional functionality can be added, the current available mixins are the following:

    - `Filter mixins`, :class:`.BesselFiltersMixin`, :class:`.ButterworthFiltersMixin`, :class:`.EllipticFiltersMixin`,
      to filter the signal by different methods also providing the possibility to implement your own filters via the
      :class:`.FiltersMixin` base class.
    - `State levels mixin`, :class:`.StateLevelsMixin`, to calculate the logical state levels of the signal.
    - `Edges mixin`, :class:`.EdgesMixin`, to obtain the edges of the signal.

A detailed example of an specialized signal that ships with the package is the voltage signal, :class:`.VoltageSignal`,
its implementation can be checked for details on how to use the base signal class. 

An example of its usage is shown in the following code snippet:

.. code-block:: python

    import numpy as np
    import signal_edges.signal as ses
    
    # Create timestamps in seconds for the signal, the horizontal axis.
    signal_timestamps = np.linspace(start=0, stop=160, num=160, endpoint=False)
    # Create voltages in seconds for the signal, the vertical axis.
    signal_voltages = np.asarray([0, 0, 0, 0, 5, 5, 5, 5, 5, 5] * (160 // 10))
    # Create signal with the previous values, and seconds and volts as units.
    signal = ses.VoltageSignal(signal_timestamps, signal_voltages, "s", "V")

    # Plot signal to file.
    signal.signal_plot("signal.png")

Which creates the following signal:

.. figure:: ../.assets/img/000_example_signal.png
    :width: 600
    :align: center
    
    The generated signal in the code snippet."""

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

import logging
from abc import ABC

import numpy as np
import numpy.typing as npt

from .. import plotter as sep
from ..definitions import get_logger
from ..exceptions import SignalError


class Signal(ABC):
    """Base class for signal, meant to be derived to create specialized signals on which to add mixins from this
    package with additional functionality.

    A signal consists in two `1xN` arrays, where `N` is the number of values, one with the values for the
    horizontal axis and another one with the values for the vertical axis. The number of values in each array must be
    the same, and additionally the values of the horizontal axis must satisfy the requirement `x[n] < x[n+1]` for
    all their values.

    .. note::

        For simplicity, the Numpy arrays provided to this class are copied internally, changes outside this classs
        to the arrays provided will not reflect on the internal ones, use the relevant getters and setters to reflect
        this changes on the internal arrays."""

    # pylint: disable=too-few-public-methods

    ## Private API #####################################################################################################
    def __init__(
        self,
        hvalues: npt.NDArray[np.float_],
        vvalues: npt.NDArray[np.float_],
        *args,
        hunits: sep.Units | None = None,
        vunits: sep.Units | None = None,
        **kwargs,
    ) -> None:
        """The constructor for the signal class.

        :meta public:
        :param hvalues: A `1xN` array with the values of the horizontal axis to copy for the signal.
        :param vvalues: A `1xN` array with the values of the vertical axis to copy for the signal.
        :param hunits: The units of the values of the horizontal axis for plots, defaults to no units.
        :param vunits: The units of the values of the vertical axis for plots, defaults to no units."""
        # pylint: disable=unused-argument

        #: Logger.
        self.__logger = get_logger()
        #: Values of the horizontal axis for the signal, must satisfy ``x[n] < x[n+1]``.
        self.__hv = np.array(hvalues, dtype=np.float_, copy=True, order="C")
        #: Values of the vertical axis for the signal.
        self.__vv = np.array(vvalues, dtype=np.float_, copy=True, order="C")
        #: Units for the values on the horizontal axis.
        self.__hunits = hunits if hunits is not None else sep.Units("N/A", "N/A", "N/A")
        #: Units for the values on the vertical axis.
        self.__vunits = vunits if vunits is not None else sep.Units("N/A", "N/A", "N/A")
        # Validate values after initialization finished.
        self._validate_values()

    ## Protected API ###################################################################################################
    @property
    def _logger(self) -> logging.Logger:
        """Getter for the logger for the signal, use this from the derived class to print information to the logger
        of the package. For information on how to configure the package logger refer to :func:`.get_logger`.

        :meta public:
        :return: The logger."""
        return self.__logger

    @property
    def _hv(self) -> npt.NDArray[np.float_]:
        """Getter for the values of the horizontal axis.

        :meta public:
        :return: A `1xN` array with the values of the horizontal axis."""
        return self.__hv

    @_hv.setter
    def _hv(self, new_hv: npt.NDArray[np.float_]) -> None:
        """Setter for the values of the horizontal axis.

        .. note::

            When setting the values directly, :meth:`.Signal._validate_values` can be used to validate them.

        :meta public:
        :param new_hv: A `1xN` array with the new values of the horizontal axis."""
        self.__hv = new_hv

    @property
    def _vv(self) -> npt.NDArray[np.float_]:
        """Getter for the values of the vertical axis.

        :meta public:
        :return: A `1xN` array with the values of the vertical axis."""
        return self.__vv

    @_vv.setter
    def _vv(self, new_vv: npt.NDArray[np.float_]) -> None:
        """Setter for the values of the vertical axis.

        .. note::

            When setting the values directly, :meth:`.Signal._validate_values` can be used to validate them.

        :meta public:
        :param new_vv: A `1xN` array with the new values of the vertical axis."""
        self.__vv = new_vv

    @property
    def _hunits(self) -> sep.Units:
        """Getter for the units of the values of the horizontal axis.

        :meta public:
        :return: The units."""
        return self.__hunits

    @_hunits.setter
    def _hunits(self, new_hunits: sep.Units) -> None:
        """Setter for the units of the values of the horizontal axis.

        :meta public:
        :param new_hunits: The new units for the values of the horizontal axis."""
        self.__hunits = new_hunits

    @property
    def _vunits(self) -> sep.Units:
        """Getter for the units of the values of the vertical axis.

        :meta public:
        :return: The units."""
        return self.__vunits

    @_vunits.setter
    def _vunits(self, new_vunits: sep.Units) -> None:
        """Setter for the units of the values of the vertical axis.

        :meta public:
        :param new_vunits: The new units for the values of the vertical axis."""
        self.__vunits = new_vunits

    def _validate_values(self) -> "Signal":
        """Validates the values of the horizontal axis and the vertical axis.

        :raise SignalError: The horizontal or vertical axes values provided are not on the form `1xN`.
        :raise SignalError: The number of horizontal or vertical axis values is zero.
        :raise SignalError: The number of horizontal and vertical axis values is not the same.
        :raise SignalError: The horizontal axis values do not satisfy the `x[n] < x[n+1]` requirement.
        :return: Instance of the class."""
        # Check that the arrays are of the form 1xN.
        if any([len(self.__hv.shape) != 1, len(self.__vv.shape) != 1]):
            raise SignalError("The values of the horizontal or vertical axis are not of the form 1xN.")
        # Ensure both axis have at least one value.
        if any([len(self.__hv) == 0, len(self.__vv) == 0]):
            raise SignalError("The number of values in the horizontal or vertical axis can't be zero.")
        # Ensure both axis have the same number of values.
        if len(self.__hv) != len(self.__vv):
            raise SignalError("The number of values of the horizontal and vertical axis must be the same.")
        # Ensure the values of the horizontal axis satisfy the x[n] < x[n+1] requirement.
        if len(np.where(np.diff(self.__hv) <= 0)[0]) > 0:
            raise SignalError("The horizontal axis values given do not satisfy the x[n] < x[n+1] requirement.")

        return self

    ## Public API ######################################################################################################
    def signal_plot(
        self,
        path: str,
        *args,
        begin: float | None = None,
        end: float | None = None,
        munits: float = 0,
        **kwargs,
    ) -> Self:
        """Performs a plot of the signal.

        :param path: The path where to store the plot, see :meth:`.Plotter.plot`.
        :param args: Additional arguments to pass to the plotting function, see :meth:`.Plotter.plot`.
        :param begin: The begin value of the horizontal axis where the plot starts, see :meth:`.Plotter.plot`.
        :param end: The end value of the horizontal axis where the plot ends, see :meth:`.Plotter.plot`.
        :param munits: Margin units for the plot, see :meth:`.Plotter.plot`.
        :param kwargs: Additional keyword arguments to pass to the plotting function, see :meth:`.Plotter.plot`.
        :return: Instance of the class."""
        # pylint: disable=too-many-locals

        # Create plotter.
        plotter = sep.Plotter(sep.Mode.LINEAR, rows=1, columns=1)

        # Adjust begin and end values if not provided.
        begin = begin if begin is not None else float(self._hv[0])
        end = end if end is not None else float(self._hv[-1])

        # Create plot for the signal.
        spl = sep.Subplot("Signal", self._hv, self._hunits, self._vv, self._vunits, begin, end, munits, "red")
        plotter.add_plot(0, 0, spl)

        # Create plot.
        plotter.plot(path, *args, **kwargs)

        return self
