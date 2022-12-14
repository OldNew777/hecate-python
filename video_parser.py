import os.path

import cv2 as cv
import numpy as np
from tqdm import tqdm
import sys
import json

import config
import func
from mylogger import logger


class Range:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.v_idx = []

    def length(self):
        return len(self)

    def __len__(self):
        return self.end - self.start + 1

    def _to_string(self):
        text_list = [f'[{self.start}, {self.end}] size={len(self)}']
        if len(self.v_idx) > 0:
            text_list.append(f' v_idx={self.v_idx}')
        return ''.join(text_list)

    def __str__(self):
        return 'Range ' + self._to_string()

    def __repr__(self):
        return self.__str__()


class ShotRange(Range):
    def __init__(self, start, end):
        super().__init__(start, end)
        self.v_range = []

    def __str__(self):
        text_list = ['ShotRange ', self._to_string()]
        for subrange in self.v_range:
            text_list.append(f' Sub-')
            text_list.append(str(subrange))
        return ''.join(text_list)

    def __repr__(self):
        return self.__str__()


class FrameInfo:
    def __init__(self, id, brightness, sharpness, uniformity):
        self.id = id
        self.brightness = brightness
        self.sharpness = sharpness
        self.uniformity = uniformity
        self.valid = True
        self.flag = ""

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"[{self.id}][{self.valid}] B: {self.brightness}, S: {self.sharpness}, U:{self.uniformity}, F: {self.flag}"


def to_gray(bgr):
    gray = cv.cvtColor(bgr, cv.COLOR_BGR2GRAY)
    gray = cv.GaussianBlur(gray, (3, 3), 0)
    return gray


def calc_brightness(bgr):
    illu = 0.2126 * bgr[:, :, 2] + 0.7152 * bgr[:, :, 1] + 0.0722 * bgr[:, :, 0]
    illu /= 255
    illu = np.mean(illu)
    return illu


def calc_sharpness(gray):
    g = gray / 255.
    dx = cv.Sobel(g, -1, 1, 0, ksize=3)
    dy = cv.Sobel(g, -1, 0, 1, ksize=3)
    sharp = cv.magnitude(dx, dy)
    sharp = np.mean(sharp)
    return sharp


def calc_uniformity(gray, num_bins=256):
    hist = cv.calcHist([gray], [0], None, [num_bins], [0, 256])
    sorted = np.sort(hist, axis=0)[::-1, :]
    idx = int(num_bins * 0.05)
    return (sum(sorted[:idx, :]) / sum(sorted)).item()


def calc_hsv_hist(img, nbins=128):
    cvt = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    planes = cv.split(cvt)

    hist0 = cv.calcHist(planes[0:1], [0], None, [nbins], [0, 256])
    hist1 = cv.calcHist(planes[1:2], [0], None, [nbins], [0, 256])
    hist2 = cv.calcHist(planes[2:3], [0], None, [nbins], [0, 256])

    cv.normalize(hist0, hist0)
    cv.normalize(hist1, hist1)
    cv.normalize(hist2, hist2)

    hist = np.concatenate([hist0, hist1, hist2])
    return hist


def orientation(gx, gy):
    alpha = 180.0 / 3.14159265358979323846264338327950288419716939937510

    # ori = np.zeros(gx.shape[0:2], dtype=np.float32)
    # for r in range(gx.shape[0]):
    #     for c in range(gx.shape[1]):
    #         deg = np.arctan2(gy[r, c], gx[r, c]) * alpha
    #         deg = deg if deg >= 0 else deg + 360
    #         deg = deg if deg < 180 else deg - 180
    #         ori[r, c] = deg

    ori = np.arctan2(gy, gx) * alpha
    ori[ori < 0] += 360
    ori[ori >= 180] -= 180

    return ori


