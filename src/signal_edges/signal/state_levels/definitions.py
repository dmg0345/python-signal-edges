"""Definitions for signal state levels."""

from dataclasses import dataclass
from enum import IntEnum, auto


class Mode(IntEnum):
    """Mode that defines the algorithm to calculate the state levels."""

    #: Histograms with mode values.
    HISTOGRAM_MODE = auto()
    #: Histograms with mean values.
    HISTOGRAM_MEAN = auto()


@dataclass
class StateLevels:
    """Definition of the state levels of the signal, in the same units as the units of the values of the vertical
    axis of the signal from which they were calculated, refer to :meth:`~.StateLevelsMixin.state_levels` for details.

    The values satisfy `lowest < low < low_runt < intermediate < high_runt < high < highest`.

    The full range in this context refers to `highest - lowest`.

    :param highest: Highest level, equal to `100%` of the full range.
    :param high: High level, maps to ``high_ref`` percentage value.
    :param high_runt: High runt level, maps to ``high_runt_ref`` percentage value.
    :param intermediate: Intermediate level, maps to ``intermediate_ref`` percentage value.
    :param low_runt: Low runt level, maps to ``low_runt_ref`` percentage value.
    :param low: Low level, maps to ``low_ref`` percentage value.
    :param lowest: Lowest level, equal to `0%` of the full range."""

    highest: float
    high: float
    high_runt: float
    intermediate: float
    low_runt: float
    low: float
    lowest: float
