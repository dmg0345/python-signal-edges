"""Common exceptions for the package."""


class Error(Exception):
    """Base exception, all exceptions in the package must inherit from this one."""


class SignalError(Error):
    """Signal exception class."""


class VoltageSignalError(SignalError):
    """Voltage signal exception class."""


class FiltersError(Error):
    """Filters exception class."""


class EdgesError(Error):
    """Edges exception class."""


class StateLevelsError(Error):
    """State levels exception class."""


class PlotterError(Error):
    """Opinionated plotter exception class."""
