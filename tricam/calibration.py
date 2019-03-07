# Original code located at github.com/erget/StereoVision
# Modifications for a 3-headed collinear stereocam done by Sarah Dlouhy [smdwdk@mst.edu]
# Code originally licensed under the GNU General Public Use License.

"""
Classes for calibrating homemade stereo cameras.
Classes:
    * ``StereoCalibration`` - Calibration for stereo camera
    * ``StereoCalibrator`` - Class to calibrate stereo camera with
.. image:: classes_calibration.svg
"""

import os

import cv2

import numpy as np
from tricam.exceptions import ChessboardNotFoundError


class StereoCalibration(object):

    """
    A stereo camera calibration.
    The ``StereoCalibration`` stores the calibration for a stereo pair. It can
    also rectify pictures taken from its stereo pair.
    """

    def __str__(self):
        output = ""
        for key, item in self.__dict__.items():
            output += key + ":\n"
            output += str(item) + "\n"
        return output

    def _copy_calibration(self, calibration):
        """Copy another ``StereoCalibration`` object's values."""
        for key, item in calibration.__dict__.items():
            self.__dict__[key] = item

    def _interact_with_folder(self, output_folder, action):
        """
        Export/import matrices as *.npy files to/from an output folder.
        ``action`` is a string. It determines whether the method reads or writes
        to disk. It must have one of the following values: ('r', 'w').
        """
        if action not in ('r', 'w'):
            raise ValueError("action must be either 'r' or 'w'.")
        for key, item in self.__dict__.items():
            if isinstance(item, dict):
                for camera in ("left", "center", "right"):
                    filename = os.path.join(output_folder,
                                            "{}_{}.npy".format(key, camera))
                    if action == 'w':
                        np.save(filename, self.__dict__[key][camera])
                    else:
                        self.__dict__[key][camera] = np.load(filename)
            else:
                filename = os.path.join(output_folder, "{}.npy".format(key))
                if action == 'w':
                    np.save(filename, self.__dict__[key])
                else:
                    self.__dict__[key] = np.load(filename)

    def __init__(self, calibration=None, input_folder=None):
        """
        Initialize camera calibration.
        If another calibration object is provided, copy its values. If an input
        folder is provided, load ``*.npy`` files from that folder. An input
        folder overwrites a calibration object.
        """
        #: Camera matrices (M)
        self.cam_mats = {"left": None, "center": None, "right": None}
        #: Distortion coefficients (D)
        self.dist_coefs = {"left": None, "center": None, "right": None}
        #: Rotation matrix (R)
        self.rot_mat = None
        #: Translation vector (T)
        self.trans_vec = None
        #: Essential matrix (E)
        self.e_mat = None
        #: Fundamental matrix (F)
        self.f_mat = None
        #: Rectification transforms (3x3 rectification matrix R1 / R2)
        self.rect_trans = {"left": None, "center": None, "right": None}
        #: Projection matrices (3x4 projection matrix P1 / P2)
        self.proj_mats = {"left": None, "center": None, "right": None}
        #: Disparity to depth mapping matrix (4x4 matrix, Q)
        self.disp_to_depth_mat = None
        #: Bounding boxes of valid pixels
        self.valid_boxes = {"left": None, "center": None, "right": None}
        #: Undistortion maps for remapping
        self.undistortion_map = {"left": None, "center": None, "right": None}
        #: Rectification maps for remapping
        self.rectification_map = {"left": None, "center": None, "right": None}
        if calibration:
            self._copy_calibration(calibration)
        elif input_folder:
            self.load(input_folder)

    def load(self, input_folder):
        """Load values from ``*.npy`` files in ``input_folder``."""
        self._interact_with_folder(input_folder, 'r')

    def export(self, output_folder):
        """Export matrices as ``*.npy`` files to an output folder."""
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        self._interact_with_folder(output_folder, 'w')

    def rectify(self, frames):
        """
        Rectify frames passed as (left, right) pair of OpenCV Mats.
        Remapping is done with nearest neighbor for speed.
        """
        new_frames = []
        for i, cam in enumerate(("left", "center", "right")):
            new_frames.append(cv2.remap(frames[i],
                                        self.undistortion_map[cam],
                                        self.rectification_map[cam],
                                        cv2.INTER_NEAREST))
        return new_frames


