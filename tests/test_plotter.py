"""Tests for the opinionated plotter."""

import os

import numpy as np
import numpy.typing as npt
import pytest

from signal_edges.plotter import Cursor, Mode, Plotter, Subplot, Units

from .conftest import env_plots


class TestPlotter:
    """A collection of tests for the opinionated plotter."""

    ## Private API #####################################################################################################

    ## Protected API ###################################################################################################
    @staticmethod
    def _gen_axis(start: float, step: float, count: int) -> npt.NDArray[np.float_]:
        """Generates the values of an axis for plotting.

        :param start: The start value for the axis.
        :param step: The step between the values.
        :param count: The number of values.
        :return: Array with the values."""
        return np.arange(start, start + step * count, step)

    ## Public API ######################################################################################################
    @pytest.mark.parametrize("rows", [1, 2])
    @pytest.mark.parametrize("columns", [1, 2])
    @pytest.mark.parametrize("count", [10000, 10000000])
    @pytest.mark.parametrize("plots_num", [1, 2, 4])
    @pytest.mark.parametrize("adir", ["linear_plot"], indirect=True)
    def test_linear_plot(self, rows: int, columns: int, count: int, plots_num: int, adir: str) -> None:
        """Tests several combinations of linear plots, saving the results to file for visual inspection.

        :param rows: The number of rows.
        :param columns: The number of columns.
        :param count: The number of values in each axis of each row and column.
        :param plots_num: The number of plots in each row and column.
        :param adir: The path where the plots will be stored."""
        # pylint: disable=too-many-arguments,too-many-locals

        # Create plotter and name from parameters.
        plot_path = os.path.join(adir, f"rw{rows}_cl{columns}_cn{count}_pn{plots_num}.png")
        plotter = Plotter(Mode.LINEAR, rows=rows, columns=columns)

        # Add plots to each slot.
        for row_i in range(rows):
            for column_i in range(columns):
                # Get a slot index from the rows and columns..
                slot_i = row_i * columns + column_i

                # Create plots and add them to the plotter.
                for plot_i in range(plots_num):
                    # Generate arrays.
                    hvalues = self._gen_axis(0.0, 1.0, count)  # Note for simplicity indices match values.
                    vvalues = self._gen_axis(0.0, 1.0 + slot_i * plot_i, count)

                    # Create plot and add it.
                    plot = Subplot(
                        name=f"pl{plot_i}",
                        hvalues=hvalues,
                        hunits=Units("N/A", "N/A", "N/A"),
                        vvalues=vvalues,
                        vunits=Units("N/A", "N/A", "N/A"),
                        begin=(count / 10) * 2,
                        end=(count / 10) * 8,
                        munits=1,
                        color=["red", "blue", "green", "violet"][plot_i],
                    )
                    plotter.add_plot(row_i, column_i, plot)

                # Create cursors and add them to the plotter.
                for cursor_i in range(7):
                    # Create cursor and add it.
                    cursor = Cursor(
                        name=["A", "B", "C", "D", "E", "F", "G"][cursor_i],
                        hindex=int((count / 10) * {0: 2, 1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 8}[cursor_i]),
                        row=row_i,
                        column=column_i,
                        subplot_ids=[f"pl{i}" for i in range(plots_num)],
                    )
                    plotter.add_cursor(cursor)

        # Perform plot and save to file.
        if env_plots():
            plotter.plot(plot_path)

    @pytest.mark.parametrize("rows", [1, 2])
    @pytest.mark.parametrize("count", [10000, 10000000])
    @pytest.mark.parametrize("plots_num", [1, 2, 4])
    @pytest.mark.parametrize("adir", ["shared_x_axis_plot"], indirect=True)
    def test_shared_x_axis_plot(self, rows: int, count: int, plots_num: int, adir: str) -> None:
        """Tests several combinations of shared horizontal axis plots, saving the results to file for visual inspection.

        :param rows: The number of rows.
        :param count: The number of values in each axis of each row and column.
        :param plots_num: The number of plots in each row and column.
        :param adir: The path where the plots will be stored."""
        # Create plotter and name from parameters.
        plot_path = os.path.join(adir, f"rw{rows}_cn{count}_pn{plots_num}.png")
        plotter = Plotter(Mode.SHARED_H_AXIS, rows=rows, columns=1)

        # Add plots to each slot.
        for row_i in range(rows):
            # Create plots and add them to the plotter.
            for plot_i in range(plots_num):
                # Generate arrays.
                hvalues = self._gen_axis(0.0, 1.0, count)  # Note for simplicity indices match values.
                vvalues = self._gen_axis(0.0, 1.0 + row_i * plot_i, count)

                # Create plot and add it.
                plot = Subplot(
                    name=f"pl{plot_i}",
                    hvalues=hvalues,
                    hunits=Units("N/A", "N/A", "N/A"),
                    vvalues=vvalues,
                    vunits=Units("N/A", "N/A", "N/A"),
                    begin=(count / 10) * 2,
                    end=(count / 10) * 8,
                    munits=1,
                    color=["red", "blue", "green", "violet"][plot_i],
                )
                plotter.add_plot(row_i, 0, plot)

            # Create cursors and add them to the plotter.
            for cursor_i in range(7):
                # Create cursor and add it.
                cursor = Cursor(
                    name=["A", "B", "C", "D", "E", "F", "G"][cursor_i],
                    hindex=int((count / 10) * {0: 2, 1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 8}[cursor_i]),
                    row=row_i,
                    column=0,
                    subplot_ids=[f"pl{i}" for i in range(plots_num)],
                )
                plotter.add_cursor(cursor)

        # Perform plot and save to file.
        if env_plots():
            plotter.plot(plot_path)
