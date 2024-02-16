"""The edges mixin, :class:`.EdgesMixin`, can be added to :class:`.Signal` to obtain different types,
:class:`~.edges.definitions.Type`, of edges of a signal. Each of the resulting edges are returned as a :class:`.Edge`.

To configure how to calculate the intermediate point of the edge, refer to :class:`.IntPointPolicy`.

The edges mixin requires the :class:`.StateLevelsMixin` to also be added to the signal, the code snippet below shows
how to add the edges functionality to a signal:

.. code-block:: python

    import signal_edges.signal as ses

    class ExampleSignal(ses.state_levels.StateLevelsMixin, ses.edges.EdgesMixin, ses.Signal):
        pass

An example of its usage using :class:`.VoltageSignal` is described below:

.. code-block:: python

    import numpy as np
    import signal_edges.signal as ses

    # Create timestamps for the signal.
    signal_timestamps = np.linspace(start=0, stop=112, num=112, endpoint=False)
    # Create voltages for the signal, and add some noise to them.
    pattern = [0, 0, 1.5, 2.5, 3.5, 5, 5, 5, 5, 3.5, 2.5, 1.5, 0, 0]
    signal_voltages = np.asarray(pattern * (112 // len(pattern))) + \\
                      np.random.normal(0, 0.1, 112)
    # Create signal.
    signal = ses.VoltageSignal(signal_timestamps, signal_voltages, "s", "V")
    # Obtain state levels.
    (state_levels, _) = signal.state_levels()
    # Obtain edges.
    edges = signal.edges(state_levels)
    
    # Plot edges.
    signal.edges_plot("signal.png", edges)

This code snippet generates the following plot:

.. figure:: ../../.assets/img/005_example_edges.png
    :width: 600
    :align: center
    
    The generated signal with the edges begin, intermediate and end points marked."""

try:
    from typing import Literal, Self
except ImportError:
    from typing_extensions import Self, Literal

import logging
from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

from ... import plotter as sep
from ...exceptions import EdgesError
from ..state_levels import StateLevels
from .definitions import AreaSignal, Edge, IntPointPolicy, Type


