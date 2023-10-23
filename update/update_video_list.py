import requests
import json
import datetime
import os
from bs4 import BeautifulSoup as bs

HEADERS = {
    'authority': 'api.bilibili.com',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'origin': 'https://space.bilibili.com',
    'referer': 'https://space.bilibili.com/489667127/channel/collectiondetail?sid=249279',
    'sec-ch-ua': '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.37',
}


class video_info:
    '''
    视频列表存储单元
    video_info
        title
        url
        top_comment
        date
    '''

    def __init__(self, video_info_json) -> None:
        self.title = video_info_json.title
        self.url = video_info_json.url
        self.top_comment = video_info_json.top_comment
        self.date = video_info_json.date

    def __lt__(self, other):
        return self.date < other.date


class video_info_list:
    def __init__(self, json_path) -> None:
        self.video_list = list()
        self.json_path = json_path
        self.check_and_read()

    def check_and_read(self):
        if not os.path.exists(self.json_path):
            os.mknod(self.json_path)
            return
        with open(self.json_path, 'r', encoding='utf-8') as f:
            video_list_json = json.load(f)
            for video_info_json in video_list_json:
                self.video_list.append(video_info(video_info_json))

    def sort_video_info(self):
        self.video_list = self.video_list.sort()

    def get_latest(self) -> video_info:
        self.sort_video_info()
        return self.video_list[-1]


def update_video_list(up_url: str) -> None:
    '''
    检查up视频是否有更新
    若有 -> 更新video_list.json
    '''
    json_file = 'video_list.json'

    video_list = video_info_list(json_file)
    latest_video = video_list.get_latest()
    if latest_video.url != get_latest_video(up_url):
        video_list = get_all_video(up_url)
        write_json(video_list, json_file)


def get_latest_video(url: str) -> str:
    return None


def get_all_video(url: str) -> video_info_list:
    res = requests.get(url, headers=HEADERS)
    res.encoding = 'utf-8'
    soup = bs(res.text)
    BVselector = soup.select_one("div.section.video.full-rows")
    for BV in BVselector.select('')
    return video_info_list()


def write_json(video_list: video_info_list, json_file: str) -> None:
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(video_list.__dict__))


if __name__ == '__main__':
    up_id = '1637070460'
    up_url = 'https://space.bilibili.com/' + up_id
    update_video_list(up_url)
