Introduction
========================================================================================================================

|ProjectName| (|ProjectFriendlyName|) is a Python package capable of filtering, extracting state levels and edges of
signals with millions of samples, among other things. It is specially suited for analysis of analog signals obtained
through tooling such as oscilloscopes or data recorders and hardware automation in CI/CD environments, although it
is flexible enough to be used for many other different purposes.

Among others, it uses the following packages underneath:

- `Numpy <https://github.com/numpy/numpy>`_, for analysis of the arrays that define the signals.
- `Scipy <https://github.com/scipy/scipy>`_, for filtering of signals.
- `Matplotlib <https://github.com/matplotlib/matplotlib>`_, for plotting of the signals.

It is recommended to start reading the documentation from the :doc:`/signal/index` chapter, and then move towards
other chapters as functionality is required. The :doc:`/faq/index` chapters covers other topics not specific to a
chapter.

.. note::

    This is the documentation for |ProjectName|, version |ProjectVersion|.

Development
------------------------------------------------------------------------------------------------------------------------

The source code for |ProjectName| is hosted at `Github <https://github.com/dmg0345/python-signal-edges>`_
and related *Docker* images for development containers are located at
`DockerHub <https://hub.docker.com/r/dmg00345/python_signal_edges>`_.

For details about automated tests for this release refer to the testing and coverage reports at
`Test Results HTML Report <_static/_test_results/test_report.html>`_ and
`Code Coverage HTML report <_static/_test_coverage/index.html>`_.

License
------------------------------------------------------------------------------------------------------------------------

.. literalinclude:: ../LICENSE

.. toctree::
    :caption: Main
    :maxdepth: 2
    :hidden:
    :includehidden:

    self
    Signal <signal/index>
    Filters <signal/filters/index>
    State Levels <signal/state_levels/index>
    Edges <signal/edges/index>
    Plotter <plotter/index>
    FAQ <faq/index>

.. toctree::
    :caption: Utils
    :maxdepth: 2
    :hidden:
    :includehidden:

    Signal Generator <signal/generator/index>
    Signals in Notebooks <signal/sample/index>