class EdgesMixin:
    """Edges mixin for :class:`.Signal` derived classes that implements the calculation of edges in a signal.

    .. caution::

        This mixin requires the :class:`.StateLevelsMixin` in the signal derived from :class:`.Signal`."""

    # pylint: disable=too-many-instance-attributes,consider-using-assignment-expr,else-if-used

    # TODO: Decide whether to reduce duplication of code this class, right now it is mostly separated for fallign and
    # rising edges but code can be common to a degree for both and separate comments help understand workflow.

    # pylint: disable=invalid-name

    #: High area identifier.
    __HIGH = 0
    #: Intermediate high area identifier.
    __INT_HIGH = 1
    #: Intermediate low area identifier.
    __INT_LOW = 2
    #: Low area identifier.
    __LOW = 3
    #: Runt high area identifier.
    __RUNT_HIGH = 4
    #: Runt low area identifier.
    __RUNT_LOW = 5

    # pylint: enable=invalid-name

    ## Private API #####################################################################################################
    def __init__(self, *args, **kwargs) -> None:
        """Class constructor."""
        super().__init__(*args, **kwargs)

        #: Area with indices of the values that satisfy `x > high`.
        self.__areas: list[npt.NDArray[np.int_]] = [np.empty(shape=(1, 1), dtype=np.int_) for _ in range(0, 6)]
        #: The state levels.
        self.__state_levels: StateLevels
        #: The intermediate point policy to apply.
        self.__int_policy: IntPointPolicy
        #: Temporary area for state levels in runt edges.
        self.__area_signal: AreaSignal = AreaSignal(hvalues=[1, 2], vvalues=[1, 2])

        # Relevant members of Signal class, make them available here for type checks and the like.
        self._logger: logging.Logger
        self._hv: npt.NDArray[np.float_]
        self._vv: npt.NDArray[np.float_]
        self._hunits: sep.Units
        self._vunits: sep.Units

    def __area_update(self, levels: StateLevels) -> Self:
        """Updates the internal areas from the state levels provided.

        The ``high``, ``int_high``, ``int_low`` and ``low`` areas have all values unique between each other.

        The ``runt_high`` and ``runt_low`` areas share values with the ``int_high`` and ``int_low``.

        The values in each area are unique and sorted in ascending order, which suits well for fast analysis using
        binary search.

        :param levels: The state levels for the signal.
        :raise EdgesError: The state levels do not satisfy `low < low_runt < intermediate < high_runt < high`.
        :return: Instance of the class."""
        # Sanity check on the levels.
        if not levels.low < levels.low_runt < levels.intermediate < levels.high_runt < levels.high:
            raise EdgesError("The state levels do not satisfy low < low_runt < intermediate < high_runt < high.")

        # Get values.
        high = np.float_(levels.high)
        high_runt = np.float_(levels.high_runt)
        intermediate = np.float_(levels.intermediate)
        low_runt = np.float_(levels.low_runt)
        low = np.float_(levels.low)

        # Normal areas.
        self.__areas[self.__HIGH] = np.where(self._vv > high)[0]
        self.__areas[self.__INT_HIGH] = np.where((self._vv <= high) & (self._vv > intermediate))[0]
        self.__areas[self.__INT_LOW] = np.where((self._vv <= intermediate) & (self._vv >= low))[0]
        self.__areas[self.__LOW] = np.where(self._vv < low)[0]

        # Runt areas.
        self.__areas[self.__RUNT_LOW] = np.where((self._vv <= high_runt) & (self._vv >= low))[0]
        self.__areas[self.__RUNT_HIGH] = np.where((self._vv >= low_runt) & (self._vv <= high))[0]

        # Keep track of state levels calculated.
        self.__state_levels = levels

        return self

    def __area_first(self, area_id: int, begin: np.int_, end: np.int_ | None = None) -> np.int_ | None:
        """Obtains the first value in the area specified between the given ``begin`` and ``end`` values.

        :param area_id: The area identifier.
        :param begin: The value to use as reference for the beginning of the search.
        :param end: The value to use as reference for the end of the search, or ``None`` to use no reference.
        :raise EdgesError: The ``begin`` reference value is not in the range `0 <= begin < len(values)`.
        :raise EdgesError: The ``end`` reference value is not in the range `0 <= end < len(values)`.
        :return: A value ``begin <= value < end`` if ``end`` was specified, otherwise `begin <= value`.
        If no value exists for the specified ``begin`` and ``end`` values, then ``None`` is returned."""
        # Ensure the begin value is in the range 0 <= begin < len(values).
        if begin < 0 or begin >= len(self._vv):
            raise EdgesError(f"The begin, {begin}, reference value is not in the range 0 <= begin < len(values).")
        # If an end value was provided, ensure it is in the range 0 <= end < len(values).
        if end is not None and (end < 0 or end >= len(self._vv)):
            raise EdgesError(f"The end, {end}, reference value is not in the range 0 <= end < len(values).")

        # Get relevant area from area identifier, and check if empty.
        area = self.__areas[area_id]
        # Obtain index that satisfies area[bindex-1] < begin <= area[bindex];
        bindex = np.searchsorted(area, begin, "left")
        # If the index is zero or greater, it is the desired value, if it matches the length, then no value exists.
        bvalue = None if bindex >= len(area) else area[bindex]

        # Check if a end value was specified, and delimit the calculated value further.
        if bvalue is not None and end is not None:
            # An end value was provided, if value found is greater or equal than end value the invalidate it.
            bvalue = None if bvalue >= end else bvalue

        return bvalue

    def __area_last(self, area_id: int, end: np.int_, begin: np.int_ | None = None) -> np.int_ | None:
        """Obtains the last value in the area specified between the given ``begin`` and ``end`` values.

        :param area_id: The area identifier.
        :param end: The value to use as reference for the end of the search.
        :param begin: The value to use as reference for the begin of the search, or ``None`` to use no reference.
        :raise EdgesError: The ``end`` reference value is not in the range `0 <= end < len(values)`.
        :raise EdgesError: The ``begin`` reference value is not in the range `0 <= begin < len(values)`.
        :return: A value ``begin <= value < end`` if ``begin`` was specified, otherwise `value < end`.
        If no value exists for the specified ``begin`` and ``end`` values, then ``None`` is returned."""
        # pylint: disable=too-many-locals

        # Ensure the end value is in the range 0 <= end < len(values).
        if end < 0 or end >= len(self._vv):
            raise EdgesError(f"The end, {end}, reference value is not in the range 0 <= end < len(values).")
        # If an begin value was provided, ensure it is in the range 0 <= begin < len(values).
        if begin is not None and (begin < 0 or begin >= len(self._vv)):
            raise EdgesError(f"The begin, {begin}, reference value is not in the range 0 <= begin < len(values).")

        # Get relevant area from area identifier.
        area = self.__areas[area_id]
        # Obtain index that satisfies area[eindex-1] < end <= area[eindex], and fetch the previous index.
        eindex = np.searchsorted(area, end, "left")
        eindex = eindex - 1 if eindex > 0 else eindex
        # If the index is zero or greater, it is the desired value, if it matches the length, then no value exists.
        evalue = None if eindex >= len(area) else area[eindex]

        # Check if a begin value was specified, and double check the value calculated.
        if evalue is not None and begin is not None:
            # A begin value exists, if value found is less than end value the invalidate it.
            evalue = None if evalue < begin else evalue

        return evalue

    def __extract_edge(self, edge_type: Type, begin: np.int_, end: np.int_) -> Edge:
        """Extracts an single edge from its ``begin`` and ``end`` values.

        :param edge_type: The type of edge to extract.
        :param begin: The value for the beginning of the edge.
        :param end: The value for the end of the edge.
        :raise EdgesError: The ``end`` reference value is not in the range `0 <= end < len(values)`.
        :raise EdgesError: The ``begin`` reference value is not in the range `0 <= begin < len(values)`.
        :raise EdgesError: The ``begin`` and end reference values is do not satisfy `begin < end`.
        :return: The extracted edge."""
        # pylint: disable=too-complex,too-many-branches,too-many-statements,too-many-locals

        # Ensure the begin value is in the range 0 <= begin < len(values).
        if begin < 0 or begin >= len(self._vv):
            raise EdgesError(f"The begin, {begin}, reference value is not in the range 0 <= begin < len(values).")
        # Ensure the end value is in the range 0 <= end < len(values).
        if end < 0 or end >= len(self._vv):
            raise EdgesError(f"The end, {end}, reference value is not in the range 0 <= end < len(values).")
        # Ensure the begin occurs before the end.
        if begin >= end:
            raise EdgesError(f"The begin, {begin}, and end, {end}, reference values do not satisfy begin < end.")

        # Handle beginning of the edge, this is common for all edge types.
        ibegin = begin
        hbegin = self._hv[ibegin]
        vbegin = self._vv[ibegin]

        # Handle end of the edge, this is common for all edge types.
        iend = end
        hend = self._hv[iend]
        vend = self._vv[iend]

        # Handle intermediate of the edge, depending on the type of edge and the policies.
        iint = None
        vint = np.float_(self.__state_levels.intermediate)
        vmax = np.float_(self.__state_levels.highest - self.__state_levels.lowest)
        ################################################################################################################
        if edge_type in (Type.FALLING, Type.FALLING_RUNT):
            # Check intermediate point policy for forced values, otherwise proceed with calculation.
            if self.__int_policy in (IntPointPolicy.POLICY_1, IntPointPolicy.POLICY_2):
                iint = ibegin if self.__int_policy is IntPointPolicy.POLICY_1 else iend
            else:
                # Calculate intermediate of the falling edge, which can be one of the following:
                # - The last value in 'int_high' area.
                # - The first value in 'int_low' area after last value of 'int_high'.
                # - The start of the edge.
                # - The end of the edge.

                # Get the last value in 'int_high' using the end of the edge as reference.
                int_high_v = self.__area_last(self.__INT_HIGH, iend, ibegin)

                # Get the first value in 'int_low' from the last value in 'int_high' if it exists.
                if int_high_v is not None:
                    int_low_v = self.__area_first(self.__INT_LOW, int_high_v, iend)
                # If the last value in 'int_high' does not exist, then use start of the edge.
                else:
                    int_low_v = self.__area_first(self.__INT_LOW, ibegin, iend)

                # Calculate distance to the intermediate points from all candidates that exist.
                indices = np.array(
                    (
                        ibegin,
                        iend,
                        0 if int_high_v is None else int_high_v,
                        0 if int_low_v is None else int_low_v,
                    )
                )
                diffs = np.abs(
                    np.array(
                        (
                            self._vv[ibegin] - vint,
                            vint - self._vv[iend],
                            vmax if int_high_v is None else self._vv[int_high_v] - vint,
                            vmax if int_low_v is None else vint - self._vv[int_low_v],
                        )
                    )
                )

                # Take the index of the point that is the nearest to the intermediate level.
                iint = indices[np.argmin(diffs)]
        ################################################################################################################
        else:
            # Check intermediate point policy for forced values, otherwise proceed with calculation.
            if self.__int_policy in (IntPointPolicy.POLICY_1, IntPointPolicy.POLICY_2):
                iint = iend if self.__int_policy is IntPointPolicy.POLICY_1 else ibegin
            else:
                # Calculate intermediate of the rising edge, which can be one of the following:
                # - The last value in 'int_low' area.
                # - The first value in 'int_high' area after last value of 'int_low'.
                # - The start of the edge.
                # - The end of the edge.

                # Get the last value in 'int_low' using the end of the edge as reference.
                int_low_v = self.__area_last(self.__INT_LOW, iend, ibegin)

                # Get the first value in 'int_high' from the last value in 'int_low' if it exists.
                if int_low_v is not None:
                    int_high_v = self.__area_first(self.__INT_HIGH, int_low_v, iend)
                # If the last value in 'int_low' does not exist, then use start of the edge.
                else:
                    int_high_v = self.__area_first(self.__INT_HIGH, ibegin, iend)

                # Calculate distance to the intermediate points from all candidates that exist.
                indices = np.array(
                    (
                        ibegin,
                        iend,
                        0 if int_high_v is None else int_high_v,
                        0 if int_low_v is None else int_low_v,
                    )
                )
                diffs = np.abs(
                    np.array(
                        (
                            vint - self._vv[ibegin],
                            self._vv[iend] - vint,
                            vmax if int_high_v is None else vint - self._vv[int_high_v],
                            vmax if int_low_v is None else self._vv[int_low_v] - vint,
                        )
                    )
                )

                # Take the index of the point that is the nearest to the intermediate level.
                iint = indices[np.argmin(diffs)]

        # Build edge and return it.
        return {
            "edge_type": edge_type,
            "ibegin": int(ibegin),
            "hbegin": float(hbegin),
            "vbegin": float(vbegin),
            "iintermediate": int(iint),
            "hintermediate": float(self._hv[iint]),
            "vintermediate": float(self._vv[iint]),
            "iend": int(iend),
            "hend": float(hend),
            "vend": float(vend),
        }

    def __extract_runt_edges(self, edge_type: Type, begin: np.int_, end: np.int_) -> tuple[Edge, Edge]:
        """Extracts a combination of runt edges from the ``begin`` of the first edge and the ``end`` of the
        last edge.

        :param edge_type: The type of the first edge to extract.
        :param begin: The value for the beginning of the edge.
        :param end: The value for the end of the edge.
        :raise EdgesError: The type of edge to extract must be a runt type of edge.
        :raise EdgesError: The ``end`` reference value is not in the range `0 <= end < len(values)`.
        :raise EdgesError: The ``begin`` reference value is not in the range `0 <= begin < len(values)`.
        :raise EdgesError: The ``begin`` and end reference values is do not satisfy `begin < end`.
        :return: The two runt edges extracted."""
        # Ensure the edge type is a runt edge.
        if edge_type not in (Type.FALLING_RUNT, Type.RISING_RUNT):
            raise EdgesError("The type of edge to extract must be of runt type.")
        # Ensure the begin value is in the range 0 <= begin < len(values).
        if begin < 0 or begin >= len(self._vv):
            raise EdgesError(f"The begin, {begin}, reference value is not in the range 0 <= begin < len(values).")
        # Ensure the end value is in the range 0 <= end < len(values).
        if end < 0 or end >= len(self._vv):
            raise EdgesError(f"The end, {end}, reference value is not in the range 0 <= end < len(values).")
        # Ensure the begin occurs before the end.
        if begin >= end:
            raise EdgesError(f"The begin, {begin}, and end, {end}, reference values do not satisfy begin < end.")

        # Build temporary signal from the portion of the signal with the runt edges, and calculate the state
        # levels for that area. TODO: Allow to get these from outside, for now use defaults.
        hvalues = self._hv[begin : end + 1]
        vvalues = self._vv[begin : end + 1]
        self.__area_signal.load(hvalues, vvalues)
        (state_levels, _) = self.__area_signal.state_levels()
        edges: list[Edge] = []

        if edge_type is Type.FALLING_RUNT:
            # Extract 'low' area of the area signal.
            low_area = np.where(vvalues < np.float_(state_levels.low))[0]

            # Calculate end of the falling edge as the first point, not 'begin', in the 'low' area.
            edge_begin = begin
            edge_end = begin + low_area[0] if low_area[0] > 0 else begin + low_area[1]
            edges.append(self.__extract_edge(Type.FALLING_RUNT, edge_begin, edge_end))

            # Calculate begin of the rising edge as the last point, not 'end', in the 'low' area.
            edge_begin = begin + low_area[-1] if low_area[-1] < (len(vvalues) - 1) else begin + low_area[-2]
            edge_end = end
            edges.append(self.__extract_edge(Type.RISING_RUNT, edge_begin, edge_end))
        else:
            # Extract 'high' area of the area signal.
            high_area = np.where(vvalues > np.float_(state_levels.high))[0]

            # Calculate end of the rising edge as the first point, not 'begin', in the 'high' area.
            edge_begin = begin
            edge_end = begin + high_area[0] if high_area[0] > 0 else begin + high_area[1]
            edges.append(self.__extract_edge(Type.RISING_RUNT, edge_begin, edge_end))

            # Calculate begin of the falling edge as the last point, not 'end', in the 'high' area.
            edge_begin = begin + high_area[-1] if high_area[-1] < (len(vvalues) - 1) else begin + high_area[-2]
            edge_end = end
            edges.append(self.__extract_edge(Type.FALLING_RUNT, edge_begin, edge_end))

        return (edges[0], edges[1])

    ## Protected API ###################################################################################################

    ## Public API ######################################################################################################
    def edges(self, levels: StateLevels, int_policy: IntPointPolicy = IntPointPolicy.POLICY_0) -> tuple[Edge, ...]:
        """Extracts the edges in the signal from the state levels given.

        :param levels: State levels.
        :param int_policy: The policy to use for intermediate point calculation.
        :raise EdgesError: Invalid state levels.
        :raise EdgesError: Assertion error in the algorithm for the signal provided.
        :return: The edges found in order of appearance in the signal."""
        # pylint: disable=too-complex,too-many-branches,too-many-statements,redefined-variable-type

        # Edges collected.
        edges = []

        # Update thresholds from the state levels provided.
        self.__area_update(levels)
        # Store intermediate point policy.
        self.__int_policy = int_policy

        # Set the initial type of edge to look for based on which logical state the signal enters first.
        high_value = self.__area_first(self.__HIGH, np.int_(0))
        low_value = self.__area_first(self.__LOW, np.int_(0))
        edge_search: Type
        curr_value: np.int_
        # There are both 'low' and 'high' values, check which one occurs first.
        if low_value is not None and high_value is not None:
            if high_value < low_value:
                # A 'high' occurs first, thus we are in 'high' looking for a falling edge.
                curr_value = high_value
                edge_search = Type.FALLING
            else:
                # A 'low' occurs first, thus we are in 'low' looking for a rising edge.
                curr_value = low_value
                edge_search = Type.RISING
        # No 'high' exists, thus we are in 'low' looking for a rising edge.
        elif low_value is not None and high_value is None:
            curr_value = low_value
            edge_search = Type.RISING
        # No 'low' exists, thus we are in 'high' looking for a falling edge.
        elif low_value is None and high_value is not None:
            curr_value = high_value
            edge_search = Type.FALLING
        # No 'low' nor 'high' exists, which implies there are no edges at all in the signal.
        else:
            return tuple(edges)

        # Run indefinitely until an exit condition is reached while searching for edges.
        while True:  # pylint: disable=while-used
            # In the first phase of the edge search, the type of edges to look for is determined, this can be one of:
            # - A rising edge.
            # - A falling edge.
            # - A runt rising edge followed by a runt falling edge.
            # - A runt falling edge followed by a runt rising edge.

            ############################################################################################################
            if edge_search is Type.FALLING:
                # The next edge, if any, is a falling edge and we are currently in 'high', it can be one of:
                # - One falling edge, which transitions from 'high' to 'low'.
                # - Two runt edges, one falling from 'high' to 'runt_low', one rising from 'runt_low' to 'high'.

                # Get the first value in 'low' from the current index.
                low_value = self.__area_first(self.__LOW, curr_value)
                # Get the first value in 'runt_low' from the current index.
                runt_low_value = self.__area_first(self.__RUNT_LOW, curr_value)
                # Get the first value in 'high' after 'runt_low' current index, if it exists.
                high_value = None if runt_low_value is None else self.__area_first(self.__HIGH, runt_low_value)

                # If there is a value in both 'low' and 'runt_low', then 'high' and ordering needs to be checked.
                if low_value is not None and runt_low_value is not None:
                    # If 'low' occurs before 'runt_low' then it is a single edge.
                    if low_value < runt_low_value:
                        edge_search = Type.FALLING
                    # 'runt_low' occurs before 'low', if no 'high' value then it is a single edge.
                    elif high_value is None:
                        edge_search = Type.FALLING
                    # 'runt_low' occurs before 'low', if 'high' occurs before 'low' it is runt edges.
                    elif high_value < low_value:
                        edge_search = Type.FALLING_RUNT
                    # 'runt_low' occurs before 'low', and 'low' occurs before 'high', thus it is a single edge.
                    else:
                        edge_search = Type.FALLING
                # If there is a value in 'low' and no value in 'runt_low' then it is a single edge.
                elif low_value is not None and runt_low_value is None:
                    edge_search = Type.FALLING
                # If there no value in 'low' and there is a value in 'runt_low', 'high' needs to be checked.
                elif low_value is None and runt_low_value is not None:
                    # If there is a value in 'high' it is a pair of runt edges, otherwise it is end of processing.
                    if high_value is not None:
                        edge_search = Type.FALLING_RUNT
                    else:
                        break
                # If there are no values in 'low' or 'runt_low', then it is the end of the processing.
                else:
                    break

                # Extract falling edge.
                if edge_search is Type.FALLING:
                    # Ensure 'low' exists at this point.
                    if low_value is None:
                        raise EdgesError("No 'low' exists for falling edge extraction.")

                    # Find the last value in 'high' before 'low', which will be the begin of the edge.
                    # This value is guaranteed to exist, as the current index is in 'high'.
                    edge_begin_value = self.__area_last(self.__HIGH, low_value, curr_value)
                    if edge_begin_value is None:
                        raise EdgesError("No edge begin obtained for falling edge.")

                    # The end of edge is the calculated 'low'.
                    edge_end_value = low_value

                    # Extract single edge.
                    edges.append(self.__extract_edge(Type.FALLING, edge_begin_value, edge_end_value))

                    # Move current index to the end of the edge, in 'low'.
                    curr_value = edge_end_value
                    # Continue looking for rising edges.
                    edge_search = Type.RISING
                # Extract runt falling edge and runt rising edge.
                else:
                    # Ensure 'runt_low' and 'high' exist at this point.
                    if runt_low_value is None or high_value is None:
                        raise EdgesError("No 'runt_low' or 'high' exists for runt edges extraction.")

                    # Find the last value in 'high' before 'runt_low', which will be the begin of the runt area.
                    # This value is guaranteed to exist, as the current index is in 'high'.
                    edge_begin_value = self.__area_last(self.__HIGH, runt_low_value, curr_value)
                    if edge_begin_value is None:
                        raise EdgesError("No edge begin obtained for runt falling edge before runt rising edge.")
                    # The end of the runt area is 'high'.
                    edge_end_value = high_value

                    # Extract runt edges.
                    edges.extend(self.__extract_runt_edges(Type.FALLING_RUNT, edge_begin_value, edge_end_value))

                    # Move current index to the end of the edge, in 'high'.
                    curr_value = edge_end_value
                    # Continue looking for falling edges.
                    edge_search = Type.FALLING
            ############################################################################################################
            else:
                # The next edge, if any, is a rising edge and we are currently in 'low', it can be one of:
                # - One rising edge, which transitions from 'low' to 'high'.
                # - Two runt edges, one rising from 'low' to 'runt_high', one falling from 'runt_high' to 'low'.

                # Get the first value in 'high' from the current index.
                high_value = self.__area_first(self.__HIGH, curr_value)
                # Get the first value in 'runt_high' from the current index.
                runt_high_value = self.__area_first(self.__RUNT_HIGH, curr_value)
                # Get the first value in 'low' after 'runt_high' current index, if it exists.
                low_value = None if runt_high_value is None else self.__area_first(self.__LOW, runt_high_value)

                # If there is a value in both 'high' and 'runt_high', then 'low' and ordering needs to be checked.
                if high_value is not None and runt_high_value is not None:
                    # If 'high' occurs before 'runt_high' then it is a single edge.
                    if high_value < runt_high_value:
                        edge_search = Type.RISING
                    # 'runt_high' occurs before 'high', if no 'low' value then it is a single edge.
                    elif low_value is None:
                        edge_search = Type.RISING
                    # 'runt_high' occurs before 'high', if 'low' occurs before 'high' it is runt edges.
                    elif low_value < high_value:
                        edge_search = Type.RISING_RUNT
                    # 'runt_high' occurs before 'high', and 'high' occurs before 'low', thus it is a single edge.
                    else:
                        edge_search = Type.RISING
                # If there is a value in 'high' and no value in 'runt_high' then it is a single edge.
                elif high_value is not None and runt_high_value is None:
                    edge_search = Type.RISING
                # If there no value in 'high' and there is a value in 'runt_high', 'low' needs to be checked.
                elif high_value is None and runt_high_value is not None:
                    # If there is a value in 'low' it is a pair of runt edges, otherwise it is end of processing.
                    if low_value is not None:
                        edge_search = Type.RISING_RUNT
                    else:
                        break
                # If there are no values in 'high' or 'runt_high', then it is the end of the processing.
                else:
                    break

                # Extract rising edge.
                if edge_search is Type.RISING:
                    # Ensure 'high' exists at this point.
                    if high_value is None:
                        raise EdgesError("No 'high' exists for rising edge extraction.")

                    # Find the last value in 'low' before 'high', which will be the begin of the edge.
                    # This value is guaranteed to exist, as the current index is in 'low'.
                    edge_begin_value = self.__area_last(self.__LOW, high_value, curr_value)
                    if edge_begin_value is None:
                        raise EdgesError("No edge begin obtained for rising edge.")

                    # The end of edge is the calculated 'high'.
                    edge_end_value = high_value

                    # Extract single edge.
                    edges.append(self.__extract_edge(Type.RISING, edge_begin_value, edge_end_value))

                    # Move current index to the end of the edge, in 'high'.
                    curr_value = edge_end_value
                    # Continue looking for falling edges.
                    edge_search = Type.FALLING
                # Extract runt rising edge and runt falling edge.
                else:
                    # Ensure 'runt_high' and 'low' exist at this point.
                    if runt_high_value is None or low_value is None:
                        raise EdgesError("No 'runt_high' or 'low' exists for runt edges extraction.")

                    # Find the last value in 'low' before 'runt_high', which will be the begin of the edge.
                    # This value is guaranteed to exist, as the current index is in 'low'.
                    edge_begin_value = self.__area_last(self.__LOW, runt_high_value, curr_value)
                    if edge_begin_value is None:
                        raise EdgesError("No edge begin obtained for runt rising edge before runt falling edge.")

                    # The end of the edge is 'low'.
                    edge_end_value = low_value

                    # Extract runt edges.
                    edges.extend(self.__extract_runt_edges(Type.RISING_RUNT, edge_begin_value, edge_end_value))

                    # Move current index to the end of the edge, in 'low'.
                    curr_value = edge_end_value
                    # Continue looking for rising edges.
                    edge_search = Type.RISING

        return tuple(edges)

    def edges_to_array(
        self,
        edges: Sequence[Edge],
        array_id: Literal["begin", "intermediate", "end"],
    ) -> tuple[npt.NDArray[np.float_], npt.NDArray[np.float_]]:
        """Converts values in a sequence of edges to relevant arrays.

        Note that for ``intermediate``, if two edges share the same intermediate point, two times that
        value will be included in the array to keep the length of the arrays consistent.

        :param edges: The sequence of edges.
        :param array_id: The array identifier, which defines the type of values to take.
        :raise EdgesError: The sequence of edges given has no edges.
        :raise EdgesError: The array identifier provided is not valid.
        :return: The values of the horizontal axis and the values of the vertical axis for the sequence of edges."""
        # Ensure the length of the edges passed is not zero.
        if len(edges) == 0:
            raise EdgesError(f"Unable to get array '{array_id}' from empty sequence of edges.")

        # Get relevant indices.
        if array_id == "begin":
            indices = np.asarray([i["ibegin"] for i in edges])
        elif array_id == "intermediate":
            indices = np.asarray([i["iintermediate"] for i in edges])
        elif array_id == "end":
            indices = np.asarray([i["iend"] for i in edges])
        else:
            raise EdgesError(f"The array identifier '{array_id}' provided is invalid.")
        # Return relevant arrays with the values.
        return (np.copy(self._hv[indices]), np.copy(self._vv[indices]))

    def edges_plot(
        self,
        path: str,
        edges: Sequence[Edge],
        *args,
        begin: float | None = None,
        end: float | None = None,
        munits: float = 0,
        points: Sequence[Literal["begin", "intermediate", "end"]] = (),
        **kwargs,
    ) -> Self:
        """Performs a plot of the edges of the signal.

        :param path: The path where to store the plot, see :meth:`.Plotter.plot`.
        :param edges: The edges to plot, if there are no edges, then no points will be plotted for edges.
        :param args: Additional arguments to pass to the plotting function, see :meth:`.Plotter.plot`.
        :param begin: The begin value of the horizontal axis where the plot starts, see :meth:`.Plotter.plot`.
        :param end: The end value of the horizontal axis where the plot ends, see :meth:`.Plotter.plot`.
        :param munits: Margin units for the plot, see :meth:`.Plotter.plot`.
        :param points: The type of edge points to plot, defaults to all edge points.
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

        # Add specified points for edges, if there are any edges.
        if len(edges) > 0:
            for point in ("begin", "intermediate", "end"):
                points_dict = {
                    "begin": ("Begin Edge Point", ">"),
                    "intermediate": ("Intermediate Edge Point", "8"),
                    "end": ("End Edge Point", "<"),
                }

                if len(points) == 0 or point in points:
                    (edges_x, edges_y) = self.edges_to_array(edges, point)

                    # For intermediate points, the values can be repeated for edges that share the same point,
                    # fetch unique values for plotting.
                    if point == "intermediate":
                        unique_indices = np.unique(edges_x, return_index=True)[1]
                        (edges_x, edges_y) = (edges_x[unique_indices], edges_y[unique_indices])

                    subplot = sep.Subplot(
                        points_dict[point][0],
                        edges_x,
                        self._hunits,
                        edges_y,
                        self._vunits,
                        begin,
                        end,
                        munits,
                        "white",
                        linestyle="none",
                        marker=points_dict[point][1],
                    )
                    plotter.add_plot(0, 0, subplot)

        # Create plot.
        plotter.plot(path, *args, **kwargs)

        return self
