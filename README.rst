**dataArtist** - *…scientific data processing made easy.*

.. image:: https://img.shields.io/badge/License-GPLv3-red.svg
.. image:: https://img.shields.io/badge/python-3.5-blue.svg

`Download for Windows 7-10 and Linux`_


|screenshot|

About
-----

| *dataArtist* is a graphical program for interactive data analysis and
  processing. It is currently specialized image processing tasks in
  combination with electroluminescence imaging of photovoltaic devices.
| It is written in Python (3.x) and is released under open source.
| *dataArtist* is written to be platform independent. It is known to run
  under Windows 7-10 and Ubuntu Linux 14.10 (soon).

**Please cite *dataArtist* as follows:**

    K.G. Bedrich et al., "Electroluminescence Imaging of PV Devices:
    Camera Calibration and Image Correction", Proc. 43rd IEEE Photovoltaic Specialists Conference, Portland, 2016.


Manuals
-------

`USER manual`_

`DEVELOPERS manual`_

Online Tutorials
----------------

| General usage, camera calibration and image correction are explained
  in youtube screencast sessions, see
| |youtube|

Supported file types
--------------------

Data is imported through drag n’drop.

#. Images

-  Common used (TIF, BMP, PNG, JPG, CSV, TXT, MAT, CR2, FIT)
-  RAW, if data type and image shape are known
-  Numpy arrays

#. Plots

-  CSV, TXT, numpy arrays

Installation
------------

a) Portable version
~~~~~~~~~~~~~~~~~~~

-  *dataArtist* runs out of the box. No installation needed (currently
   Windows only). See section `Releases`_.


b) Installation into existing Python installation using pip
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- After installing Python3.x and ensuring that 'pip' is a recognised command in the command shell (Windows: CMD.exe).
  you need to install the following packages BEFORE installing dataArtist:
  
    - PyQt5 
    - OpenCV3.1
    - OPTIONAL: RabbitMQ (for inter-program communication)

-  Best use anaconda as Python environment. It comes with numba, scipy and
   many more packages, that might be painful to install by hand.
   Please refer to the `USER manual`_ for more information.
-  Once these packages are installed, open a command shell and type:

``pip install dataArtist``

- Now start dataArtist from the command shell:

``dataArtist``

- To launch dataArtist into the system tray type:

``dataArtist -s``

- To open a dataArtist session directly type:

``dataArtist -o /path/to/my/session.da``


Scripting, Automation, Modding
------------------------------

| *dataArtist* comes with a built-in python shell. Data can be examplary
  accessed though ``d1.l3`` (display 1, data layer 3) and tools
  e.g. through ``d.tools['Axes'].click()`` (in current display execute
  tool ‘Axes’).
| *dataArtist* allows adding own tools, displays and importers, for
  examples, see dataArtist/modding.

Main dependencies
-----------------

+----------------------+----------------------------------------------------------+
| Package              | Description                                              |
+======================+==========================================================+
| `pyqtgraph\_karl`_   | Scientific Graphics and GUI Library based on Qt (Fork)   |
+----------------------+----------------------------------------------------------+
| `imgProcessor`_      | General propose image processing libary                  |
+----------------------+----------------------------------------------------------+
| `appBase`_           | Base packages for apps, based on Qt                      |
+----------------------+----------------------------------------------------------+
| `fancyWidgets`_      | A collection of fancy widgets, based on Qt               |
+----------------------+----------------------------------------------------------+
| `fancyTools`_        | A collection of useful not-GUI tools                     |
+----------------------+----------------------------------------------------------+

Example: Electroluminescence imaging
------------------------------------

Camera calibration
~~~~~~~~~~~~~~~~~~

For camera calibration all needed images are dropped into *dataArtist*
and the matching tool is executed. The calibration results are
hereinafter saved to a calibration file. The determination of the
point spread function is exemplary shown in the following figure:

|screenshotpsf|

    dataArtist screenshot - toolbar ‘calibration’. **a**: Best focus
    determination; **b**: noise-level-function measurement; **c**: Dark
    current mapping; **d**: Flat field mapping; **e**: PSF estimation
    (selected): **f**: lens distortion measurement

Image correction
~~~~~~~~~~~~~~~~

The correction of EL image is shown in the following figure.
Perspective correction (red box) can be done either using the outline
of the PV device (automatically detected or manually defined) or using
a reference image.

|screenshotcorrection|

    | dataArtist screenshot - **a**: tool ‘CalibrationFile’; **b**: tool
      ‘CorrectCamera’; **c**: tool ‘PerspectiveCorrection’
    | **green line**: Camera correction; **red line**: Perspective
      correction





.. |screenshot| image:: https://cloud.githubusercontent.com/assets/350050/15406631/806a7a8a-1dc4-11e6-9e76-709cd482857f.png
.. |screenshotpsf| image:: https://cloud.githubusercontent.com/assets/350050/15404653/bd2e51b6-1dbb-11e6-8282-2ea539f0286d.png
.. |screenshotcorrection| image:: https://cloud.githubusercontent.com/assets/350050/15404785/53d4c992-1dbc-11e6-93b7-c6108ab9a2b0.png
.. _Download for Windows 7-10 and Linux: https://github.com/radjkarl/dataArtist/releases/
.. _USER manual: https://github.com/radjkarl/dataArtist/raw/master/dataArtist/media/USER_MANUAL.pdf
.. _DEVELOPERS manual: http://radjkarl.github.io/dataArtist/
.. _Releases: https://github.com/radjkarl/dataArtist/releases
.. _pyqtgraph\_karl: https://github.com/radjkarl/pyqtgraph_karl
.. _imgProcessor: https://github.com/radjkarl/imgProcessor
.. _appBase: https://github.com/radjkarl/appBase
.. _fancyWidgets: https://github.com/radjkarl/fancyWidgets
.. _fancyTools: https://github.com/radjkarl/fancyTools

.. |youtube| image:: https://cloud.githubusercontent.com/assets/350050/15802145/a8eaac4c-2a66-11e6-865d-4c77c306acc9.png
   :target: https://https://www.youtube.com/playlist?list=PLKyzYL-Q8RckIHJuR0godQA0eQpkABBbb
