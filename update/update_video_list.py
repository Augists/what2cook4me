import requests
import json
import uuid
import random
import datetime
import os
from bs4 import BeautifulSoup as bs

HEADERS = {
    'authority': 'api.bilibili.com',
    # 'path': '/x/space/wbi/arc/search?mid=1637070460&pn=1&ps=25&index=1&order=pubdate&order_avoided=true&platform=web&web_location=1550101&w_rid=9f20eea6cf38eadbb274ce17de811a7e&wts=1698396618',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'sec-ch-ua': '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.37',
}

COOKIES = {
    'buvid3': "{}{:05d}infoc".format(uuid.uuid4(), random.randint(1, 99999))
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
            load_video_list_json = json.load(f)
            for video_info_json in load_video_list_json:
                self.video_list.append(video_info(video_info_json))

    def sort_video_info(self):
        self.video_list = self.video_list.sort()

    def get_latest(self) -> video_info:
        self.sort_video_info()
        return self.video_list[-1] if len(self.video_list) else None


def update_video_list(up_url: str) -> None:
    '''
    检查up视频是否有更新
    若有 -> 更新video_list.json
    '''
    json_file = 'video_list.json'

    video_list = video_info_list(json_file)
    latest_video = video_list.get_latest()
    if latest_video == None or latest_video.url != get_latest_video(up_url):
        video_list = get_all_video(up_url)
        write_json(video_list, json_file)


def get_latest_video(url: str) -> str:
    return None


def get_all_video(url: str) -> video_info_list:
    res = requests.get(url, headers=HEADERS, cookies=COOKIES)
    res.encoding = 'utf-8'
    print(res.text)
    soup = bs(res.text)
    # print(soup)
    BVselector = soup.select_one("div.section.video.full-rows")
    # for BV in BVselector.select('div'):
    # print(BV)
    return video_info_list()


def write_json(video_list: video_info_list, json_file: str) -> None:
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(video_list.__dict__))


if __name__ == '__main__':
    up_id = '1637070460'
    # path: /x/space/wbi/arc/search?mid=1637070460&ps=30&tid=0&pn=1&keyword=&order=pubdate&platform=web&web_location=1550101&order_avoided=true&w_rid=5f623e925753e2a2c08c9820ada9a3b9&wts=1698397697
    # path: /x/space/wbi/arc/search?mid=1637070460&ps=30&tid=0&pn=6&keyword=&order=pubdate&platform=web&web_location=1550101&order_avoided=true&w_rid=5763958a6ea4eb77e4f6020ef4fa5814&wts=1698397854
    up_url = 'https://api.bilibili.com/x/space/wbi/arc/search?mid=' + \
        up_id + '&order=pubdate&order_avoided=true&platform=web'
    # update_video_list(up_url)
    print(get_all_video(up_url))
