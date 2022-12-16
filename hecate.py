import sys
import config
import video_parser
import thumnail_extraction

if __name__ == '__main__':
    args = sys.argv
    opt = config.HecateParams(args)
    print(opt)
