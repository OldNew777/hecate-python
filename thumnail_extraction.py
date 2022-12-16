import cv2
import sys
import numpy as np

import func


def detect_thumbnail_frames(opt, meta, v_shot_range,
                            X: np.ndarray, diff: np.ndarray, v_thumb_idx: list):
    v_thumb_idx.clear()

    minK = 5
    maxK = 30
    nfrm = meta.nframes

    v_frm_valid = [False] * nfrm
    for i in range(len(v_shot_range)):
        for j in range(len(v_shot_range[i].v_idx)):
            v_frm_valid[v_shot_range[i].v_idx[j]] = True

    nfrm_valid = sum(v_frm_valid)
    if nfrm_valid <= 1:
        # If there's no valid frame, pick one most still frame
        minidx = -1
        minval = sys.float_info.max
        for i in range(nfrm):
            val = diff[i]
            if val < minval:
                minval = val
                minidx = i
        v_thumb_idx.append(minidx)
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
        v_srt_val, v_srt_idx = func.hecate_sort(v_shot_len) # sorted sorted indices/values
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

        # km_data = np.zeros(shape=(nfrm_valid, X.shape[1], dtype=X.dtype))
        # X.dtype
