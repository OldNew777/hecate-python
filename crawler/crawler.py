import requests
import json
import os
import shutil
from bs4 import BeautifulSoup

import config


def craw(bv: str, output_root_dir: os.path) -> None:
    """
    :param bv: bv to crawl
    :param output_root_dir: directory to save the crawled data
    :return: None
    """

    output_dir = os.path.join(output_root_dir, bv)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)

    r = requests.get(url=f'https://www.ibilibili.com/video/{bv}', headers=config.get_headers())
    soup = BeautifulSoup(r.text, 'lxml')

    def find_url(soup: BeautifulSoup, text: str) -> str:
        node = soup.find_all(name='span', class_='input-group-addon', text=text, recursive=True)
        assert len(node) == 1
        node = node[0]
        return node.parent.input.get('value')

    cover_url = find_url(soup, '视频图片:')
    cover = requests.get(url=cover_url, headers=config.get_headers()).content
    cover_suffix = cover_url.split('.')[-1]
    with open(os.path.join(output_dir, f'cover.{cover_suffix}'), 'wb') as f:
        f.write(cover)

    chat_url = find_url(soup, '弹幕地址:')
    chat = requests.get(url=chat_url, headers=config.get_headers()).content
    with open(os.path.join(output_dir, 'chat.xml'), 'wb') as f:
        f.write(chat)


if __name__ == '__main__':
    output_root_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dataset')
    if not os.path.exists(output_root_dir):
        os.mkdir(output_root_dir)
    bv = 'BV1Yv4y1S713'
    craw(bv, output_root_dir)