class StereoCalibrator(object):

    """A class that calibrates stereo cameras by finding chessboard corners."""

    def _get_corners(self, image):
        """Find subpixel chessboard corners in image."""
        temp = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(temp,
                                                 (self.rows, self.columns))
        if not ret:
            raise ChessboardNotFoundError("No chessboard could be found.")
        cv2.cornerSubPix(temp, corners, (11, 11), (-1, -1),
                         (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS,
                          30, 0.01))
        return corners

    def _show_corners(self, image, corners):
        """Show chessboard corners found in image."""
        temp = image
        cv2.drawChessboardCorners(temp, (self.rows, self.columns), corners,
                                  True)
        window_name = "Chessboard"
        cv2.imshow(window_name, temp)
        if cv2.waitKey(0):
            cv2.destroyWindow(window_name)

    def __init__(self, rows, columns, square_size, image_size):
        """
        Store variables relevant to the camera calibration.
        ``corner_coordinates`` are generated by creating an array of 3D
        coordinates that correspond to the actual positions of the chessboard
        corners observed on a 2D plane in 3D space.
        """
        #: Number of calibration images
        self.image_count = 0
        #: Number of inside corners in the chessboard's rows
        self.rows = rows
        #: Number of inside corners in the chessboard's columns
        self.columns = columns
        #: Size of chessboard squares in cm
        self.square_size = square_size
        #: Size of calibration images in pixels
        self.image_size = image_size
        pattern_size = (self.rows, self.columns)
        corner_coordinates = np.zeros((np.prod(pattern_size), 3), np.float32)
        corner_coordinates[:, :2] = np.indices(pattern_size).T.reshape(-1, 2)
        corner_coordinates *= self.square_size
        #: Real world corner coordinates found in each image
        self.corner_coordinates = corner_coordinates
        #: Array of real world corner coordinates to match the corners found
        self.object_points = []
        #: Array of found corner coordinates from calibration images for left
        #: and right camera, respectively
        #: calibration only needs image points from left and right, not center
        self.image_points = {"left": [], "center": [], "right": []}

    def add_corners(self, image_group, show_results=False):
        """
        Record chessboard corners found in an image pair.
        The image pair should be an iterable composed of three CvMats ordered
        (left, right).  Only takes the image points of the outer cameras because the
        corners in both the left and right side should also be in the center.
        """
        side = "left"
        self.object_points.append(self.corner_coordinates)
        for image in image_group:
            corners = self._get_corners(image)
            if show_results:
                self._show_corners(image, corners)
            self.image_points[side].append(corners.reshape(-1, 2))
            side = "center"
            if show_results:
                self._show_corners(image, corners)
            self.image_points[side].append(corners.reshape(-1, 2))
            side = "right"
            self.image_count += 1

    # a megafunction to calibrate and rectify tricam
    def calibrate_cameras(self):
        """Calibrate cameras based on found chessboard corners."""
        criteria = (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS,
                    100, 1e-5)
        flags = (cv2.CALIB_FIX_ASPECT_RATIO + cv2.CALIB_ZERO_TANGENT_DIST +
                 cv2.CALIB_SAME_FOCAL_LENGTH)
        calib13 = StereoCalibration()
        (calib13.cam_mats["left"], calib13.dist_coefs["left"],
         calib13.cam_mats["right"], calib13.dist_coefs["right"],
         calib13.rot_mat, calib13.trans_vec, calib13.e_mat,
         calib13.f_mat) = cv2.stereoCalibrate(self.object_points,
                                              self.image_points["left"],
                                              self.image_points["right"],
                                              calib13.cam_mats["left"],
                                              calib13.dist_coefs["left"],
                                              calib13.cam_mats["right"],
                                              calib13.dist_coefs["right"],
                                              self.image_size,
                                              calib13.rot_mat,
                                              calib13.trans_vec,
                                              calib13.e_mat,
                                              calib13.f_mat,
                                              criteria=criteria,
                                              flags=flags)[1:]

        calib12 = StereoCalibration()
        (calib12.cam_mats["left"], calib12.dist_coefs["left"],
         calib12.cam_mats["center"], calib12.dist_coefs["center"],
         calib12.rot_mat, calib12.trans_vec, calib12.e_mat,
         calib12.f_mat) = cv2.stereoCalibrate(self.object_points,
                                              self.image_points["left"],
                                              self.image_points["center"],
                                              calib12.cam_mats["left"],
                                              calib12.dist_coefs["left"],
                                              calib12.cam_mats["center"],
                                              calib12.dist_coefs["center"],
                                              self.image_size,
                                              calib12.rot_mat,
                                              calib12.trans_vec,
                                              calib12.e_mat,
                                              calib12.f_mat,
                                              criteria=criteria,
                                              flags=flags)[1:]

        cerberus = StereoCalibration()
        alpha = 0
        cerberus.cam_mats["left"] = calib12.cam_mats["left"]
        cerberus.dist_coefs["left"] = calib12.dist_coefs["left"]
        cerberus.cam_mats["center"] = calib12.cam_mats["center"]
        cerberus.dist_coefs["center"] = calib12.dist_coefs["center"]
        cerberus.cam_mats["right"] = calib13.cam_mats["right"]
        cerberus.dist_coefs["right"] = calib13.dist_coefs["right"]

        (cerberus.rect_trans["left"], cerberus.rect_trans["center"], cerberus.rect_trans["right"],
         cerberus.proj_mats["left"], cerberus.proj_mats["center"], cerberus.proj_mats["right"],
         cerberus.disp_to_depth_mat, cerberus.valid_boxes["left"],
         cerberus.valid_boxes["right"]) = cv2.rectify3Collinear(cerberus.cam_mats["left"], cerberus.dist_coefs["left"],
                                                                cerberus.cam_mats["center"],
                                                                cerberus.dist_coefs["center"],
                                                                cerberus.cam_mats["right"],
                                                                cerberus.dist_coefs["right"], self.image_points["left"],
                                                                self.image_points["right"], self.image_size,
                                                                calib12.rot_mat, calib12.trans_vec, calib13.rot_mat,
                                                                calib13.trans_vec, alpha, self.image_size, flags=0)

        cerberus.f_mat = cv2.findFundamentalMat(self.image_points["left"], self.image_points["right"])

        for cam in ("left", "center", "right"):
                (cerberus.undistortion_map[cam],
                 cerberus.rectification_map[cam]) = cv2.initUndistortRectifyMap(
                    cerberus.cam_mats[cam],
                    cerberus.dist_coefs[cam],
                    cerberus.rect_trans[cam],
                    cerberus.proj_mats[cam],
                    self.image_size,
                    cv2.CV_32FC1)
        return cerberus

    def check_calibration(self, calibration):
        """
        Check calibration quality by computing average reprojection error.
        First, undistort detected points and compute epilines for each side.
        Then compute the error between the computed epipolar lines and the
        position of the points detected on the other side for each point and
        return the average error.
        """
        sides = ("left", "center", "right")
        which_image = {sides[0]: 1, sides[1]: 2, sides[2]: 3}
        undistorted, lines = {}, {}
        for side in sides:
            undistorted[side] = cv2.undistortPoints(
                         np.concatenate(self.image_points[side]).reshape(-1,
                                                                         1, 2),
                         calibration.cam_mats[side],
                         calibration.dist_coefs[side],
                         P=calibration.cam_mats[side])
            lines[side] = cv2.computeCorrespondEpilines(undistorted[side],
                                                        which_image[side],
                                                        calibration.f_mat)
        total_error = 0
        this_side, second_side, other_side = sides
        for side in sides:
            for i in range(len(undistorted[side])):
                total_error += abs(undistorted[this_side][i][0][0] *
                                   ((lines[other_side][i][0][0] +
                                    lines[second_side][i][0][0]) /
                                    (lines[other_side][i][0][0] *
                                    lines[second_side][i][0][0])) +
                                   undistorted[this_side][i][0][1] *
                                   ((lines[other_side][i][0][1] +
                                     lines[second_side][i][0][1]) /
                                    (lines[other_side][i][0][1] *
                                     lines[second_side][i][0][1])) +
                                   (((lines[other_side][i][0][2]) +
                                    lines[second_side][i][0][2]) /
                                    lines[other_side][i][0][2] *
                                    lines[second_side][i][0][2]))
            other_side, this_side, second_side = sides
        total_points = self.image_count * len(self.object_points)
        return total_error / total_points
