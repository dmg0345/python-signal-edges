"""Definitions for signal edges."""

from enum import IntEnum, auto
from typing import TypedDict

import numpy as np
import numpy.typing as npt

from ..signal import Signal
from ..state_levels import StateLevelsMixin


class IntPointPolicy(IntEnum):
    """Policies that dictate how to calculate the intermediate point of edges.

    By default, the intermediate point of any edge, both normal or runt edge, is the point within the edge
    the nearest to the intermediate value in the :class:`.StateLevels` provided by the user.

    This behaviour can be modified by using intermediate point policies."""

    #: Use the data point in the edge, including ``begin`` and ``end``, that is nearest to the intermediate level.
    POLICY_0 = auto()
    #: Force use of ``begin`` for falling edges and ``end`` for rising edges.
    POLICY_1 = auto()
    #: Force use of ``end`` for falling edges and ``begin`` for rising edges.
    POLICY_2 = auto()


class Type(IntEnum):
    """Type of an edge.

    The :class:`.StateLevels` provided for calculation of edges define the following logical areas for edges:

        - The `high area`, ``high_a``, for values that satisfy `value > high`.
        - The `intermediate high area`, ``int_high_a``, for values that satisfy `intermediate < value <= high`.
        - The `intermediate low area`, ``int_low_a``, for values that satisfy `low < value <= intermediate`.
        - The `low area`, ``low_a``, for values that satisfy `value < low`.
        - The `runt low area`, ``runt_low_a``, for values that satisfy `low <= value <= high_runt`.
        - The `runt high area`, ``runt_high_a``, for values that satisfy `runt_low <= value <= high`.

    The runt areas and the intermediate areas overlap between each other, and the high and low areas do
    not overlap with any other area. The type of an edge is defined by how it transitions between these
    areas.

    Runt edges can only be found in pairs, since until a ``high`` or ``low`` logical level has been reached
    it is not possible to determine whether edges are truly runt edges or normal edges."""

    #: A normal falling edge, from ``high_a`` to ``low_a``.
    FALLING = auto()
    #: A runt falling edge, from ``high_a`` to ``runt_low_a`` or from ``runt_high_a`` to ``low_a``.
    FALLING_RUNT = auto()
    #: A normal rising edge, from ``low_a`` to ``high_a``.
    RISING = auto()
    #: A runt rising edge, from ``low_a`` to ``runt_high_a`` or from ``runt_low_a`` to ``high_a``.
    RISING_RUNT = auto()


class Edge(TypedDict):
    """Definition of an edge in a signal.

    :param edge_type: The type of edge.
    :param ibegin: Index of the beginning of the edge in the signal.
    :param hbegin: Value of the horizontal axis of the signal at the beginning of the edge.
    :param vbegin: Value of the vertical axis of the signal at the beginning of the edge.
    :param iintermediate: Index of the intermediate point of the edge in the signal.
    :param hintermediate: Value of the horizontal axis of the signal at the intermediate of the edge.
    :param vintermediate: Value of the vertical axis of the signal at the intermediate of the edge.
    :param iend: Index of the end of the edge in the signal.
    :param hend: Value of the horizontal axis of the signal at the end of the edge.
    :param vend: Value of the vertical axis of the signal at the end of the edge."""

    # pylint: disable=too-few-public-methods

    edge_type: Type
    ibegin: int
    hbegin: float
    vbegin: float
    iintermediate: int
    hintermediate: float
    vintermediate: float
    iend: int
    hend: float
    vend: float


class AreaSignal(StateLevelsMixin, Signal):
    """Definition of a signal used to calculate state levels in a delimited area of the original signal."""

    ## Private API #####################################################################################################

    ## Protected API ###################################################################################################

    ## Public API ######################################################################################################
    def load(self, hvalues: npt.NDArray[np.float_], vvalues: npt.NDArray[np.float_]) -> "AreaSignal":
        """Loads the values specified into the signal.

        :param hvalues: The values for the horizontal axis.
        :param vvalues: The values for the vertical axis.
        :return: Instance of the class."""
        self._hv = hvalues
        self._vv = vvalues

        return self
