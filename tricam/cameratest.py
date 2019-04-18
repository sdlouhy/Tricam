# NOTE: the from tricam.whatever is because of pycharm's weird environment 'features'.  In actual command line code,
#       this should be whatever file.

from tricam.stereo_cameras import StereoGroup as StereoGroup
from tricam.calibration import StereoCalibration as StereoCalibration
from tricam.calibration import StereoCalibrator as StereoCalibrator
import numpy as np
import cv2
import os
from progressbar import ProgressBar, Bar, Percentage


devices = (1, 2, 3)
tricam = StereoGroup(devices)
# this is for just displaying cameras
# tricam.show_videos()

# calibrator test section
num_img = int(input("enter number of images: "))
calibration = None
cols = 9
rows = 6
# size of squares in cm
sq_sz = 2.5
# size of calibrated image in pixels, 640 * 480
img_sz = 307200

chess_finder = []

calibrator = StereoCalibrator(rows, cols, sq_sz, img_sz)

progress = ProgressBar(maxval=num_img,
                       widgets=[Bar("=", "[", "]"), " ", Percentage()])

tricam.show_videos()
for device in devices:
    # does this while all cameras are running
    for i in range(num_img):
        frames = tricam.get_chessboard(cols, rows, True)
        for side, frame in zip(("left", "center", "right"), frames):
            number_string = str(i + 1).zfill(len(str(num_img)))
            filename = "{}_{}.ppm".format(side, number_string)
            chess_finder.append()
            cv2.imwrite(chess_finder, frame)
        progress.update(progress.max_value - (num_img - i))
        for j in range(10):
            tricam.show_frames(1)
    progress.finish()

np.ndarray(chess_finder)
calib = StereoCalibration(chess_finder, calibration)
calibrator.check_calibration(calib)

calib.export("calibration")
# rectify
# display rectification

# point cloud test
# convert images to 3d using previously found values from rectification
