"""Filters are implemented from a base mixin class, :class:`.FiltersMixin`, some examples of the currently implemented
filters are the Bessel filters, :class:`.BesselFiltersMixin`, Butterworth filters, :class:`.ButterworthFiltersMixin` and
elliptic filters, :class:`.EllipticFiltersMixin`."""

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

import logging
from abc import ABC

import numpy as np
import numpy.typing as npt

from ... import plotter as sep


class FiltersMixin(ABC):
    """Base class for filter mixins for :class:Signal derived classes."""

    # pylint: disable=too-few-public-methods

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
    def filters_plot(
        self,
        path: str,
        signal: Self,
        *args,
        begin: float | None = None,
        end: float | None = None,
        munits: float = 0,
        **kwargs,
    ) -> Self:
        """Performs a plot of the original signal and the provided filtered signal.

        :param path: The path where to store the plot, see :meth:`.Plotter.plot`.
        :param signal: The filtered signal.
        :param args: Additional arguments to pass to the plotting function, see :meth:`.Plotter.plot`.
        :param begin: The begin value of the horizontal axis where the plot starts, see :meth:`.Plotter.plot`
        :param end: The end value of the horizontal axis where the plot end, see :meth:`.Plotter.plot`.
        :param munits: Margin units for the plot, see :meth:`.Plotter.plot`
        :param kwargs: Additional keyword arguments to pass to the plotting function, see :meth:`.Plotter.plot`.
        :return: Instance of the class."""
        # Create plotter.
        plotter = sep.Plotter(sep.Mode.LINEAR, rows=1, columns=1)

        # Adjust begin and end values if not provided.
        begin = begin if begin is not None else float(self._hv[0])
        end = end if end is not None else float(self._hv[-1])

        # Add subplot for the original signal.
        plotter.add_plot(
            0,
            0,
            sep.Subplot(
                "Original",
                self._hv,
                self._hunits,
                self._vv,
                self._vunits,
                begin,
                end,
                munits,
                "red",
            ),
        ).add_plot(
            0,
            0,
            sep.Subplot(
                "Filtered",
                getattr(signal, "_hv"),
                getattr(signal, "_hunits"),
                getattr(signal, "_vv"),
                getattr(signal, "_vunits"),
                begin,
                end,
                munits,
                "blue",
            ),
        ).plot(
            path, *args, **kwargs
        )

        return self
