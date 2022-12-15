import requests
from bs4 import BeautifulSoup
import json
import os
import shutil
import re
from you_get import common

import config


def craw_cover_chat(bv: str, output_dir: os.path) -> None:
    """
    :param bv: bv to crawl
    :param output_dir: directory to save the crawled data
    :return: None
    """

    r = requests.get(url=f'https://www.ibilibili.com/video/{bv}', headers=config.get_headers())
    soup = BeautifulSoup(r.text, 'lxml')

    def find_url(soup: BeautifulSoup, text: str) -> str:
        node = soup.find_all(name='span', attrs={'class': 'input-group-addon'}, text=text, recursive=True)
        assert len(node) == 1
        node = node[0]
        return node.parent.input.get('value')

    # download video cover
    cover_url = find_url(soup, '视频图片:')
    cover = requests.get(url=cover_url, headers=config.get_headers()).content
    cover_suffix = cover_url.split('.')[-1]
    with open(os.path.join(output_dir, f'cover.{cover_suffix}'), 'wb') as f:
        f.write(cover)

    # download video chat and save it as a json file
    chat_url = find_url(soup, '弹幕地址:')
    chat = requests.get(url=chat_url, headers=config.get_headers()).content
    soup = BeautifulSoup(chat, 'lxml', from_encoding='utf-8')
    chat_nodes = soup.find_all(name='d', recursive=True)
    chat_list = []
    for chat_node in chat_nodes:
        attributes = chat_node.get('p').split(',')
        chat_text = chat_node.text
        chat_time = float(attributes[0])
        chat_send_time = int(attributes[4])
        chat_list.append({
            'text': chat_text,
            'time': chat_time,
            'send_time': chat_send_time
        })
    with open(os.path.join(output_dir, 'chat.json'), 'w', encoding='utf-8') as f:
        json.dump(chat_list, f, ensure_ascii=False, indent=4)


def remkchilddir(root_dir: os.path, name: str) -> os.path:
    output_dir = os.path.join(root_dir, name)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)
    return output_dir


def craw_video(bv: str, output_root_dir: os.path) -> None:
    output_dir = remkchilddir(output_root_dir, bv)

    # download video
    common.any_download(url=f'https://www.bilibili.com/video/{bv}', output_dir=output_dir, merge=True, info_only=False,
                        stream_id='dash-flv360')

    # download video cover and chat
    craw_cover_chat(bv=bv, output_dir=output_dir)
    # rename the video file
    video_files = [f for f in os.listdir(output_dir) if f.endswith('.mp4')]
    assert len(video_files) == 1
    video_file = video_files[0]
    os.rename(os.path.join(output_dir, video_file), os.path.join(output_dir, f'video.mp4'))


def download_video_series(series_number: int, output_root_dir: os.path) -> None:
    raise NotImplementedError

    temp_dir = remkchilddir(output_root_dir, 'temp')

    url = f'https://www.bilibili.com/bangumi/play/ss{series_number}'
    r = requests.get(url=url, headers=config.get_headers())
    soup = BeautifulSoup(r.text, 'lxml')

    # with open(os.path.join(temp_dir, 'origin.html'), 'w', encoding='utf-8') as f:
    #     f.write(r.text)
    # with open(os.path.join(temp_dir, 'processed.html'), 'w', encoding='utf-8') as f:
    #     f.write(soup.prettify())

    # FIXME: episode numbers are loaded dynamically with javascript
    href_nodes = soup.find_all(name='a', attrs={
        'href': re.compile(r'^/bangumi/play/ep\d+/$'),
    }, recursive=True)
    ep_list = [node.get('href') for node in href_nodes]
    n = len(ep_list)

    print(f'Found {n} episodes in series {series_number}')
    for href in ep_list:
        print(href)
    exit(0)

    # # download video
    # common.any_download_playlist(url=f'https://www.bilibili.com/bangumi/play/ss{series_number}', output_dir=temp_dir,
    #                              merge=True, info_only=False, stream_id='dash-flv360')

    # video_files = [f for f in os.listdir(temp_dir) if f.endswith('.mp4')]
    # video_files.sort()
    # assert n == len(video_files)
    for i in range(n):
        pattern = f'第{i + 1}'
        # if re.search(pattern, video_files[i]) is None:
        #     raise ValueError(f'video file {video_files[i]} does not match the pattern {pattern}')
        output_dir = remkchilddir(output_root_dir, f'ss{series_number}-{i + 1}')

        # # rename the video file
        # os.rename(os.path.join(temp_dir, video_files[i]), os.path.join(output_dir, f'video.mp4'))

        # download video cover and chat
        craw_cover_chat(bv=f'ss{series_number}-{i + 1}', output_dir=output_dir)

    shutil.rmtree(temp_dir)


if __name__ == '__main__':
    output_root_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dataset')
    if not os.path.exists(output_root_dir):
        os.mkdir(output_root_dir)

    # bv = 'BV138411L7Ze'
    # craw_video(bv, output_root_dir)

    # # not implemented
    # series_number = 357
    # download_video_series(series_number, output_root_dir)
