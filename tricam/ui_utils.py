# Original code located at github.com/erget/StereoVision
# Modifications for a 3-headed collinear stereocam done by Sarah Dlouhy [smdwdk@mst.edu]
# Code originally licensed under the GNU General Public Use License.

"""
Utilities for easing user interaction with the ``tricam`` package.

Variables:

    * ``CHESSBOARD_ARGUMENTS`` - ``argparse.ArgumentParser`` for working with
      chessboards
    * ``STEREO_BM_FLAG`` - ``argparse.ArgumentParser`` for using StereoBM

Functions:

    * ``find_files`` - Discover stereo images in directory
    * ``calibrate_folder`` - Calibrate chessboard images discoverd in a folder

Classes:

    * ``BMTuner`` - Tune block matching algorithm to camera pair

.. image:: classes_ui_utils.svg
"""

from argparse import ArgumentParser
from functools import partial
import os

import cv2
from progressbar import ProgressBar, Percentage, Bar
from tricam.calibration import StereoCalibrator
from tricam.exceptions import BadBlockMatcherArgumentError

#: Command line arguments for collecting information about chessboards
CHESSBOARD_ARGUMENTS = ArgumentParser(add_help=False)
CHESSBOARD_ARGUMENTS.add_argument("--rows", type=int,
                                  help="Number of inside corners in the "
                                  "chessboard's rows.", default=9)
CHESSBOARD_ARGUMENTS.add_argument("--columns", type=int,
                                  help="Number of inside corners in the "
                                  "chessboard's columns.", default=6)
CHESSBOARD_ARGUMENTS.add_argument("--square-size", help="Size of chessboard "
                                  "squares in cm.", type=float, default=1.8)


#: Command line arguments for using StereoBM rather than StereoSGBM
STEREO_BM_FLAG = ArgumentParser(add_help=False)
STEREO_BM_FLAG.add_argument("--use_stereobm", help="Use StereoBM rather than "
                            "StereoSGBM block matcher.", action="store_true")


# TODO: fix this to work with three camera file searching
def find_files(folder):
    """Discover stereo photos and return them as a pairwise sorted list."""
    files = [i for i in os.listdir(folder) if i.startswith("left")]
    files.sort()
    for i in range(len(files)):
        insert_string = "center{}".format(files[i * 2][4:])
        files.insert(i * 2 + 1, insert_string)
    for i in range(len(files)):
        insert_string = "right{}".format(files[i * 2][4:])
        files.insert(i * 2 + 1, insert_string)
    files = [os.path.join(folder, filename) for filename in files]
    return files


def calibrate_folder(args):
    """
    Calibrate camera based on chessboard images, write results to output folder.

    All images are read from disk. Chessboard points are found and used to
    calibrate the stereo pair. Finally, the calibration is written to the folder
    specified in ``args``.

    ``args`` needs to contain the following fields:
        input_files: List of paths to input files
        rows: Number of rows in chessboard
        columns: Number of columns in chessboard
        square_size: Size of chessboard squares in cm
        output_folder: Folder to write calibration to
    """
    height, width = cv2.imread(args.input_files[0]).shape[:2]
    calibrator = StereoCalibrator(args.rows, args.columns, args.square_size,
                                  (width, height))
    progress = ProgressBar(maxval=len(args.input_files),
                           widgets=[Bar("=", "[", "]"),
                           " ", Percentage()])
    print("Reading input files...")
    progress.start()
    while args.input_files:
        left, right = args.input_files[:2]
        img_left, im_right = cv2.imread(left), cv2.imread(right)
        calibrator.add_corners((img_left, im_right),
                               show_results=args.show_chessboards)
        args.input_files = args.input_files[2:]
        progress.update(progress.max_value - len(args.input_files))

    progress.finish()
    print("Calibrating cameras. This can take a while.")
    calibration = calibrator.calibrate_cameras()
    avg_error = calibrator.check_calibration(calibration)
    print("The average error between chessboard points and their epipolar "
          "lines is \n"
          "{} pixels. This should be as small as possible.".format(avg_error))
    calibration.export(args.output_folder)


