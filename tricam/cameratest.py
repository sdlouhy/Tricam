from tricam.stereo_cameras import StereoGroup as StereoGroup
from tricam.stereo_cameras import ChessboardFinder as ChessboardFinder
from tricam.calibration import StereoCalibration as StereoCalibration
from tricam.calibration import StereoCalibrator as StereoCalibrator
import cv2

devices = [1, 2, 3]
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


calibrator = StereoCalibrator(rows, cols, sq_sz, img_sz)

for i in range(num_img):
    reader = ChessboardFinder(tricam)
    chess_finder = ChessboardFinder.get_chessboard(reader, cols, rows, show=True)
    # match the chessboards for the pairs (1,2), (1, 3)
    # save the calibration to a file or smth
    print(i + 1, "/", num_img, " complete")
calib = StereoCalibration(chess_finder, calibration)
# rectify
# display rectification

# point cloud test
# convert images to 3d using previously found values from rectification
