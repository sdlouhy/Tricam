# NOTE: the from tricam.whatever is because of pycharm's weird environment 'features'.  In actual command line code,
#       this should be whatever file.

from tricam.stereo_cameras import StereoGroup as StereoGroup
from tricam.stereo_cameras import ChessboardFinder as ChessboardFinder
from tricam.calibration import StereoCalibration as StereoCalibration
from tricam.calibration import StereoCalibrator as StereoCalibrator
import numpy as np


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

reader = ChessboardFinder(tricam)

chess_finder = []

calibrator = StereoCalibrator(rows, cols, sq_sz, img_sz)

tricam.show_videos()
for device in devices:
    i = 0
    # does this while all cameras are running
    while i < num_img:
        # capture images here
        tricam.get_frames_singleimage()
        i += 1
        print(i + 1, "/", num_img, " complete")


for i in range(num_img):
    # match the chessboards for the pairs (1,2), (1, 3)
    # save the calibration to a file or smth
    reader.get_chessboard(cols, rows, show=True)
    chess_finder.append(i)
    print(i + 1, "/", num_img, " complete")

np.ndarray(chess_finder)
calib = StereoCalibration(chess_finder, calibration)
calibrator.check_calibration(calib)

calib.export("calibration")
# rectify
# display rectification

# point cloud test
# convert images to 3d using previously found values from rectification
