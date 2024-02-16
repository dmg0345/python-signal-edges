"""Definitions for the opinionated plotter."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import TypeAlias

import numpy as np
import numpy.typing as npt


class Mode(IntEnum):
    """Plotter mode provides some customization options between plots."""

    #: Linear plotter with independent vertical axis and horizontal axis in each plot.
    LINEAR = auto()
    #: Linear plotter with shared horizontal axis for all subplots, a single column is required.
    SHARED_H_AXIS = auto()


@dataclass
class Units:
    """Units provide a name, a symbol and magnitude for display.

    :param name: The name of the units, for example, ``seconds`` for seconds.
    :param symbol: The symbol for the units, for example, ``s`` for seconds.
    :param magnitude: The magnitude the units measure, for example, ``Time`` for seconds."""

    name: str
    symbol: str
    magnitude: str


@dataclass
class Subplot:
    """Definition of a subplot within a plot.

    :param name: Name of the subplot, must be unique within the plot.
    :param hvalues: `1xN` array with values for the horizontal axis, they must satisfy the requirement `x[n] < x[n+1]`.
    :param hunits: The units for the horizontal axis.
    :param vvalues: `1xN` array with the values for the vertical axis.
    :param vunits: The units for the vertical axis.
    :param begin: The value on the horizontal axis where the plotting starts.
    :param end: The value on the vertical axis where the plotting ends.
    :param munits: The margin units to both sides of the plot, a margin unit equals ``begin`` - ``end``.
    :param color: A matplotlib RGB/RGBA string or named color, such as ``#FFFFFF80`` or ``black``.
    :param linestyle: A matplotlib named linestyle value, such as ``solid`` or ``dashed``.
    :param marker: A matplotlib named marker value, such as ``none`` or ``o``."""

    # pylint: disable=too-many-instance-attributes

    name: str
    hvalues: npt.NDArray[np.float_]
    hunits: Units
    vvalues: npt.NDArray[np.float_]
    vunits: Units
    begin: float
    end: float
    munits: float = 0.0
    color: str = "red"
    linestyle: str = "solid"
    marker: str = "o"


#: Type alias for a plot, a collection of subplots.
Plot: TypeAlias = list[Subplot]
#: Type alias for the plot area, accessed as ``x[row_i][column_i][plot_id]``.
PlotArea: TypeAlias = dict[int, dict[int, Plot]]


@dataclass
class Cursor:
    """A vertical line that marks values of interest in one or more subplots within a plot.

    :param name: Name of the cursor for display, it is recommended to use a single character.
    :param hindex: The index of the horizontal value of the first subplot in the plot for the cursor.
    :param row: The row index of the plot.
    :param column: The column index of the plot.
    :param subplot_ids: Identifiers of the subplots for which the cursor should fetch vertical axis values.
    :param hvdec: Number of decimals for the value on the horizontal axis on display.
    :param vvdec: Number of decimals for values on the vertical axis of relevant subplots on display.
    :param color: A matplotlib RGB/RGBA string or named color, such as ``#FFFFFF80`` or ``black``.
    :param linestyle: A matplotlib named linestyle value, such as ``solid`` or ``dashed``."""

    # pylint: disable=too-many-instance-attributes

    name: str
    hindex: int
    row: int
    column: int
    subplot_ids: Sequence[str]
    hvdec: int = 3
    vvdec: int = 3
    color: str = "#E0E0E080"
    linestyle: str = "dashed"
