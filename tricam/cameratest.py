from tricam.stereo_cameras import StereoGroup as StereoGroup
from tricam.stereo_cameras import ChessboardFinder as ChessboardFinder
from tricam.calibration import StereoCalibration as StereoCalibration
from tricam.calibration import StereoCalibrator as StereoCalibrator
import cv2

devices = (1, 2, 3)
tricam = StereoGroup(devices)
# 5tricam.show_videos()

# calibrator test
num_img = int(input("enter number of images"))
cols = 9
rows = 6
# reader = ChessboardFinder(tricam)
# calib = ChessboardFinder.get_chessboard(reader, cols, rows, show=False)
for i in range(num_img):
    # something happens here
    print(i + 1, "/", num_img)


# point cloud test