def calc_egde_hist_g(gx, gy, nbins_ori=16, nbins_mag=16):
    _range_ori = [0, 180]
    _range_mag = [0, 256]

    ori = orientation(gx, gy)
    mag = cv.magnitude(gx, gy)

    hist_ori = cv.calcHist([ori], [0], None, [nbins_ori], _range_ori)
    hist_mag = cv.calcHist([mag], [0], None, [nbins_mag], _range_mag)

    cv.normalize(hist_ori, hist_ori)
    cv.normalize(hist_mag, hist_mag)

    return np.concatenate([hist_ori, hist_mag])


def calc_egde_hist(gray, nbins_ori=16, nbins_mag=16):
    gx = cv.Scharr(gray, cv.CV_32F, 1, 0)
    gy = cv.Scharr(gray, cv.CV_32F, 0, 1)

    return calc_egde_hist_g(gx, gy, nbins_ori, nbins_mag)


def calc_pyr_color_hist(img, nbins=128, level=2):
    h, w, _ = img.shape
    npatches = 0
    for i in range(level):
        npatches += 4 ** i

    hist_sz = 3 * nbins

    hist = np.ndarray([hist_sz * npatches, 1], np.float32)

    patch = 0
    for l in range(level):
        for x in range(2 ** l):
            for y in range(2 ** l):
                p_width = int(np.floor(w / 2 ** l))
                p_height = int(np.floor(h / 2 ** l))
                p_x = x * p_width
                p_y = y * p_height
                patch_img = img[p_y:p_y + p_height, p_x:p_x + p_width]
                patch_hist = calc_hsv_hist(patch_img, nbins)
                hist[hist_sz * patch:hist_sz * patch + hist_sz] = patch_hist
                patch += 1

    return hist


def calc_pyr_edge_hist(img, nbins_ori=16, nbins_mag=16, level=2):
    h, w = img.shape  # gray
    npatches = 0
    for i in range(level):
        npatches += 4 ** i

    hist_sz = nbins_ori + nbins_mag

    hist = np.ndarray([hist_sz * npatches, 1], dtype=np.float32)

    patch = 0
    for l in range(level):
        for x in range(2 ** l):
            for y in range(2 ** l):
                p_width = int(np.floor(w / 2 ** l))
                p_height = int(np.floor(h / 2 ** l))
                p_x = x * p_width
                p_y = y * p_height
                patch_img = img[p_y:p_y + p_height, p_x:p_x + p_width]
                patch_hist = calc_egde_hist(patch_img, nbins_ori, nbins_mag)
                hist[hist_sz * patch:hist_sz * patch + hist_sz] = patch_hist
                patch += 1

    return hist


def calc_pyr_edge_hist_g(gx, gy, nbins_ori=16, nbins_mag=16, level=2):
    h, w, _ = gx.shape
    npatches = 0
    for i in range(level):
        npatches += 4 ** i

    hist_sz = nbins_ori + nbins_mag

    hist = np.ndarray([hist_sz * npatches, 1], dtype=np.float32)

    patch = 0
    for l in range(level):
        for x in range(2 ** l):
            for y in range(2 ** l):
                p_width = int(np.floor(w / 2 ** l))
                p_height = int(np.floor(h / 2 ** l))
                p_x = x * p_width
                p_y = y * p_height
                patch_gx = gx[p_y:p_y + p_height, p_x:p_x + p_width]
                patch_gy = gy[p_y:p_y + p_height, p_x:p_x + p_width]
                patch_hist = calc_egde_hist_g(patch_gx, patch_gy, nbins_ori, nbins_mag)
                hist[hist_sz * patch:hist_sz * patch + hist_sz] = patch_hist
                patch += 1

    return hist


def sbd_heuristic(v_diff, njumps, min_shot_len):
    jump = []
    sorted_v_idx = [i for i in range(len(v_diff))]
    sorted_v_idx = sorted(sorted_v_idx, key=lambda id: v_diff[id])
    sorted_v_diff = sorted(v_diff)
    for i in range(len(sorted_v_diff) - 1, -1, -1):
        add = True
        if sorted_v_idx[i] + 1 < min_shot_len or len(v_diff) - sorted_v_idx[i] < min_shot_len:
            add = False
        else:
            for j in range(len(jump)):
                length = abs(jump[j] - sorted_v_idx[i]) + 1
                if length < min_shot_len:
                    add = False
                    break
        if add:
            jump.append(sorted_v_idx[i])
        if len(jump) == njumps:
            break
    return jump


