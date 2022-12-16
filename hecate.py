import os.path
import sys
import config
import func
import video_parser
import thumnail_extraction
from mylogger import logger
from video_parser import *

if __name__ == '__main__':
    args = sys.argv
    opt = config.HecateParams(args)
    logger.info(f'Hecate parameters: {opt}')

    parser = VideoParser()
    ranges = parser.parse_video(opt.in_video)

    logger.debug(f'ranges: {ranges}')
