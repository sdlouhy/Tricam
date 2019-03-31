# Original code located at github.com/erget/StereoVision
# Modifications for a 3-headed collinear stereocam done by Sarah Dlouhy [smdwdk@mst.edu]
# Code originally licensed under the GNU General Public Use License.

"""
Classes for interacting with stereo cameras.

Classes:

    * ``StereoGroup`` - Base class for interacting with stereo cameras

        * ``ChessboardFinder`` - Class for finding chessboards with all three cameras
        * ``CalibratedGroup`` - Calibrated stereo camera pair that rectifies its
          images

.. image:: classes_stereo_cameras.svg
"""

import cv2

from tricam.point_cloud import PointCloud


class StereoGroup(object):

    """
    A stereo group of cameras.

    This class allows all cameras in a stereo group to be accessed
    simultaneously. It also allows the user to show single frames or videos
    captured online with the cameras. It should be instantiated with a context
    manager to ensure that the cameras are freed properly after use.
    """

    #: Window names for showing captured frame from each camera
    windows = ["{} camera".format(side) for side in ("Left", "Center", "Right")]

    def __init__(self, devices):
        """
        Initialize cameras.

        ``devices`` is an iterable containing the device numbers.
        """
        #: Video captures associated with the ``StereoGroup``
        self.captures = [cv2.VideoCapture(device) for device in devices]

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        for capture in self.captures:
            capture.release()
        for window in self.windows:
            cv2.destroyWindow(window)

    def get_frames(self):
        """Get current frames from cameras."""
        return [capture.read() for capture in self.captures]

    def get_frames_singleimage(self):
        """
        Get current left and right frames from a single image,
        by splitting the image in half.
        """
        frame = self.captures[0].read()[1, 2]
        height, width, colors = frame.shape
        left_frame = frame[:, :width/3, :]
        center_frame = frame[:, width/3: 2*width/3, :]
        right_frame = frame[:, 2*width/3:, :]
        return [left_frame, center_frame, right_frame]

    def show_frames(self, wait=0):
        """
        Show current frames from cameras.

        ``wait`` is the wait interval in milliseconds before the window closes.
        """
        for window, frame in zip(self.windows, self.get_frames()):
            cv2.imshow(window, frame)
        cv2.waitKey(wait)

    def show_videos(self):
        """Show video from cameras."""
        while True:
            self.show_frames(1)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        raise StopIteration()


class ChessboardFinder(StereoGroup):

    """A ``StereoGroup`` that can find chessboards in its images."""

    def get_chessboard(self, columns, rows, show=False):
        """
        Take a picture with a chessboard visible in all three captures.

        ``columns`` and ``rows`` should be the number of inside corners in the
        chessboard's columns and rows. ``show`` determines whether the frames
        are shown while the cameras search for a chessboard.
        """
        found_chessboard = [False, False, False]
        while not all(found_chessboard):
            frames = self.get_frames()
            if show:
                self.show_frames(1)
            for i, frame in enumerate(frames):
                (found_chessboard[i],
                 corners) = cv2.findChessboardCorners(frame, (columns, rows),
                                                      flags=cv2.CALIB_CB_FAST_CHECK)
            return frames


class CalibratedGroup(StereoGroup):

    """
    A ``StereoGroup`` that works with rectified images and produces point clouds.
    """

    def __init__(self, devices, calibration, block_matcher):
        """
        Initialize cameras.

        ``devices`` is an iterable of the device numbers. If you want to use the
        ``CalibratedPair`` in offline mode, it should be None.
        ``calibration`` is a ``StereoCalibration`` object.
        ``block_matcher`` is a ``BlockMatcher`` object.
        """
        if devices:
            super(CalibratedGroup, self).__init__(devices)
        #: ``StereoCalibration`` object holding the camera group's calibration
        self.calibration = calibration
        #: ``BlockMatcher`` object for computing disparity and point cloud
        self.block_matcher = block_matcher

    def get_frames(self):
        """Rectify and return current frames from cameras."""
        frames = super(CalibratedGroup, self).get_frames()
        return self.calibration.rectify(frames)

    def get_point_cloud(self, group):
        """Get 3D point cloud from image pair."""
        disparity = self.block_matcher.get_disparity(group)
        points = self.block_matcher.get_3d(disparity,
                                           self.calibration.disp_to_depth_mat)
        colors = cv2.cvtColor(group[0], cv2.COLOR_BGR2RGB)
        return PointCloud(points, colors)
