from tricam.stereo_cameras import StereoGroup as StereoGroup

devices = (1, 2, 3)
tricam = StereoGroup(devices)
tricam.show_videos()
