"""The sample module introduces the :class:`.Sample` and :class:`.Waveform` classes, a collection of utilities
specially intended for analysis of signals in notebooks, although they are also suitable for use outside these.

In this context, a `sample` is a collection of `waveforms`, each `sample` is stored in a directory,
managed by :class:`.SampleManager`, with the following structure:

.. code-block::

    samples
        sample_000
            waveform_000.npz
            waveform_001.npz
            ...
        sample_001
            waveform_000.npz
            waveform_001.npz
            ...
        ...

Each waveform is a ``.npz`` file generated with :meth:`numpy.savez_compressed` with additional metadata.

Each sample in the ``samples`` directory is identified by an integer number, and similarly each `waveform` in
each sample is identified by an integer number. For example notebooks where :class:`.Sample`, :class:`.SampleManager`
and :class:`.Waveform` are used refer to the `other/notebook` folders in the repository."""

import os
import re
import shutil
import sys
import tempfile
from collections.abc import Sequence
from typing import Any, Literal, TypeAlias, cast

import numpy as np
import numpy.typing as npt

try:
    import IPython
    import IPython.display
except ImportError:
    pass


from ... import plotter as sep
from ...exceptions import SignalError
from ..edges import Edge
from ..signal import Signal
from ..state_levels import StateLevels


class Waveform:
    """Utility class to handle a waveforms within :class:`.Sample`."""

    ## Private API #####################################################################################################
    def __init__(self, sid: int, wid: int, path: str) -> None:
        """Class constructor.

        :param wid: The waveform identifier.
        :param path: The path to the waveform file."""
        #: Sample identifier.
        self._sid = sid
        #: Waveform identifier.
        self._wid = wid

        self._meta = {}
        self._hvalues = np.asarray([1, 2, 3])
        self._vvalues = np.asarray([1, 2, 3])

        # Load waveform file and extract relevant data.
        with np.load(path) as data:
            #: The values of the horizontal axis.
            self._hvalues = data["hvalues"]
            #: The values of the vertical axis.
            self._vvalues = data["vvalues"]
            #: The metadata values.
            self._meta = {k: v for k, v in data.items() if k not in ("hvalues", "vvalues")}

    ## Protected API ###################################################################################################

    ## Public API ######################################################################################################
    @property
    def sid(self) -> int:
        """The sample identifier of the sample that contains this waveform.

        :return: Sample identifier."""
        return self._sid

    @property
    def wid(self) -> int:
        """The waveform identifier within the sample.

        :return: Waveform identifier."""
        return self._wid

    @property
    def hvalues(self) -> npt.NDArray[np.float_]:
        """The values of the horizontal axis.

        :return: The array with the values."""
        return self._hvalues

    @property
    def vvalues(self) -> npt.NDArray[np.float_]:
        """The values of the vertical axis.

        :return: The array with the values."""
        return self._vvalues

    @property
    def meta(self) -> dict[str, Any]:
        """Dictionary with the metadata of the waveform.

        :return: Metadata of the waveform."""
        return self._meta


class Sample:
    """Sample class with its underlying instances of :class:`.Waveform` for each waveform."""

    ## Private API #####################################################################################################
    def __init__(self, sid: int, waveforms: Sequence[Waveform]) -> None:
        """Class constructor.

        :param sid: The sample identifier.
        :param waveforms: The waveforms for the sample."""
        #: Sample identifier.
        self._sid = sid
        #: The waveforms of the sample.
        self._waveforms: dict[int, Waveform] = {wfm.wid: wfm for wfm in waveforms}

    ## Protected API ###################################################################################################

    ## Public API ######################################################################################################
    @property
    def sid(self) -> int:
        """The sample identifier for the sample.

        :return: The sample identifier."""
        return self._sid

    @property
    def waveforms(self) -> dict[int, Waveform]:
        """A dictionary with the waveforms, where the keys are waveform identifiers and the values are the waveforms.

        :return: Dictionary with the waveforms for the sample."""
        return self._waveforms


ItemSignal: TypeAlias = tuple[float, float, float, str, str, Signal]
ItemStateLevels: TypeAlias = tuple[float, float, float, Signal, StateLevels]
ItemEdges: TypeAlias = tuple[float, float, float, Signal, Sequence[Edge]]
Item: TypeAlias = tuple[Literal["signal", "state_levels", "edges"], ItemSignal | ItemStateLevels | ItemEdges]


