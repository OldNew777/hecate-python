import cv2 as cv
import numpy as np
from tqdm import tqdm

def parse_video(path):
    video = cv.VideoCapture(path)
    if not video.isOpened():
        return None
    frame_list = []
    while True:
        ret, frame = video.read()
        if not ret:
            break
        frame_list.append(frame)
    video.release()
    return frame_list

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

def calc_uniformity(gray, num_bins = 256):
    hist = cv.calcHist([gray], [0], None, [num_bins], [0, 256])
    sorted = np.sort(hist, axis=0)[::-1, :]
    idx = int(num_bins * 0.05)
    return (sum(sorted[:idx, :]) / sum(sorted)).item()

def filter_low_quality(info_list, max_filter_percentage=0.15, threshold=[0.075, 0.08, 0.8]):
    sort_brightness = sorted(info_list, key=lambda item : item["brightness"])
    sort_sharpness = sorted(info_list, key=lambda item : item["sharpness"])
    sort_uniformity = sorted(info_list, key=lambda item : -item["uniformity"]) # max to min
    for i in range(int(len(info_list) * max_filter_percentage)):
        if sort_brightness[i]["brightness"] < threshold[0]:
            sort_brightness[i]["valid"] = False
            sort_brightness[i]["flag"] += "DARK "
        if sort_sharpness[i]["sharpness"] < threshold[1]:
            sort_sharpness[i]["valid"] = False
            sort_sharpness[i]["flag"] += "BLUR "
        if sort_uniformity[i]["uniformity"] > threshold[2]:
            sort_uniformity[i]["valid"] = False
            sort_uniformity[i]["flag"] += "UNIFORM "

def filter_transition(info_list, frame_list, max_filter_percentage=0.1, threshold=[0.5, 0,1]):
    img_size = frame_list[0].shape[0] * frame_list[0].shape[1]

    # compute the first-order derivative frame-by-frame difference
    v_diff = [0]
    for i in range(1, len(frame_list) - 1):
        v_diff.append(
            (cv.norm(frame_list[i] - frame_list[i - 1]) + cv.norm(frame_list[i + 1] - frame_list[i]))
            / (2. * img_size)
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
        rho_out = 1 - min(1, sum(sum(v_edge[i-1] * v_edge_dl[i]))) /  max(1e-6, sum(sum(v_edge[i-1])))
        rho_in = 1 - min(1, sum(sum(v_edge_dl[i-1] * v_edge[i]))) /  max(1e-6, sum(sum(v_edge[i-1])))

        v_ecr.append(max(rho_out, rho_in))

    # CUT detection
    sorted_cut = sorted(info_list, key=lambda item : -v_diff[item["id"]])
    for i in range(int(len(info_list) * max_filter_percentage)):
        if v_diff[sorted_cut[i]["id"]] >= threshold[0]:
            sorted_cut[i]["valid"] = False
            sorted_cut[i]["flag"] += "CUT "

    # TRANSITION detection (cut, fade, dissolve, wipe)
    sorted_transition = sorted(info_list, key=lambda item : v_ecr[item["id"]])
    for i in range(int(len(info_list) * max_filter_percentage)):
        if v_ecr[sorted_transition[i]["id"]] >= threshold[1]:
            sorted_transition[i]["valid"] = False
            sorted_transition[i]["flag"] += "ECR "


def parse_frame_info(frame_list):
    info_list = []
    for idx, bgr in enumerate(tqdm(frame_list)):
        gray = to_gray(bgr)

        info = {
            "id" : idx,
            "brightness" : calc_brightness(bgr),
            "sharpness" : calc_sharpness(gray),
            "uniformity" : calc_uniformity(gray),
            "valid" : True,
            "flag": "",
        }
        # print(info)

        info_list.append(info)
    return info_list
        
def debug_show_invalid(info_list):
    for item in info_list:
        if not item["valid"]:
            print(item)
            cv.imshow("2", frame_list[item["id"]])
            cv.waitKey()

def debug_show_certain_invalid(info_list, key):
    for item in info_list:
        if not item["valid"] and key in item["flag"]:
            print(item)
            cv.imshow("2", frame_list[item["id"]])
            cv.waitKey()

def debug_show_valid(info_list):
    for item in info_list:
        if item["valid"]:
            print(item)
            cv.imshow("2", frame_list[item["id"]])
            cv.waitKey()

if __name__ == "__main__":
    frame_list = parse_video("video.mp4")
    info_list = parse_frame_info(frame_list)
    filter_low_quality(info_list)
    filter_transition(info_list, frame_list)
    # debug_show_certain_invalid(info_list, "ECR")
    debug_show_valid(info_list)