Signal Edges
------------------------------------------------------------------------------------------------------------------------

**Signal Edges** is a Python package capable of filtering, extracting state levels and edges of signals with millions
of samples, among other things. It is specially suited for analysis of analog signals obtained through recorders, such
as oscilloscopes or data recorders, and hardware automation in CI/CD environments, although it is flexible enough to
be used for many other different purposes.

.. figure:: https://github.com/dmg0345/python-signal-edges/blob/master/doc/.assets/img/007_example_complex_plot_1.png
    :align: center

Find **Signal Edges** on `PyPi <https://pypi.org/project/python-signal-edges/>`_, or install it as follows:

.. code-block::

    pip install python-signal-edges

Refer to the documentation `here <https://dmg0345-python-signal-edges.netlify.app/>`_ for more details.

Development
------------------------------------------------------------------------------------------------------------------------

Clone the repository as:

.. code-block:: powershell

    git clone https://github.com/dmg0345/python-signal-edges

Ensure the *Github* file with the relevant environment variables exist as expected in the *compose.yaml* file and the
correct paths are set in the *manage.ps1* file for your environment. Afterwards, find the base Docker image for the
development container at `DockerHub <https://hub.docker.com/r/dmg00345/python_signal_edges>`_.

To develop using `devcontainers` and `Visual Studio Code`:

.. code-block:: powershell

    docker pull dmg00345/python_signal_edges:latest
    ./manage.ps1 run

Create a release
------------------------------------------------------------------------------------------------------------------------

To generate a release follow the steps below:

1. Create a ``release`` branch from ``develop`` branch, e.g. ``release/X.Y.Z``.
2. Update version in *conf.py* file and in *pyproject.toml* file.
3. Create pull request from ``release`` branch to ``master`` with the changes with title *Release X.Y.Z*.
4. When merged in ``master`` create release and tag from *Github*, review production workflow passes for deployment.
5. Delete the ``release/X.Y.Z`` branch.
