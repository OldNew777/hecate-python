import cv2
import numpy as np


def reorder(sorted_l: list, index_map: list) -> list:
    size = len(sorted_l)
    ordered = [0] * size
    for i in range(size):
        ordered[i] = sorted_l[index_map[i]]
    return ordered


def hecate_sort(unsorted: list) -> (list, list):
    size = len(unsorted)
    index_map = [0] * size
    for i in range(size):
        index_map[i] = i
    # sort array unsorted and output its right index_map
    unsorted.sort(key=lambda index: unsorted[index])
    return reorder(unsorted, index_map), index_map
