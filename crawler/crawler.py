import requests
import json
import os
import shutil
from bs4 import BeautifulSoup
from you_get import common

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

    # download video
    common.any_download(url=f'https://www.bilibili.com/video/{bv}', output_dir=output_dir, merge=True, info_only=False,
                        stream_id='flv360')


if __name__ == '__main__':
    output_root_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dataset')
    if not os.path.exists(output_root_dir):
        os.mkdir(output_root_dir)

    bv = 'BV138411L7Ze'
    craw(bv, output_root_dir)
