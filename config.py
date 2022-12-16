from optparse import OptionParser


class HecateParams:
    def __init__(self, args):
        optparser = OptionParser()
        optparser.add_option('-i', '--in_video', action='store', dest='in_video', default='video.mp4',
                             help='Input video file')
        optparser.add_option('-o', '--out_dir', action='store', dest='out_dir', default='./outputs',
                             help='Output directory')
        optparser.add_option('-s', '--step_sz', action='store', dest='step_sz', default=1,
                             help='Step size for frame subsampling')
        optparser.add_option('-n', '--njpg', action='store', dest='njpg', default=5,
                             help='Number of thumbnails to be generated')
        optparser.add_option('--invalid_wnd', action='store', dest='invalid_wnd', default=0.15,
                             help='Window for dropping neighbor frames of low-quality ones (seconds)')
        opt = optparser.parse_args(args)[0]

        self.in_video = opt.in_video
        self.out_dir = opt.out_dir
        self.step_sz = int(opt.step_sz)
        self.njpg = int(opt.njpg)
        self.invalid_wnd = float(opt.invalid_wnd)

    def __str__(self):
        return str(self.__dict__)
