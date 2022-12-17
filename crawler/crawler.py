import sys

import requests
from bs4 import BeautifulSoup
import json
import os
import shutil
import re
from you_get import common
from argparse import ArgumentParser

import config
from mylogger import logger


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
    cover_suffix = cover_url.split('.')[-1]
    cover_path = os.path.join(output_dir, f'cover.{cover_suffix}')
    if not os.path.exists(cover_path):
        cover = requests.get(url=cover_url, headers=config.get_headers()).content
        with open(cover_path, 'wb') as f:
            f.write(cover)

    # download video chat and save it as a json file
    chat_url = find_url(soup, '弹幕地址:')
    chat_path = os.path.join(output_dir, 'chat.json')
    if not os.path.exists(chat_path):
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
        with open(chat_path, 'w', encoding='utf-8') as f:
            json.dump(chat_list, f, ensure_ascii=False, indent=4)


def check_dir(root_dir: os.path, name: str = None) -> os.path:
    output_dir = root_dir
    if name is not None:
        output_dir = os.path.join(output_dir, name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir


def craw_video(bv: str, output_root_dir: os.path, overwrite=False) -> None:
    output_dir = check_dir(output_root_dir, bv)
    video_path = os.path.join(output_dir, f'video.mp4')

    if not os.path.exists(video_path) or overwrite:
        # download video
        common.any_download(url=f'https://www.bilibili.com/video/{bv}', output_dir=output_dir, merge=True,
                            info_only=False,
                            stream_id='dash-flv360')
        # rename the video file
        video_files = [f for f in os.listdir(output_dir) if f.endswith('.mp4')]
        assert len(video_files) == 1
        video_file = video_files[0]
        os.rename(os.path.join(output_dir, video_file), video_path)

    # download video cover and chat
    craw_cover_chat(bv=bv, output_dir=output_dir)


def download_video_series(series_number: int, output_root_dir: os.path) -> None:
    raise NotImplementedError

    temp_dir = check_dir(output_root_dir, 'temp')

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

    logger.info(f'Found {n} episodes in series {series_number}')
    for href in ep_list:
        logger.info(href)
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
        output_dir = check_dir(output_root_dir, f'ss{series_number}-{i + 1}')

        # # rename the video file
        # os.rename(os.path.join(temp_dir, video_files[i]), os.path.join(output_dir, f'video.mp4'))

        # download video cover and chat
        craw_cover_chat(bv=f'ss{series_number}-{i + 1}', output_dir=output_dir)

    shutil.rmtree(temp_dir)


def search(keyword: str, page: int, pagesize: int = 20, result_type: str = 'video') -> list:
    assert pagesize == 20

    param = {
        '__refresh__': True,
        '_extra': '',
        'keyword': keyword,
        'page': page,
        'page_size': pagesize,
        'from_source': '',
        'platform': 'pc',
        'highlight': 0,
        'single_column': 0,
        'search_type': 'video',
        'source_tag': 3,
        'dynamic_offset': 0,
        'order': 'dm',
    }
    r = requests.get(url='https://api.bilibili.com/x/web-interface/search/all/v2',
                     params=param, headers=config.get_headers())
    data = r.json()
    for item in data['data']['result']:
        if item['result_type'] == result_type:
            return item['data']

    # unsupported result_type
    raise ValueError(f'unsupported result_type: {result_type}')


def high_quality(video: dict) -> bool:
    duration = video['duration']
    n_play = video['play']
    n_chat = video['video_review']
    is_pay = video['is_pay']
    is_union_video = video['is_union_video']

    def duration2seconds(duration: str) -> float:
        seconds = 0.0
        time_sections = duration.split(':')
        time_sections.reverse()
        for i, time_section in enumerate(time_sections):
            seconds += float(time_section) * (60 ** i)
        return seconds
    duration = duration2seconds(duration)

    duration_valid = 30 <= duration <= 180
    n_play_valid = n_play >= 10000
    n_chat_valid = n_chat / duration >= 0.2
    is_pay_valid = is_pay == 0
    is_union_video_valid = is_union_video == 0

    return duration_valid and n_play_valid and n_chat_valid and is_pay_valid and is_union_video_valid


def craw_search(keyword: str, num: int, output_root_dir: os.path) -> None:
    logger.info(f'Searching {keyword} for {num} videos')

    n = 0
    search_max_limit = 1000
    page = 0
    pagesize = 20
    results = []
    while n < num:
        page += 1
        if page * pagesize >= search_max_limit:
            logger.warning(f'Search size limited to {search_max_limit}, only {len(results)} videos found')
            break
        video_list = search(keyword=keyword, page=page)
        for video in video_list:
            bv = video['bvid']
            if not high_quality(video):
                logger.info(f'Skip {bv} for low quality')
                continue
            logger.info(f'Process {bv}, {n + 1}/{num}')
            craw_video(bv=bv, output_root_dir=output_root_dir)
            results.append(video)
            n += 1
            if n >= num:
                break
        with open(os.path.join(output_root_dir, f'{keyword}.json'), 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)


def parse_args(args):
    default_output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'hecate-dataset'
    )
    parser = ArgumentParser(description='Craw Bilibili videos')
    parser.add_argument('--series', type=int, action='store', dest='series', default=None, help='Series number')
    parser.add_argument('--search', type=str, action='store', dest='search', default=None, help='Keyword for searching')
    parser.add_argument('-n', '--num', type=int, action='store', dest='num', default=10, help='Number of videos to craw for searching')
    parser.add_argument('-o', '--output_dir', type=str, action='store', dest='output_dir', default=str(default_output_dir), help='Output directory')
    parser.add_argument('--bv', type=str, action='store', dest='bv', default=None, help='Bilibili video id')

    return parser.parse_args(args)


if __name__ == '__main__':
    parser = parse_args(sys.argv[1:])
    check_dir(parser.output_dir)

    if parser.bv is not None:
        craw_video(bv=parser.bv, output_root_dir=parser.output_dir)
    elif parser.series is not None:
        download_video_series(series_number=parser.series, output_root_dir=parser.output_dir)
    elif parser.search is not None:
        craw_search(keyword=parser.search, num=parser.num, output_root_dir=parser.output_dir)
    else:
        logger.info('No video specified, exit')
