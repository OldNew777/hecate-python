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

def parse_frame_info(frame_list):
    info_list = []
    for idx, bgr in enumerate(tqdm(frame_list)):
        gray = cv.cvtColor(bgr, cv.COLOR_BGR2GRAY)

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
        

if __name__ == "__main__":
    frame_list = parse_video("video.mp4")
    info_list = parse_frame_info(frame_list)
    filter_low_quality(info_list)
    # for item in info_list:
    #     if not item["valid"]:
    #         print(item)
    #         cv.imshow("2", frame_list[item["id"]])
    #         cv.waitKey()