# Original code located at github.com/erget/StereoVision
# Modifications for a 3-headed collinear stereocam done by Sarah Dlouhy [smdwdk@mst.edu]
# Code originally licensed under the GNU General Public Use License.
from setuptools import setup

setup(name="TriCam",
      version="1.0.0",
      description=("Library and utilities for 3d reconstruction from stereo "
                   "cameras."),
      long_description=open("README.rst").read(),
      author="Daniel Lee",
      author_email="lee.daniel.1986@gmail.com",
      packages=["stereovision"],
      scripts=["bin/calibrate_cameras",
               "bin/capture_chessboards",
               "bin/images_to_pointcloud",
               "bin/show_webcams",
               "bin/tune_blockmatcher"],
      url="http://erget.sdlouhy.com/Tricam",
      download_url="http://pypi.python.org/pypi/TriCam",
      license="GNU GPL",
      requires=["cv2",
                "simplejson",
                "numpy",
                "progressbar"],
      provides=["stereovision"],
      classifiers=["Development Status :: 5 - Production/Stable",
                   "Natural Language :: English",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python :: 3",
                   "Intended Audience :: Developers",
                   "Intended Audience :: Education",
                   "Intended Audience :: Science/Research",
                   "License :: Freely Distributable",
                   "License :: OSI Approved :: GNU General Public License v3 "
                   "or later (GPLv3+)",
                   "Natural Language :: English",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python :: 3.6",
                   "Topic :: Multimedia :: Graphics :: Capture"])
