"""The plotter, :class:`.Plotter`, is an opinionated and customized plotter based on `matplotlib` suitable for the
plotting of signals and their generated artifacts in |ProjectName|. It supports additional features such as the use
of rasters when plotting millions of samples, shared horizontal axis between plots or plot of cursors for points
of interest.

The plotter is used throughout the package to generate the plots included in this documentation, some other more
complex plots that can be achieved with this plotter are shown below:

.. figure:: ../.assets/img/006_example_complex_plot_0.png
    :width: 600
    :align: center
    
    Plot of three different signals with synchronized edges, with cursors, state levels and points of the edges.
    
.. figure:: ../.assets/img/007_example_complex_plot_1.png
    :width: 600
    :align: center
    
    The same plot as before but with the original unfiltered signals in grey.

The plotter supports many different kinds of plots to explicitly document them all, for code snippets and examples,
refer to the existing uses of the plotter throughout |ProjectName| and the `API` described below."""

import os

import matplotlib
import matplotlib.axes
import matplotlib.figure
import matplotlib.patheffects
import matplotlib.pyplot
import numpy as np

from ..definitions import get_logger
from ..exceptions import PlotterError
from .definitions import Cursor, Mode, Plot, PlotArea, Subplot


class Plotter:
    """Implementation of an plotter based on `matplotlib`."""

    #: Path to the matplotlib style file.
    _style = os.path.join(os.path.normpath(os.path.dirname(__file__)), "style", "style.mplstyle")

    ## Private API #####################################################################################################
    def __init__(self, *args, mode: Mode = Mode.LINEAR, rows: int = 1, columns: int = 1, **kwargs) -> None:
        """Class constructor.

        :param mode: The plotter mode.
        :param rows: Number of rows in the plot.
        :param columns: Number of colums in the plot.
        :raise PlotterError: The number of rows must be higher than zero.
        :raise PlotterError: The number of columns must be higher than zero.
        :raise PlotterError: The number of columns for an horizontal shared axis plot must be one."""
        # pylint: disable=unused-argument

        #: Logger.
        self._logger = get_logger()
        #: Plotter mode.
        self._mode = mode
        #: Number of rows.
        self._rows = rows
        #: Number of columns.
        self._columns = columns

        # Sanity check on values.
        if self._rows <= 0:
            raise PlotterError("At least one row must be specified for plotter.")
        if self._columns <= 0:
            raise PlotterError("At least one column must be specified for plotter.")
        if all([self._mode is Mode.SHARED_H_AXIS, self._columns > 1]):
            raise PlotterError("For a plotter with shared horizontal axis, the number of columns must be one.")

        #: Plot area.
        self._area: PlotArea = {j: {i: [] for i in range(self._columns)} for j in range(self._rows)}
        #: Cursors.
        self._cursors: list[Cursor] = []

    ## Protected API ###################################################################################################
    def _get_plot(self, row: int, column: int) -> Plot | None:
        """Obtains a plot from its row and column indices, with all its subplots.

        :param row: The index of the row, must be zero or a positive number.
        :param column: The index of the column, must be zero or a positive number.
        :return: The plot, or ``None`` if the row and columns are not valid."""
        if any([row >= self._rows, row < 0, column >= self._columns, column < 0]):
            return None
        return self._area[row][column]

    def _get_plot_coords(self, subplot_id: str) -> tuple[int, int] | None:
        """Obtains the row and column indices for a plot from one of its subplot identifiers.

        :param subplot_id: Subplot identifier to identify the plot.
        :return: The row and column indices, or ``None`` if no plot found for subplot identifier."""
        for row_key, row in self._area.items():
            for column_key, column in row.items():
                if subplot_id in tuple(i.name for i in column):
                    return (row_key, column_key)
        return None

    ## Public API ######################################################################################################
    def add_plot(self, row: int, column: int, subplot: Subplot) -> "Plotter":
        """Adds a subplot to the plot at specified row and column indices.

        :param row: The index of the row to the the plot where to add the subplot.
        :param column: The index of the column to the plot where to add the subplot.
        :param subplot: The definition of the subplot to add.
        :raise PlotterError: The begin and end value of the subplot to add are inconsistent.
        :raise PlotterError: The values provided for one of the axis are empty, not the same length or invalid.
        :raise PlotterError: The row and column indices given do not map to a plot.
        :raise PlotterError: The subplot identifier provided already exists in the plot.
        :raise PlotterError: The units of the horizontal and vertical axes of the subplot must match current plot.
        :raise PlotterError: When sharing an horizontal axis, all horizontal axis and margin units must be the same.
        :return: Instance of the class."""
        # Check that the begin is before the end value in the subplot.
        if subplot.begin > subplot.end:
            raise PlotterError("Subplot begin value must be less than the subplot end value.")
        # Check that the horizontal values and vertical values of the subplot to add satisfy requirements.
        if any(
            [
                len(subplot.hvalues) != len(subplot.vvalues),
                len(subplot.vvalues) == 0,
                len(subplot.hvalues) == 0,
                len(np.where(np.diff(subplot.hvalues) <= 0)[0]) > 0,  # Check x[n] < x[n+1].
            ]
        ):
            raise PlotterError("Values of the axis of the subplot to add are invalid.")
        # Check if the coordinates are valid.
        if (plot := self._get_plot(row, column)) is None:
            raise PlotterError("The row and column indices given do not map to a plot.")
        # Check that there is no subplot of given identifier in plot.
        if any(i.name == subplot.name for i in plot):
            raise PlotterError("The subplot identifier provided already exists in plot.")
        # Check that the units of the plot to add and the current plots in the slot are all the same.
        if not all(subplot.hunits == i.hunits and subplot.vunits == i.vunits for i in plot):
            raise PlotterError("Horizontal or vertical axis units in subplot to add do not match existing plot.")

        # Check that if running in common axis mode.
        if self._mode is Mode.SHARED_H_AXIS:
            # Check that the horizontal axis and margin units are all the same in all the subplots in every plots.
            if not all(
                i.hunits == subplot.hunits and i.munits == subplot.munits
                for (_, row) in self._area.items()
                for i in row[0]
            ):
                raise PlotterError("All subplots in every plot must have the same horizontal axis and margin units.")

        self._area[row][column].append(subplot)

        return self

    def add_cursor(self, cursor: Cursor) -> "Plotter":
        """Adds a cursor to the plot.

        :param cursor: The definition of the cursor to add.
        :raise PlotterError: The row and column indices given do not map to a plot.
        :raise PlotterError: No subplot identifiers were given for cursor.
        :raise PlotterError: At least one of the subplot identifiers in the cursor is invalid.
        :raise PlotterError: The index of the cursor does not exist in all the subplots specified.
        :return: Instance of the class."""
        # Check if row and column are consistent.
        if (plot := self._get_plot(cursor.row, cursor.column)) is None:
            raise PlotterError("The row and column indices given do not map to a plot.")
        # Check if all the subplot identifiers exist in the plot.
        if len(cursor.subplot_ids) == 0:
            raise PlotterError("No subplot identifiers were given for cursor.")
        # Check if all the subplot identifiers exist in the plot.
        if not all(subplot_id in [i.name for i in plot] for subplot_id in cursor.subplot_ids):
            raise PlotterError("At least one of the subplot identifiers does not exist in plot.")
        # Check that all the indices exist in all the subplots.
        if not all(0 <= cursor.hindex < len(i.hvalues) for i in plot if i.name in cursor.subplot_ids):
            raise PlotterError("The cursor horizontal axis index value does not exist in all subplots in plot.")

        self._cursors.append(cursor)

        return self

    def plot(
        self,
        path: str,
        dpi: float = 300.0,
        figsize: tuple[float, float] = (19.20, 10.80),
        raster_limit: int = 1920,
        backend: str = "Agg",
    ) -> "Plotter":
        """Runs the plotter and saves the results to file.

        :param path: Path where to store the resulting ``.png`` file with the plot.
        :param dpi: See :class:`matplotlib.figure.Figure` for details.
        :param figsize: See :class:`matplotlib.figure.Figure` for details, defaults to 1080p.
        :param raster_limit: Uses rasters and pixel markers below this number of values to optimize plotting speed.
        :param backend: See :meth:`matplotlib.figure.Figure.savefig` for details.
        :return: Instance of the class."""
        # pylint: disable=too-complex,too-many-arguments,too-many-locals,too-many-branches,too-many-statements

        # Check if file exists, and if so, delete it.
        if os.path.exists(path):
            os.unlink(path)
        # Check if directory name exists, if not, create directory structure.
        if not os.path.exists(dir_path := os.path.dirname(path)):
            os.makedirs(dir_path)

        # If dealing with a common axis, then analyze all the current plots and calculate common begin and end values.
        common_begin, common_end = 0, 0
        if self._mode is Mode.SHARED_H_AXIS:
            # Calculate the lowest start value, and use that for all plots.
            common_begin = min(subplot.begin for (_, i) in self._area.items() for (_, j) in i.items() for subplot in j)
            # Calculate the highest end value, and use that for all plots.
            common_end = max(subplot.end for (_, i) in self._area.items() for (_, j) in i.items() for subplot in j)

        # Create plots with specified custom style.
        with matplotlib.pyplot.style.context(self._style):  # type: ignore
            # Create figure.
            figure: matplotlib.figure.Figure = matplotlib.figure.Figure(dpi=dpi, figsize=figsize, layout="constrained")

            # Create subplots per plot.
            all_mpl_subplots = []
            for row_i, row in self._area.items():
                for column_i, column in row.items():
                    # If no subplots in current plot, then continue with the next.
                    if len(column) == 0:
                        continue
                    mpl_subplot = figure.add_subplot(self._rows, self._columns, row_i * self._columns + column_i + 1)

                    # Loop plots in the column.
                    for subplot in column:
                        # Calculate the begin and end values.
                        if self._mode is Mode.SHARED_H_AXIS:
                            begin, end = common_begin, common_end
                        else:
                            begin, end = subplot.begin, subplot.end

                        # Calculate begin and end values keeping into account the margin, with limits check.
                        mval = (end - begin) * subplot.munits
                        begin = subplot.hvalues[0] if (begin - mval) < subplot.hvalues[0] else (begin - mval)
                        end = subplot.hvalues[-1] if (end + mval) > subplot.hvalues[-1] else (end + mval)

                        # Get the relevand indices of the data to plot, if there is no data, the continue with the next.
                        indices = np.where((subplot.hvalues >= begin) & (subplot.hvalues <= end))[0]
                        if len(indices) == 0:
                            continue

                        # Get the values to plot from the horizontal and vertical axis.
                        hvalues = subplot.hvalues[indices]
                        vvalues = subplot.vvalues[indices]

                        # Plot, use rasters and use pixels as markers after the raster limit to speed up plotting.
                        marker = subplot.marker if any([len(hvalues) < raster_limit, subplot.marker == "none"]) else ","
                        mpl_subplot.plot(
                            hvalues,
                            vvalues,
                            label=subplot.name,
                            marker=marker,
                            linestyle=subplot.linestyle,
                            color=subplot.color,
                            rasterized=not len(hvalues) < raster_limit,
                        )

                        # Configure labels on both axes, this is redundant past the first call since we've
                        # already checked all the units are the same, but keep it here for type checkers.
                        mpl_subplot.set_xlabel(
                            f"{subplot.hunits.magnitude} / {subplot.hunits.name} ({subplot.hunits.symbol})",
                            fontsize="large",
                        )
                        mpl_subplot.set_ylabel(
                            f"{subplot.vunits.magnitude} / {subplot.vunits.name} ({subplot.vunits.symbol})",
                            fontsize="large",
                        )

                    # Disable margins on the X axis, as we control them above.
                    mpl_subplot.margins(x=0)

                    # Only have major X and major Y axis active.
                    mpl_subplot.grid(False, "both", "both")
                    mpl_subplot.grid(True, "major", "x")
                    mpl_subplot.grid(True, "major", "y")

                    # Configure fontsize of the major ticks numbers on the X and Y axis.
                    mpl_subplot.tick_params(axis="x", which="major", labelsize="medium")
                    mpl_subplot.tick_params(axis="y", which="major", labelsize="medium")

                    # Give some padding to labels.
                    mpl_subplot.xaxis.labelpad = 10
                    mpl_subplot.yaxis.labelpad = 10

                    # Set legend for the subplots with some transparency.
                    mpl_subplot.add_artist(
                        mpl_subplot.legend(
                            title="Plots",
                            title_fontsize="medium",
                            loc="lower left",
                            frameon=True,
                            framealpha=0.60,
                            fontsize="small",
                        )
                    )

                    # Collect relevant cursors for this plot and handle them.
                    all_mpl_cursors = []
                    cursors = tuple(i for i in self._cursors if all([i.row == row_i, i.column == column_i]))
                    for _, cursor in enumerate(cursors):
                        # Get relevant subplots for cursor, at least one exists.
                        subplots = [subplot for subplot in column if subplot.name in cursor.subplot_ids]
                        # Get horizontal value from first subplot as a reference.
                        cursor_hvalue = subplots[0].hvalues[cursor.hindex]

                        # Build label for cursor.
                        label = f"{cursor.name}: [X: {np.round(cursor_hvalue, cursor.hvdec)}"
                        for subplot in subplots:
                            label += f", {subplot.name}: {np.round(subplot.vvalues[cursor.hindex], cursor.vvdec)}"
                        label += "]"

                        # Plot cursor as a vertical line.
                        all_mpl_cursors.append(
                            mpl_subplot.axvline(
                                cursor_hvalue,
                                linewidth=1,
                                linestyle=cursor.linestyle,
                                color=cursor.color,
                                label=label,
                            )
                        )

                        # Annotate the name of the cursor on top of it, if overlaps occur, that is on the user
                        # who should place cursors not too close to each other or with shorter names.
                        mpl_subplot.annotate(
                            cursor.name,
                            (cursor_hvalue, mpl_subplot.get_ylim()[1]),
                            ha="left",
                            va="center",
                            annotation_clip=False,
                            xytext=(-3, 8),
                            textcoords="offset points",
                            fontsize="medium",
                            color=cursor.color,
                            path_effects=[
                                matplotlib.patheffects.Stroke(linewidth=1, foreground="black"),
                                matplotlib.patheffects.Normal(),
                            ],
                        )

                    # If cursors were added, then also add the legend for cursors with some transparency.
                    if len(all_mpl_cursors) > 0:
                        mpl_subplot.add_artist(
                            mpl_subplot.legend(
                                handles=all_mpl_cursors,
                                title="Cursors",
                                title_fontsize="medium",
                                loc="lower right",
                                frameon=True,
                                framealpha=0.60,
                                fontsize="small",
                                handletextpad=0,
                                handlelength=0,
                            )
                        )

                    # Append subplot to list of subplots.
                    all_mpl_subplots.append(mpl_subplot)

            # Adjust shared axis on all subplots if set for that mode.
            if self._mode is Mode.SHARED_H_AXIS:
                for mpl_subplot_i, mpl_subplot in enumerate(all_mpl_subplots):
                    # Create the shared axis when there is at least two subplots.
                    if mpl_subplot_i > 0:
                        mpl_subplot.sharex(all_mpl_subplots[mpl_subplot_i - 1])
                    # Hide all horizontal axis, except for the last one, but keep grids visible.
                    if mpl_subplot_i != (len(all_mpl_subplots) - 1):
                        mpl_subplot.tick_params(axis="x", which="both", labelcolor="None", labelsize=0)
                        mpl_subplot.set_xlabel("")

            # Adjust padding between subplots.
            figure.get_layout_engine().set(w_pad=1 / 10, h_pad=1 / 10, hspace=1 / 20, wspace=1 / 20)  # type: ignore

            # Configure backends.
            if backend == "Agg":
                matplotlib.rcParams["agg.path.chunksize"] = 100000

            # Save to file or display on screen.
            figure.savefig(path, format="png", backend=backend)

        return self
