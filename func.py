import cv2
import numpy as np
from typing import Tuple
import time
from mylogger import logger


def time_it(func):
    def wrapper(*args, **kwargs):
        logger.info(f'Running {func.__name__}...')
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info(f"Time taken by {func.__name__} is {end - start:.04f} seconds")
        return result
    return wrapper


def reorder(sorted_l: list, index_map: list) -> list:
    size = len(sorted_l)
    ordered = [0] * size
    for i in range(size):
        ordered[i] = sorted_l[index_map[i]]
    return ordered


def hecate_sort(unsorted: list) -> Tuple[list, list]:
    size = len(unsorted)
    index_map = [0] * size
    for i in range(size):
        index_map[i] = i
    # sort array unsorted and output its right index_map
    unsorted.sort(key=lambda index: unsorted[index])
    return reorder(unsorted, index_map), index_map


def perform_kmeans(km_data: np.ndarray, ncluster: int, km_attempts: int = 1,
                   km_max_cnt: int = 1000, km_eps: float = 0.0001) -> Tuple[np.ndarray, np.ndarray]:
    km_lbl = np.zeros(shape=(1, 1), dtype=np.int32)
    km_ctr = np.zeros(shape=(1, 1), dtype=np.float32)
    if km_data.shape[0] == 1:
        cv2.reduce(src=km_data, dim=0, rtype=cv2.REDUCE_AVG, dst=km_ctr)
    else:
        km_k = min(ncluster, km_data.shape[0])
        km_opt = (cv2.TermCriteria_MAX_ITER | cv2.TermCriteria_EPS, km_max_cnt, km_eps)
        cv2.kmeans(data=km_data, K=km_k, bestLabels=km_lbl, criteria=km_opt,
                   attempts=km_attempts, flags=cv2.KMEANS_PP_CENTERS, centers=km_ctr)

    return km_lbl, km_ctr


def mat_at(a: np.ndarray, index: int):
    return a[index // a.shape[1], index % a.shape[1]]