class BMTuner(object):

    """
    A class for tuning Stereo BM settings.

    Display a normalized disparity picture from two pictures captured with a
    ``CalibratedPair`` and allow the user to manually tune the settings for the
    ``BlockMatcher``.

    The settable parameters are intelligently read from the ``BlockMatcher``,
    relying on the ``BlockMatcher`` exposing them as ``parameter_maxima``.
    """

    #: Window to show results in
    window_name = "BM Tuner"

    def _set_value(self, parameter, new_value):
        """Try setting new parameter on ``block_matcher`` and update map."""
        try:
            self.block_matcher.__setattr__(parameter, new_value)
        except BadBlockMatcherArgumentError:
            return
        self.update_disparity_map()

    def _initialize_trackbars(self):
        """
        Initialize trackbars by discovering ``block_matcher``'s parameters.
        """
        for parameter in self.block_matcher.parameter_maxima.keys():
            maximum = self.block_matcher.parameter_maxima[parameter]
            if not maximum:
                maximum = self.shortest_dimension
            cv2.createTrackbar(parameter, self.window_name,
                               self.block_matcher.__getattribute__(parameter),
                               maximum,
                               partial(self._set_value, parameter))

    def _save_bm_state(self):
        """Save current state of ``block_matcher``."""
        for parameter in self.block_matcher.parameter_maxima.keys():
            self.bm_settings[parameter].append(
                               self.block_matcher.__getattribute__(parameter))

    def __init__(self, block_matcher, calibration, image_group):
        """
        Initialize tuner window and tune given pair.

        ``block_matcher`` is a ``BlockMatcher``, ``calibration`` is a
        ``StereoCalibration`` and ``image_pair`` is a rectified image pair.
        """
        #: Stereo calibration to find Stereo BM settings for
        self.calibration = calibration
        #: (left, right) image pair to find disparity between
        self.group = image_group
        #: Block matcher to be tuned
        self.block_matcher = block_matcher
        #: Shortest dimension of image
        self.shortest_dimension = min(self.group[0].shape[:2])
        #: Settings chosen for ``BlockMatcher``
        self.bm_settings = {}
        for parameter in self.block_matcher.parameter_maxima.keys():
            self.bm_settings[parameter] = []
        cv2.namedWindow(self.window_name)
        self._initialize_trackbars()
        self.tune_group(image_group)

    def update_disparity_map(self):
        """
        Update disparity map in GUI.

        The disparity image is normalized to the range 0-255 and then divided by
        255, because OpenCV multiplies it by 255 when displaying. This is
        because the pixels are stored as floating points.
        """
        disparity = self.block_matcher.get_disparity(self.group)
        norm_coeff = 255 / disparity.max()
        cv2.imshow(self.window_name, disparity * norm_coeff / 255)
        cv2.waitKey()

    def tune_group(self, group):
        """Tune a pair of images."""
        self._save_bm_state()
        self.group = group
        self.update_disparity_map()

    def report_settings(self, parameter):
        """
        Report chosen settings for ``parameter`` in ``block_matcher``.

        ``bm_settings`` is updated to include the latest state before work is
        begun. This state is removed at the end so that the method has no side
        effects. All settings are reported except for the first one on record,
        which is ``block_matcher``'s default setting.
        """
        self._save_bm_state()
        report = []
        settings_list = self.bm_settings[parameter][1:]
        unique_values = list(set(settings_list))
        value_frequency = {}
        for value in unique_values:
            value_frequency[settings_list.count(value)] = value
        frequencies = value_frequency.keys()
        frequencies.sort(reverse=True)
        header = "{} value | Selection frequency".format(parameter)
        left_column_width = len(header[:-21])
        right_column_width = 21
        report.append(header)
        report.append("{}|{}".format("-" * left_column_width,
                                     "-" * right_column_width,))
        for frequency in frequencies:
            left_column = str(value_frequency[frequency]).center(
                                                             left_column_width)
            right_column = str(frequency).center(right_column_width)
            report.append("{}|{}".format(left_column, right_column))
        # Remove newest settings
        for param in self.block_matcher.parameter_maxima.keys():
            self.bm_settings[param].pop(-1)
        return "\n".join(report)
