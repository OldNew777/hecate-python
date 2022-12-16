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
    v_shot_range = parser.parse_video(opt)

    logger.debug(f'v_shot_range: {v_shot_range}')

    # thumnail_extraction.detect_thumbnail_frames(
    #     opt=opt, meta=parser.meta, v_shot_range=v_shot_range, X=parser.X_ecr, diff=parser.X_diff)
