from tricam.stereo_cameras import StereoGroup as StereoGroup
from tricam.stereo_cameras import ChessboardFinder as ChessboardFinder

devices = (1, 2, 3)
tricam = StereoGroup(devices)
tricam.show_videos()

# calibrator test
calib = ChessboardFinder(tricam)


# point cloud test
