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

def parse_frame_info(frame_list):
    info_list = []
    for bgr in tqdm(frame_list):
        gray = cv.cvtColor(bgr, cv.COLOR_BGR2GRAY)

        info = {
            "brightness": calc_brightness(bgr),
            "sharpness": calc_sharpness(gray),
            "uniformity": calc_uniformity(gray)
        }
        # print(info)

        info_list.append(info)
        

if __name__ == "__main__":
    frame_list = parse_video("video.mp4")
    info_list = parse_frame_info(frame_list)