from argparse import ArgumentParser
import os


class HecateParams:
    def __init__(self, args):
        optparser = ArgumentParser()
        optparser.add_argument('-i', '--in_video', action='store', dest='in_video', default='video.mp4',
                               help='Input video file')
        optparser.add_argument('-o', '--out_dir', action='store', dest='out_dir', default='./outputs',
                               help='Output directory')
        optparser.add_argument('-s', '--step_sz', action='store', dest='step_sz', default=1,
                               help='Step size for frame subsampling')
        optparser.add_argument('-n', '--njpg', action='store', dest='njpg', default=5,
                               help='Number of thumbnails to be generated')
        optparser.add_argument('--invalid_wnd', action='store', dest='invalid_wnd', default=0.15,
                               help='Window for dropping neighbor frames of low-quality ones (seconds)')
        opt = optparser.parse_args(args)

        self.in_video = os.path.relpath(opt.in_video)
        self.out_dir = os.path.relpath(opt.out_dir)
        self.step_sz = int(opt.step_sz)
        self.njpg = int(opt.njpg)
        self.invalid_wnd = float(opt.invalid_wnd)

        self.chat_window = (-3.0, 7.0)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class VideoMetadata:
    def __init__(self, width: int, height: int, fps: float, nframes: int):
        self.width = width
        self.height = height
        self.fps = fps
        self.nframes = nframes
        self.duration = nframes / fps

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
