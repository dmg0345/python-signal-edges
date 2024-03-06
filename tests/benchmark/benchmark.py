"""The files at `tests/benchmark` provide an example script to do profiling that can be customized for different
scenarios, it relies on `line_profiler <https://github.com/pyutils/line_profiler>`_ package.

The code snippet below shows how to run the benchmark script from a PowerShell terminal and save the results to file:

.. code-block:: powershell

    kernprof --line-by-line --builtin --outfile './tests/benchmark/benchmark.lprof' './tests/benchmark/benchmark.py';
    $output = python -m line_profiler -rmt "./tests/benchmark/benchmark.lprof";
    $output = $output -join [System.Environment]::NewLine;
    Set-Content -Path "./tests/benchmark/benchmark.txt" -Value "$output" -Force;

The following shows benchmarks for signals of different types using these scripts:

.. code-block::

    ~100k samples with ~500 edges:
        Filtering: 0.00 seconds, State Levels: 0.01 seconds, Edges: 0.06 seconds
    ~100k samples with ~5k edges:
        Filtering: 0.00 seconds, State Levels: 0.01 seconds, Edges: 0.61 seconds
    ~1M samples with ~5k edges:
        Filtering: 0.03 seconds, State Levels: 0.03 seconds, Edges: 0.58 seconds
    ~1M samples with ~50k edges:
        Filtering: 0.02 seconds, State Levels: 0.03 seconds, Edges: 4.86 seconds
    ~10M samples with ~50k edges:
        Filtering: 0.23 seconds, State Levels: 0.25 seconds, Edges: 5.32 seconds
    ~10M samples with ~500k edges:
        Filtering: 0.24 seconds, State Levels: 0.31 seconds, Edges: 52.75 seconds
    ~30M samples with ~25k edges:
        Filtering: 0.68 seconds, State Levels: 1.83 seconds, Edges: 4.50 seconds
    ~30M samples with ~2k edges:
        Filtering: 0.08 seconds, State Levels: 0.52 seconds, Edges: 0.88 seconds
    ~30M samples with ~150k edges:
        Filtering: 0.66 seconds, State Levels: 0.87 seconds, Edges: 19.44 seconds

Below some notes are listed in terms of performance:

- If the full range of the signal calculated from the state levels, :class:`.StateLevels`, is below an expected value
  for the user system, then a processing to extract edges can be skipped as there isn't any.

- Runt edges, :class:`~.edges.definitions.Type` are more time consuming to extract than normal edges, a signal with
  an excessive amount of runt edges can be a symptom of issues in the system or in the acquisition and a better
  signal conditioning could reduce their number.

- The intermediate point policy for edges, :class:`.IntPointPolicy`, can be adjusted to avoid calculation of
  intermediate points, forcing the use of the ``begin`` or ``end`` values as ``intermediate``. This can be convenient
  when the rising or falling times of the system are fast for the acquisition system to acquire samples during
  that period.

- For specific scenarios, disabling logging and the garbage collector temporarily during the processing."""

# pylint: skip-file

import gc
import os
import sys

# Add path to 'signal-edges' package and perform imports.
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from signal_edges.signal import VoltageSignal
from signal_edges.signal.edges import IntPointPolicy
from signal_edges.signal.generator import SignalGenerator

if __name__ == "__main__":
    # Disable garbage collection and enable profiling.
    gc.disable()
    profile.enable()  # type: ignore

    # Create generator with initial values.
    sampling_frequency = 100000
    generator = SignalGenerator(0, 1 / sampling_frequency, 100, 0, 100)

    # Build signal with multiple pulses.
    generator.add_flat(10)
    generator.add_edge("falling", 0, 10)
    generator.add_flat(10)
    generator.add_edge("rising", 10, 10)
    generator.repeat((1000000 - 40) // 40)

    # Generate signal with some noise.
    (signal_x, signal_y) = generator.generate(noise=(0, 5))

    # Create voltage signal from sample.
    signal = VoltageSignal(signal_x, signal_y, "s", "V")

    # Create filtered signal.
    profile(signal.filters_elliptic)  # type: ignore
    filtered_signal = signal.filters_elliptic(sampling_frequency, 4, sampling_frequency / 2.5)
    # Calculate state levels.
    profile(filtered_signal.state_levels)  # type: ignore
    (state_levels, (_, _)) = filtered_signal.state_levels()
    # Calculate edges.
    profile(filtered_signal.edges)  # type: ignore
    edges = filtered_signal.edges(state_levels, IntPointPolicy.POLICY_0)

    # Print some data.
    print(f"Number of samples: {len(signal.timestamps)}.")
    print(f"Number of edges extracted: {len(edges)}.")

    # End profile and resume garbage collection.
    profile.disable()  # type: ignore
    gc.enable()
