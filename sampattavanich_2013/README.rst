Requirements
============

* OMERO Python bindings -- see installation instructions here:
  http://www.openmicroscopy.org/site/support/omero4/developers/Python.html
* Python packages: PIL
* ffmpeg with libx264 support (configure --enable-libx264)
* qt-faststart from libav-tools

Usage
=====

1. Add the OMERO Python source directory (``lib/python`` inside the OMERO.py or
   OMERO.server directory) to your ``PYTHONPATH``.

2. Run ``extract.py`` to download the individual movie frames from the OMERO
   server as JPEG files. If interrupted, it will pick up where it left off
   instead of starting over from the beginning. 26GB of disk space is required
   to store the individual JPEG files, which are placed in the ``frames``
   directory.

3. Run ``render.py``. A further 2GB of disk space is required for processed JPEG
   files and 100-200MB for final rendered MP4 files (all placed in
   ``frames/*/render``). Up to 4 CPU cores will be utilized. If interrupted, it
   will start over from the beginning.
