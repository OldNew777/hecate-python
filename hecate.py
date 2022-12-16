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

    logger.info('Load video frames')
    frame_list = parse_video(opt.in_video)

    logger.info('Parse frames info')
    info_list = parse_frame_info(frame_list)

    logger.info('Filter low quality frames')
    filter_low_quality(info_list)

    logger.info('Filter transition')
    X_diff, X_ecr = filter_transition(info_list, frame_list)

    logger.info('Extract histo features')
    # feature = extract_histo_features(frame_list, info_list)

    logger.info('Post process')
    post_process(frame_list, info_list, X_diff)
    ranges = update_shot_range(frame_list, info_list, 40)

    logger.debug(ranges)

    # debug_show_certain_invalid(frame_list, info_list, "[GFL]")
    # debug_show_valid(frame_list, info_list)

    # logger.debug(feature.shape)