class VideoParser:
    def __init__(self):
        self.chat_scores = None
        self.opt = None
        self.frame_list = None
        self.info_list = None
        self.ranges = None
        self.feature = None
        self.X_ecr = None
        self.X_diff = None
        self.meta = None

    @func.time_it
    def parse_video(self, opt: config.HecateParams):
        self.opt = opt
        self.init(opt.video_file)
        # frame_len = len(self.frame_list)
        # if frame_len > 20000:
        #     logger.warning("More than 20000 frames, only first 20000 frames will be kept.")
        #     self.frame_list = self.frame_list[0:20000]
        self.parse_frame_info()
        self.filter_low_quality()
        self.filter_transition()
        self.extract_histo_features()
        self.post_process()
        self.update_shot_range(40)
        self.filter_redundant_and_obtain_subshots()

        return self.ranges

    @func.time_it
    def init(self, path):
        video = cv.VideoCapture(path)
        assert video.isOpened(), 'Cannot capture source'

        logger.info(f'OpenCV version: {cv.__version__}')
        (major_ver, minor_ver, subminor_ver) = (cv.__version__).split('.')
        if int(major_ver) < 3:
            nframes = video.get(cv.cv.CV_CAP_PROP_FRAME_COUNT)
            fps = video.get(cv.cv.CV_CAP_PROP_FPS)
            width = int(video.get(cv.cv.CAP_PROP_FRAME_WIDTH))
            height = int(video.get(cv.cv.CAP_PROP_FRAME_HEIGHT))
        else:
            nframes = int(video.get(cv.CAP_PROP_FRAME_COUNT))
            fps = video.get(cv.CAP_PROP_FPS)
            width = int(video.get(cv.CAP_PROP_FRAME_WIDTH))
            height = int(video.get(cv.CAP_PROP_FRAME_HEIGHT))
        self.meta = config.VideoMetadata(width=width, height=height, fps=fps, nframes=nframes)
        logger.info(f'Video metadata: {self.meta}')

        self.frame_list = []
        while True:
            ret, frame = video.read()
            if not ret:
                break
            self.frame_list.append(frame)
        video.release()

    @func.time_it
    def filter_low_quality(self, max_filter_percentage=0.15, threshold=[0.075, 0.08, 0.8]):
        info_list = self.info_list
        sort_brightness = sorted(info_list, key=lambda item: item.brightness)
        sort_sharpness = sorted(info_list, key=lambda item: item.sharpness)
        sort_uniformity = sorted(info_list, key=lambda item: -item.uniformity)  # max to min
        for i in range(int(len(info_list) * max_filter_percentage)):
            if sort_brightness[i].brightness < threshold[0]:
                sort_brightness[i].valid = False
                sort_brightness[i].flag += "DARK "
            if sort_sharpness[i].sharpness < threshold[1]:
                sort_sharpness[i].valid = False
                sort_sharpness[i].flag += "BLUR "
            if sort_uniformity[i].uniformity > threshold[2]:
                sort_uniformity[i].valid = False
                sort_uniformity[i].flag += "UNIFORM "

    @func.time_it
    def filter_transition(self, max_filter_percentage=0.1, threshold=[0.5, 0, 1]):
        info_list = self.info_list
        frame_list = self.frame_list
        img_size = frame_list[0].shape[0] * frame_list[0].shape[1]

        # compute the first-order derivative frame-by-frame difference
        v_diff = [0]
        for i in range(1, len(frame_list) - 1):
            v_diff.append(
                (cv.norm(frame_list[i] - frame_list[i - 1]) +
                 cv.norm(frame_list[i + 1] - frame_list[i])) / (2. * img_size)
            )
        v_diff.append(0)

        # compute edge-change-ratio (ECR)
        dl_sz = 5
        dl_elm = cv.getStructuringElement(cv.MORPH_CROSS, (2 * dl_sz + 1, 2 * dl_sz + 1), (dl_sz, dl_sz))

        # Pre-compute edge & edge dilation
        v_edge = []
        v_edge_dl = []
        for i in range(len(frame_list)):
            gray = to_gray(frame_list[i])
            theta = cv.threshold(gray, 0, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)[0]
            v_edge.append(cv.Canny(gray, theta, 1.2 * theta))
            v_edge_dl.append(cv.dilate(v_edge[i], dl_elm))
            v_edge[i] -= 254
            v_edge_dl[i] -= 254

        # Transition detection using ECR (edge change ratio)
        v_ecr = []
        for i in range(len(frame_list)):
            rho_out = 1 - min(1, sum(sum(v_edge[i - 1] * v_edge_dl[i]))) / max(1e-6, sum(sum(v_edge[i - 1])))
            rho_in = 1 - min(1, sum(sum(v_edge_dl[i - 1] * v_edge[i]))) / max(1e-6, sum(sum(v_edge[i - 1])))

            v_ecr.append(max(rho_out, rho_in))

        # CUT detection
        sorted_cut = sorted(info_list, key=lambda item: -v_diff[item.id])
        for i in range(int(len(info_list) * max_filter_percentage)):
            if v_diff[sorted_cut[i].id] >= threshold[0]:
                sorted_cut[i].valid = False
                sorted_cut[i].flag += "CUT "

        # TRANSITION detection (cut, fade, dissolve, wipe)
        sorted_transition = sorted(info_list, key=lambda item: v_ecr[item.id])
        for i in range(int(len(info_list) * max_filter_percentage)):
            if v_ecr[sorted_transition[i].id] >= threshold[1]:
                sorted_transition[i].valid = False
                sorted_transition[i].flag += "ECR "

        self.X_diff = np.array(v_diff).reshape([len(v_diff), 1])
        self.X_ecr = np.array(v_ecr).reshape([len(v_ecr), 1])
        return self.X_diff, self.X_ecr

    @func.time_it
    def extract_histo_features(self, pyr_level=2, omit_filtered=True, nbins_color=128,
                               nbins_edge_ori=8, nbins_edge_mag=8):
        frame_list = self.frame_list
        info_list = self.info_list
        npatches = 0
        for i in range(pyr_level):
            npatches += 4 ** i

        nbins_edge = nbins_edge_mag + nbins_edge_ori
        color_hist = np.zeros([npatches * 3 * nbins_color, len(frame_list)], dtype=np.float32)
        edge_hist = np.zeros([npatches * nbins_edge, len(frame_list)], dtype=np.float32)

        for i in tqdm(range(len(frame_list)), desc="Extracting histo features"):
            if omit_filtered and not info_list[i].valid:
                continue

            color_hist[:, i] = calc_pyr_color_hist(frame_list[i], nbins_color, pyr_level)[:, 0]
            edge_hist[:, i] = calc_pyr_edge_hist(
                to_gray(frame_list[i]), nbins_edge_ori, nbins_edge_mag, pyr_level)[:, 0]

        color_hist = color_hist.T
        edge_hist = edge_hist.T

        self.feature = np.concatenate([color_hist, edge_hist], axis=1)
        logger.info(f"Feature shape: {self.feature.shape}")
        return self.feature

    @func.time_it
    def post_process(self, min_shot_len=40):  # no gfl
        frame_list = self.frame_list
        info_list = self.info_list
        X_diff = self.X_diff

        start_idx = -1
        end_idx = -1
        shotlen = -1
        max_shot_len = min_shot_len * 3

        for i in tqdm(range(len(frame_list)), desc="Post process"):
            if start_idx < 0 and info_list[i].valid:
                start_idx = i
            if start_idx >= 0 and (not info_list[i].valid or i + 1 == len(frame_list)):
                end_idx = i
                shotlen = end_idx - start_idx + 1
                if shotlen >= max_shot_len:
                    njumps = int(np.floor(shotlen / min_shot_len))
                    v_diff = X_diff[start_idx:end_idx + 1]
                    jump = sbd_heuristic(v_diff, njumps, min_shot_len)
                    # logger.debug(start_idx, end_idx, jump)
                    for k in range(len(jump)):
                        info_list[start_idx + jump[k] - 1].valid = False
                        info_list[start_idx + jump[k] - 1].flag += "[GFL] "

                start_idx = -1
                end_idx = -1

    @func.time_it
    def filter_redundant_and_obtain_subshots(self):
        valid_frame = [item for id, item in enumerate(self.frame_list) if self.info_list[id].valid]
        nfrm_valid = len(valid_frame)
        if nfrm_valid == 0:
            return

        km_data = np.ndarray([nfrm_valid, self.feature.shape[1]], dtype=self.feature.dtype)
        v_idxmap = np.zeros([nfrm_valid], dtype=int)

        row = 0
        for i in range(len(self.frame_list)):
            if self.info_list[i].valid:
                km_data[row] = np.copy(self.feature[row])
                v_idxmap[row] = i
                row += 1

        # print(km_data.shape)
        # print(self.feature.shape)
        # print(np.max(km_data))
        # print(np.min(km_data))
        ncluster = min(nfrm_valid // 2, len(self.ranges))
        km_lbl, km_ctr = func.perform_kmeans(km_data, ncluster)

        v_frm_clusterid = -np.ones(len(self.frame_list))
        for i in range(km_lbl.shape[0]):
            v_frm_clusterid[v_idxmap[i]] = km_lbl[i]

        for shotid, shot in enumerate(self.ranges):
            sb0 = shot.start
            sb1 = shot.end

            ssb0 = -1
            ssb1 = -1
            lbl = -1
            for j in range(sb0, sb1 + 1):
                if self.info_list[j].valid:
                    if ssb0 < 0:
                        ssb0 = j
                        lbl = v_frm_clusterid[j]
                    ssb1 = j
                if ssb0 >= 0 and (v_frm_clusterid[j] != lbl or j == sb1):
                    diff_min_idx = -1
                    diff_min_val = sys.float_info.max
                    for k in range(ssb0, ssb1 + 1):
                        diff_k = self.X_diff[k]
                        if diff_k < diff_min_val:
                            diff_min_idx = k
                            diff_min_val = diff_k

                    r = Range(ssb0, ssb1)
                    r.v_idx.append(diff_min_idx)
                    self.ranges[shotid].v_idx.append(diff_min_idx)
                    self.ranges[shotid].v_range.append(r)

                    for k in range(ssb0, ssb1 + 1):
                        if k != diff_min_idx:
                            self.info_list[k].valid = False
                            self.info_list[k].flag += "[Redundant] "

                    ssb0 = ssb1 = lbl = -1
            sb0 = sb1 = -1

    def update_shot_range(self, min_shot_len):
        frame_list = self.frame_list
        info_list = self.info_list
        ranges = []
        sb0 = sb1 = -1
        for i in range(len(frame_list)):
            if info_list[i].valid:
                if sb0 < 0:
                    sb0 = i
                sb1 = i

            if sb0 >= 0 and sb1 >= 0 and (not info_list[i].valid or i + 1 == len(frame_list)):
                # logger.debug(sb0, sb1)
                if sb1 - sb0 + 1 > min_shot_len:
                    ranges.append(ShotRange(sb0, sb1))
                else:
                    for j in range(sb0, sb1 + 1):
                        info_list[j].valid = False
                        info_list[j].flag += "SHORT "
                sb0 = sb1 = -1
        self.ranges = ranges
        return ranges

    @func.time_it
    def parse_frame_info(self):
        frame_list = self.frame_list
        info_list = []
        for idx, bgr in enumerate(tqdm(frame_list, desc="Parse frame info")):
            gray = to_gray(bgr)

            info = FrameInfo(
                idx,
                calc_brightness(bgr),
                calc_sharpness(gray),
                calc_uniformity(gray)
            )
            # logger.debug(info)

            info_list.append(info)
        self.info_list = info_list

        # compute screen chat scores
        assert len(frame_list) == self.meta.nframes
        chat_window = (int(-self.meta.fps * self.opt.chat_window[1]),
                       int(-self.meta.fps * self.opt.chat_window[0]))    # reverse here to transform from frame view to chat view
        chat_pdf = np.zeros(shape=(chat_window[1] - chat_window[0]), dtype=np.float32)
        for i in range(chat_window[0], 0):
            chat_pdf[i] = func.regularized_gaussian_distribution_0_1(i / chat_window[0])
        for i in range(0, chat_window[1]):
            chat_pdf[i] = func.regularized_gaussian_distribution_0_1(i / chat_window[1])
        chat_pdf = func.normalize_pdf(chat_pdf)
        pdf_indexes = [0] * len(frame_list)
        pdf_index = 1
        chat_pdfs = [chat_pdf]
        for i in tqdm(range(self.meta.nframes), 'Init chat pdf'):
            if i + chat_window[0] < 0 or i + chat_window[1] >= self.meta.nframes:
                chat_pdf_new = chat_pdf.copy()
                for j in range(chat_window[0], chat_window[1]):
                    if i + j < 0 or i + j >= self.meta.nframes:
                        chat_pdf_new[j] = 0.0
                chat_pdf_new = func.normalize_pdf(chat_pdf_new)
                chat_pdfs.append(chat_pdf_new)
                pdf_indexes[i] = pdf_index
                pdf_index += 1
            else:
                pdf_indexes[i] = 0

        with open(os.path.join(os.path.dirname(self.opt.video_file), 'chat.json'), 'r', encoding='utf-8') as f:
            chats = json.load(f)
        chat_scores = np.zeros(shape=(len(frame_list)), dtype=np.float32)
        for chat in tqdm(chats, 'Compute chat scores'):
            chat_frame_index = min(int(chat['time'] * self.meta.fps + 0.5), self.meta.nframes - 1)
            # logger.debug(f'{chat_frame_index}: {chat["text"]}')
            chat_pdf = chat_pdfs[pdf_indexes[chat_frame_index]]
            for i in range(max(chat_window[0], -chat_frame_index), min(chat_window[1], self.meta.nframes - chat_frame_index)):
                chat_scores[chat_frame_index + i] += chat_pdf[i]
        self.chat_scores = chat_scores / np.max(chat_scores)

        # max_index = np.argmax(chat_scores)
        # logger.debug(f'chat_scores: {chat_scores.shape}, {chat_scores[max_index]}')
        # cv.imshow(f'Highest chat score: frame {max_index}', frame_list[max_index])
        # cv.waitKey(0)

        return info_list

    def debug_show_invalid(self):
        info_list = self.info_list
        frame_list = self.frame_list
        for item in info_list:
            if not item.valid:
                logger.debug(item)
                cv.imshow(f"Invalid {item.id}", frame_list[item.id])
                cv.waitKey()

    def debug_show_certain_invalid(self, key):
        info_list = self.info_list
        frame_list = self.frame_list
        for item in info_list:
            if not item.valid and key in item.flag:
                logger.debug(item)
                cv.imshow(f"Invalid {item.id}", frame_list[item.id])
                cv.waitKey()

    def debug_show_valid(self):
        info_list = self.info_list
        frame_list = self.frame_list
        for item in info_list:
            if item.valid:
                logger.debug(item)
                cv.imshow(f"Valid {item.id}", frame_list[item.id])
                cv.waitKey()

    def debug_show_ranges(self):
        for sr in self.ranges:
            for idx in sr.v_idx:
                logger.debug(self.info_list[idx])
                cv.imshow(f"Range selected {idx}", self.frame_list[idx])
                cv.waitKey()
                cv.destroyWindow(f"Range selected {idx}")