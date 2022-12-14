import os.path
import shutil

import cv2
import sys
import numpy as np

import func
import config
from mylogger import logger


@func.time_it
def detect_thumbnail_frames(opt: config.HecateParams, meta: config.VideoMetadata, v_shot_range: list,
                            feature: np.ndarray, diff: np.ndarray, chat_scores: np.ndarray) -> list:
    v_thumb_idx = []

    minK = 5
    maxK = 30
    nfrm = meta.nframes

    v_frm_valid = [False] * nfrm
    for i in range(len(v_shot_range)):
        for j in range(len(v_shot_range[i].v_idx)):
            v_frm_valid[v_shot_range[i].v_idx[j]] = True

    def score_func(index: int) -> float:
        # return func.mat_at(diff, index)                                                 # stillness
        # return (1.0 - chat_scores[index]) * opt.chat_alpha                              # chat
        return func.mat_at(diff, index) + (1.0 - chat_scores[index]) * opt.chat_alpha   # stillness + chat

    nfrm_valid = sum(v_frm_valid)
    if nfrm_valid == 0:
        # If there's no valid frame, pick one most still/chat frame
        min_idx = -1
        min_val = sys.float_info.max
        for i in range(nfrm):
            val = score_func(i)
            if val < min_val:
                min_val = val
                min_idx = i
        logger.debug(f'No valid frame, pick most still/chat frame: {min_idx}, value = {min_val}')
        v_thumb_idx.append(min_idx)
    elif nfrm_valid <= opt.njpg:
        # If not enough frames are left,
        # include all remaining keyframes sorted by shot length
        v_shot_len = []
        v_keyfrm_idx = []
        for i in range(len(v_shot_range)):
            max_subshot_id = -1
            max_subshot_len = -1
            for j in range(len(v_shot_range[i].v_range)):
                shotlen = v_shot_range[i].v_range[j].length()
                if shotlen > max_subshot_len:
                    max_subshot_id = j
                    max_subshot_len = shotlen
            v_shot_len.append(max_subshot_len)
            v_keyfrm_idx.append(v_shot_range[i].v_range[max_subshot_id].v_idx[0])

        # Include keyframes sorted by shot length
        _, v_srt_idx = func.hecate_sort(v_shot_len)     # sorted indices/values
        len_idx = len(v_srt_idx)
        for i in range(len_idx):
            v_thumb_idx.append(v_keyfrm_idx[v_srt_idx[len_idx - 1 - i]])
    else:
        v_valid_frm_idx = []
        v_valid_frm_shotlen = []
        for i in range(len(v_shot_range)):
            for j in range(len(v_shot_range[i].v_range)):
                v_valid_frm_idx.append(v_shot_range[i].v_range[j].v_idx[0])
                v_valid_frm_shotlen.append(v_shot_range[i].v_range[j].length())
        # logger.debug(f'v_valid_frm_idx: {len(v_valid_frm_idx)} {v_valid_frm_idx}')

        km_data = np.zeros(shape=(nfrm_valid, feature.shape[1]), dtype=feature.dtype)
        for i in range(len(v_valid_frm_idx)):
            km_data[i] = feature[v_valid_frm_idx[i]].copy()

        km_k = min(maxK, min(nfrm_valid, max(minK, opt.njpg)))
        km_lbl, km_ctr = func.perform_kmeans(km_data, km_k, opt.njpg)

        clust_sz = [0] * km_k
        for i in range(km_lbl.shape[0]):
            clust_sz[func.mat_at(km_lbl, i)] += v_valid_frm_shotlen[i]

        _, v_srt_idx = func.hecate_sort(clust_sz)   # sorted indices/values

        # obtain thumbnails -- the most still frame per cluster
        for i in range(km_k):
            min_idx = -1
            min_val = sys.float_info.max
            for j in range(km_lbl.shape[0]):
                if func.mat_at(km_lbl, j) == v_srt_idx[km_k - 1 - i]:
                    val = score_func(v_valid_frm_idx[j])
                    if val < min_val:
                        min_idx = j
                        min_val = val
            # logger.debug(f'v_valid_frm_idx[min_idx]')
            # logger.debug(f'v_valid_frm_idx[{min_idx}]')
            # logger.debug(f'{v_valid_frm_idx[min_idx]}')
            v_thumb_idx.append(v_valid_frm_idx[min_idx])

    return v_thumb_idx


@func.time_it
def generate_thumbnails(opt: config.HecateParams, v_thumb_idx: list) -> None:
    njpg_count = 0
    frame_index = 0

    out_dir = os.path.join(opt.out_dir, 'thumbnails')
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    video = cv2.VideoCapture(opt.video_file)
    assert video.isOpened(), 'Cannot capture source'
    while njpg_count < len(v_thumb_idx):
        ret, frame = video.read()
        if not ret:
            break
        rank = -1
        for i in range(len(v_thumb_idx)):
            if frame_index == v_thumb_idx[i]:
                rank = i
                break
        if 0 <= rank < opt.njpg:
            cv2.imwrite(os.path.join(out_dir, f'{rank}.jpg'), frame)
            njpg_count += 1
        if njpg_count >= opt.njpg:
            break
        frame_index += 1
    video.release()
