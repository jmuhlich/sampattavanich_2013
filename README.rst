Requirements
============

* OMERO Python bindings -- see installation instructions here:
  http://www.openmicroscopy.org/site/support/omero4/developers/Python.html
* Python packages: PIL
* ffmpeg with libx264 support (configure --enable-libx264)

Usage
=====

1. Set the ``OMERO_PREFIX`` environment variable to point to your unpacked
   OMERO.server directory.

2. Add ``$OMERO_PREFIX/lib/python`` to your ``PYTHONPATH``.

3. Run ``extract.py`` to download the individual movie frames from the OMERO
   server as JPEG files. If interrupted, it will pick up where it left off
   instead of starting over from the beginning. 26GB of disk space is required
   to store the individual JPEG files, which are placed in the ``frames``
   directory.

4. Run ``render.py``. A further 2GB of disk space is required for processed JPEG
   files (placed in ``frames/*/processed``), and 100MB for final rendered MP4
   files (placed in ``movies``). All CPU cores will be utilized. If interrupted,
   it will start over from the beginning.
