import os.path
import sys
import config
import func
import video_parser
import thumnail_extraction
from mylogger import logger
from video_parser import *

from mylogger import logger
from crawler import craw_bilibili


def hecate(opt: config.HecateParams):
    logger.info(f'Hecate parameters: {opt}')

    parser = VideoParser()
    v_shot_range = parser.parse_video(opt)

    logger.debug(f'v_shot_range: {v_shot_range}')

    v_thumb_idx = thumnail_extraction.detect_thumbnail_frames(
        opt=opt, meta=parser.meta, v_shot_range=v_shot_range,
        feature=parser.feature, diff=parser.X_diff, chat_scores=parser.chat_scores)

    thumnail_extraction.generate_thumbnails(opt=opt, v_thumb_idx=v_thumb_idx)


if __name__ == '__main__':
    logger.setLevel('INFO')
    opt = config.HecateParams(sys.argv[1:])
    hecate(opt)
