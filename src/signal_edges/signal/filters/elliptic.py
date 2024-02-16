"""The :class:`.EllipticFiltersMixin` implements a mixin that can be added to :class:`.Signal` derived classes to
add elliptic filters functionality, as shown in the code snippet below:

.. code-block:: python

    import signal_edges.signal as ses

    class ExampleSignal(ses.filters.EllipticFiltersMixin, ses.Signal):
        pass
        
An example of its usage using :class:`.VoltageSignal` is described below:

.. code-block:: python

    import numpy as np
    import signal_edges.signal as ses

    # Create timestamps for the signal, and calculate the sampling frequency.
    signal_timestamps = np.linspace(start=0, stop=160, num=160, endpoint=False)
    sampling_frequency = 1 / (signal_timestamps[1] - signal_timestamps[0])
    # Create voltages for the signal, and add some noise to them.
    signal_voltages = np.asarray([0, 0, 0, 0, 5, 5, 5, 5, 5, 5] * (160 // 10)) + \\
                      np.random.normal(0, 0.1, 160)
    # Create signal.
    signal = ses.VoltageSignal(signal_timestamps, signal_voltages, "s", "V")
    # Create the filtered signal.
    filtered_signal = signal.filters_elliptic(sampling_frequency, 2, lp_cutoff=sampling_frequency / 2.5)
    
    # Plot original signal and filtered signal.
    signal.filters_plot("signal.png", filtered_signal)

This code snippet generates the following plot:

.. figure:: ../../.assets/img/003_example_elliptic_signal.png
    :width: 600
    :align: center
    
    The generated signal and filtered signal in the code snippet."""

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

from copy import deepcopy

import scipy.signal

from ...exceptions import FiltersError
from .filters import FiltersMixin


class EllipticFiltersMixin(FiltersMixin):
    """Mixin derived from :class:`.FiltersMixin` for :class:`.Signal` that implements elliptic filters."""

    # pylint: disable=too-few-public-methods

    ## Private API #####################################################################################################

    ## Protected API ###################################################################################################

    ## Public API ######################################################################################################
    def filters_elliptic(
        self,
        sampling_frequency: float,
        order: int,
        lp_cutoff: float | None = None,
        hp_cutoff: float | None = None,
        bp_cutoff: tuple[float, float] | None = None,
        bs_cutoff: tuple[float, float] | None = None,
        pb_ripple: float = 0.1,
        sb_ripple: float = 100.0,
    ) -> Self:
        """Runs an elliptic filter on the signal, refer to :func:`scipy.signal.ellip` for more information.

        One of ``lp_cutoff``, ``hp_cutoff``, ``bp_cutoff`` or ``bs_cutoff`` must be specified. If none or more than one
        are specified, an error is raised as it won't be possible to determine the type of filter to apply.

        :param sampling_frequency: Sampling frequency in Hertz.
        :param order: Order of the filter.
        :param lp_cutoff: Use a lowpass filter with this cutoff frequency in Hertz, defaults to ``None``.
        :param hp_cutoff: Use a highpass filter with this cutoff frequency in Hertz, defaults to ``None``.
        :param bp_cutoff: Use a bandpass filter with this pair of cutoff frequencies in Hertz, defaults to ``None``.
        :param bs_cutoff: Use a bandstop filter with this pair of cutoff frequencies in Hertz, defaults to ``None``.
        :param pb_ripple: Pass band ripple, defaults to ``0.1``.
        :param sb_ripple: Stop band ripple, defaults to ``100.0``.
        :raise FiltersError: Could not determine the type of filter to use.
        :raise FiltersError: Could not create underlying Second Order Sections for filter.
        :return: A new instance of the class with the filtered signal."""
        # pylint: disable=too-many-arguments

        # Figure out filter mode from the cutoff frequencies.
        if all([lp_cutoff is not None, hp_cutoff is None, bp_cutoff is None, bs_cutoff is None]):
            cutoff, ftype = lp_cutoff, "lowpass"
        elif all([lp_cutoff is None, hp_cutoff is not None, bp_cutoff is None, bs_cutoff is None]):
            cutoff, ftype = hp_cutoff, "highpass"
        elif all([lp_cutoff is None, hp_cutoff is None, bp_cutoff is not None, bs_cutoff is None]):
            cutoff, ftype = bp_cutoff, "bandpass"
        elif all([lp_cutoff is None, hp_cutoff is None, bp_cutoff is None, bs_cutoff is not None]):
            cutoff, ftype = bs_cutoff, "bandstop"
        else:
            raise FiltersError("Invalid cutoff frequency combination given to elliptic filter.")

        # Create second order sections and check they are valid.
        sos = scipy.signal.ellip(
            N=order,
            rp=pb_ripple,
            rs=sb_ripple,
            Wn=cutoff,
            btype=ftype,
            analog=False,
            output="sos",
            fs=sampling_frequency,
        )
        if sos is None:
            raise FiltersError("Invalid elliptic filter configuration given.")

        # Create a copy of self, and update the vertical values with the new filtered values.
        filtered_signal = deepcopy(self)

        # Use zero phase filter for filtering, creating the same number of samples.
        setattr(filtered_signal, "_vv", scipy.signal.sosfiltfilt(sos, self._vv))

        return filtered_signal