class SampleManager:
    """Manages the samples in the given root directory."""

    ## Private API #####################################################################################################
    def __init__(self, root: str) -> None:
        """Class constructor.

        :param root: Root directory where the samples are located.
        :raise SignalError: The root directory does not exist."""
        if not all([os.path.exists(root), os.path.isdir(root)]):
            raise SignalError(f"The path to samples '{root}' does not exist.")
        #: Path to the root directory with the samples.
        self._root = os.path.normpath(os.path.realpath(root))

    ## Protected API ###################################################################################################
    def _get_spath(self, sid: int) -> str:
        """Obtains the path to the specified sample.

        :param sid: The sample identifier.
        :return: The path to the sample folder."""
        return os.path.join(self._root, f"sample_{sid:03}")

    def _get_wpath(self, sid: int, wid: int) -> str:
        """Obtains the path to a waveform in a sample.

        :param sid: The sample identifier.
        :param wid: The waveform identifier.
        :return: The path to the waveform file."""
        return os.path.join(self._get_spath(sid), f"waveform_{wid:03}.npz")

    ## Public API ######################################################################################################
    @staticmethod
    def plot(
        row_0: Sequence[Item],
        *args,
        path: str | None = None,
        mode: sep.Mode = sep.Mode.LINEAR,
        points: Sequence[Literal["begin", "intermediate", "end"]] = (),
        levels: Sequence[Literal["highest", "high", "high_runt", "intermediate", "low_runt", "low", "lowest"]] = (),
        row_1: Sequence[Item] = (),
        row_2: Sequence[Item] = (),
        row_3: Sequence[Item] = (),
        cursors: Sequence[sep.Cursor] = (),
        **kwargs,
    ) -> None:
        """Shortcut for complex plots related to samples, refer to implementation and code snippets for more details.

        :param row_0: Plot items for the first row.
        :param args: The arguments to pass to the plotter, see :meth:`.Plotter.plot`.
        :param path: Path where to save the resulting plot, see :meth:`.Plotter.plot`, or ``None`` for notebooks.
        :param mode: The mode of operation of the plotter, see :meth:`.Plotter.plot`.
        :param points: When plotting edges, the point of the edges to plot, defaults to all.
        :param levels: When plotting state levels, the levels to plot, defaults to all.
        :param row_1: Plot items for the second row, if any.
        :param row_2: Plot items for the third row, if any.
        :param row_3: Plot items for the fourth row, if any.
        :param cursors: Cursors for the plot.
        :param kwargs: The keyword arguments to pass to the plotter, see :meth:`.Plotter.plot`.
        :raise SignalError: An item identifier is invalid or not recognized."""
        # pylint: disable=too-complex,too-many-locals,redefined-loop-name,too-many-nested-blocks,too-many-branches
        # pylint: disable=too-many-statements

        # Calculate the number of rows.
        rows = 1
        rows += 1 if len(row_1) > 0 else 0
        rows += 1 if len(row_2) > 0 else 0
        rows += 1 if len(row_3) > 0 else 0

        # Create plotter.
        plotter = sep.Plotter(mode=mode, rows=rows, columns=1)

        # Handle signal and edges.
        for row_i, row in enumerate([row_0, row_1, row_2, row_3]):
            # If there is no plots in the row, then skip to the next.
            if len(row) == 0:
                continue

            for item_id, item in row:
                ########################################################################################################
                if item_id == "signal":
                    # Get relevant data from item.
                    item = cast(ItemSignal, item)
                    (begin, end, munits, name, color, signal) = item
                    (hvalues, vvalues) = (getattr(signal, "_hv"), getattr(signal, "_vv"))
                    (hunits, vunits) = (getattr(signal, "_hunits"), getattr(signal, "_vunits"))

                    # Create subplot for signal.
                    spl = sep.Subplot(name, hvalues, hunits, vvalues, vunits, begin, end, munits, color=color)

                    # Add plot in relevant row and column.
                    plotter.add_plot(row_i, 0, spl)
                ########################################################################################################
                elif item_id == "state_levels":
                    # Get relevant data from item.
                    item = cast(ItemStateLevels, item)
                    (begin, end, munits, signal, state_levels) = item
                    (hunits, vunits) = (getattr(signal, "_hunits"), getattr(signal, "_vunits"))
                    state_levels_to_array = getattr(signal, "state_levels_to_array")

                    # Create subplot for signal.
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
                            (level_x, level_y) = state_levels_to_array(state_levels, level)
                            subplot = sep.Subplot(
                                levels_dict[level],
                                level_x,
                                hunits,
                                level_y,
                                vunits,
                                begin,
                                end,
                                munits,
                                "#7F7F7F",
                                linestyle="dotted",
                                marker="none",
                            )
                            plotter.add_plot(row_i, 0, subplot)
                ########################################################################################################
                elif item_id == "edges":
                    # Get relevant data from item.
                    item = cast(ItemEdges, item)
                    (begin, end, munits, signal, edges) = item
                    (hunits, vunits) = (getattr(signal, "_hunits"), getattr(signal, "_vunits"))
                    edges_to_array = getattr(signal, "edges_to_array")

                    # If there are any edges plot them.
                    if len(edges) > 0:
                        for point in ("begin", "intermediate", "end"):
                            points_dict = {
                                "begin": ("Begin Edge Point", ">"),
                                "intermediate": ("Intermediate Edge Point", "8"),
                                "end": ("End Edge Point", "<"),
                            }

                            if len(points) == 0 or point in points:
                                (edges_x, edges_y) = edges_to_array(edges, point)

                                # For intermediate points, the values can be repeated for edges that share the
                                # same point, fetch unique values for plotting.
                                if point == "intermediate":
                                    unique_indices = np.unique(edges_x, return_index=True)[1]
                                    (edges_x, edges_y) = (edges_x[unique_indices], edges_y[unique_indices])

                                subplot = sep.Subplot(
                                    points_dict[point][0],
                                    edges_x,
                                    hunits,
                                    edges_y,
                                    vunits,
                                    begin,
                                    end,
                                    munits,
                                    "white",
                                    linestyle="none",
                                    marker=points_dict[point][1],
                                )
                                plotter.add_plot(row_i, 0, subplot)
                ########################################################################################################
                else:
                    raise SignalError(f"Invalid item identifier '{item_id}' for item in plot.")

        # Handle cursors.
        for cursor in cursors:
            plotter.add_cursor(cursor)

        # Run plotter if plotting to file, otherwise plot and display.
        if path is None:
            # Check if relevant module was imported.
            if "IPython" not in sys.modules:
                raise SignalError("Can't plot to notebook because IPython was not imported.")

            # Plot to temporary file, display it in notebook and then delete it.
            with tempfile.NamedTemporaryFile("w+", suffix=".png", delete=False) as file:
                plotter.plot(i := os.path.normpath(file.name), *args, **kwargs)
                IPython.display.display(IPython.display.Image(i))  # type: ignore
                os.unlink(i)
        else:
            plotter.plot(path, *args, **kwargs)

    def get_sids(self) -> tuple[int, ...]:
        """Obtains the existing sample identifiers in the root folder.

        :return: The sample identifiers."""
        return tuple(
            int(match.groups()[0])
            for i in os.listdir(self._root)
            if os.path.isdir(os.path.join(self._root, i))
            and ((match := re.match(r"sample_([0-9]{3})$", i)) is not None)
        )

    def get_wids(self, sid: int) -> tuple[int, ...]:
        """Obtains the waveform identifiers of a sample in the root folder.

        :param sid: The sample identifier.
        :return: The waveform identifiers for the sample."""
        return tuple(
            int(match.groups()[0])
            for i in os.listdir(self._get_spath(sid))
            if os.path.isfile(os.path.join(self._get_spath(sid), i))
            and ((match := re.match(r"waveform_([0-9]{3}).npz$", i)) is not None)
        )

    def new(self, sid: int, waveforms: Sequence[dict[str, Any]], overwrite: bool = False) -> Sample:
        """Creates a new sample with the data for the waveforms provided in the format below:

        .. code-block:: json

            {
                "wid": "An integer with the waveform identifier",
                "vvalues": "Numpy array with values for the vertical axis of a signal",
                "hvalues": "Numpy array with values for the horizontal axis of a signal"
            }

        Any other value in the waveform dictionary is stored in the `.npz` file as metadata.

        :param sid: The sample identifier of the new sample.
        :param waveforms: The waveforms for the sample following the format described above for each.
        :param overwrite: Overwrite the sample if it exists, if ``False`` then raise exception instead.
        :raise SignalError: The specified sample already exists and ``overwrite`` was set to ``False``.
        :raise SignalError: At least one of the waveforms is not in the correct format.
        :return: The sample created."""
        # Get path for sample, and check if it exists, handling overwrite.
        if os.path.exists(spath := self._get_spath(sid)):
            if not overwrite:
                raise SignalError(f"Sample at path '{spath}' already exists.")
            shutil.rmtree(spath)
        # Create directory structure.
        os.makedirs(spath)

        # Store each waveform.
        for _, wfm in enumerate(waveforms):
            # Ensure mandatory keys exist.
            if not all(i in wfm.keys() for i in ("wid", "vvalues", "hvalues")):
                raise SignalError("At least one of the mandatory keys for the waveform dictionary is missing.")
            # Save to file.
            np.savez_compressed(self._get_wpath(sid, wfm["wid"]), **{k: wfm[k] for k in wfm.keys() if k != "wid"})

        # Return loaded sample.
        return self.load(sid)

    def load(self, sid: int) -> Sample:
        """Loads the specified sample from the root folder.

        :param sid: The sample identifier.
        :raise SignalError: The sample specified does not exist.
        :return: The sample with its waveforms."""
        # Get path to sample.
        if not os.path.exists(spath := self._get_spath(sid)):
            raise SignalError(f"The sample at '{spath}' does not exist.")
        # Return loaded sample.
        return Sample(sid, [Waveform(sid, wid, self._get_wpath(sid, wid)) for wid in self.get_wids(sid)])

    def save(self, sid: int, sample: Sample, overwrite: bool = False) -> Sample:
        """Saves the save to the root folder, overwriting a previous sample if it exists.

        :param sid: The sample identifier.
        :param sample: The sample to save.
        :param overwrite: Overwrite the sample if it exists, if ``False`` then raise exception instead.
        :return: The sample that was just saved."""
        # Convert sample to waveform dictionaries and create anew.
        return self.new(
            sid,
            [{"wid": k, "hvalues": v.hvalues, "vvalues": v.vvalues, **v.meta} for k, v in sample.waveforms.items()],
            overwrite,
        )
