import requests
import json
import uuid
import random
import os
# from bs4 import BeautifulSoup as bs

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

base_url = 'https://bilibili.com/'
json_path = 'video_list.json'
up_id = '1637070460'


class Video_Info:
    '''
    视频列表存储单元
    Video_Info
        title
        url
        top_comment
    '''

    # 居然有支持oop的语言不支持重载方法
    # def __init__(self, video_info_json) -> None:
    # self.title = video_info_json.title
    # self.url = video_info_json.url
    # self.top_comment = video_info_json.top_comment

    def __init__(self, title, url, top_comment) -> None:
        self.title = title
        self.url = url
        self.top_comment = top_comment

    # def __lt__(self, other):
    # return self.date < other.date


class Video_Info_List:
    def __init__(self) -> None:
        self.video_list = []
        self.latest_video_bv = None
        self.check_and_read()

    def check_and_read(self):
        '''
        not exist:
            create file and return
        exist:
            read into video_list and latest_video_bv
        '''
        if not os.path.exists(json_path):
            open(json_path, 'a').close()
            # cannot use mknod on Windows, use open to create file on multi-platform. details:
            # https://stackoverflow.com/questions/32691981/python-module-os-has-no-attribute-mknod
            # os.mknod(json_path)
            return
        with open(json_path, 'r', encoding='utf-8') as f:
            load_video_list_json = json.load(f)
            self.latest_video_bv = load_video_list_json['latest_video_bv']
            for video_info_json in load_video_list_json['list']:
                title = video_info_json['title']
                url = video_info_json['url']
                top_comment = video_info_json['top_comment']
                self.video_list.append(Video_Info(title, url, top_comment))

    # def sort_video_info(self):
    # self.video_list = self.video_list.sort()

    def check_update(self, up_url: str) -> bool:
        '''
        no update -> False
        '''
        # self.sort_video_info()
        return True if self.latest_video_bv != get_latest_video(up_url) else False

    def add_video_info(self, video_info):
        title = video_info['title']
        url = base_url + video_info['bvid']
        top_comment = get_top_comment(video_info['bvid'])
        self.video_list.append(Video_Info(title, url, top_comment))


def update_video_list(up_url: str) -> None:
    '''
    读取本地json文件
    检查up视频是否有更新
    若有 -> 更新video_list.json
    '''
    video_info_list = Video_Info_List()
    if video_info_list.check_update(up_url):
        get_all_video(up_url, video_info_list)
        write_json(video_info_list)
    else:
        print("no update\nstay unchanged")


def get_latest_video(url: str) -> str:
    '''
    return latest bv
    '''
    res = requests.get(
        url=url,
        headers=HEADERS,
        timeout=10,
        cookies=COOKIES)
    res.encoding = 'utf-8'
    json_res = json.loads(res.text)
    res_video_list = json_res['data']['list']['vlist']
    return res_video_list[0]['bvid']


def get_all_video(url: str, video_info_list: Video_Info_List) -> None:
    res = requests.get(
        url=url,
        headers=HEADERS,
        timeout=10,
        cookies=COOKIES)
    res.encoding = 'utf-8'
    json_res = json.loads(res.text)
    res_video_list = json_res['data']['list']['vlist']
    # update latest video info(bv)
    video_info_list.latest_video_bv = res_video_list[0]['bvid']
    for res_video_info in res_video_list:
        video_info_list.add_video_info(res_video_info)

    # soup = bs(res.text)
    # BVselector = soup.select_one("div.section.video.full-rows")
    # for BV in BVselector.select('div'):
    # print(BV)


def get_top_comment(bv: str) -> str:
    """
    获取视频的置顶评论，如果没有置顶评论则返回 None
    """
    comment_base_url = 'http://api.bilibili.com/x/v2/reply/main'
    params = {
        'type': 1,
        'oid': bv,
    }
    response = requests.get(
        url=comment_base_url,
        params=params,
        headers=HEADERS,
        timeout=10,
        cookies=COOKIES)
    response.raise_for_status()
    comment_data = response.json()
    top_comment_data = comment_data['data']['top']['upper']
    if top_comment_data is None:
        # 如果没有置顶评论则查看最上面的一条评论
        if comment_data['data']['replies'][0]['member']['mid'] == '1637070460':
            return comment_data['data']['replies'][0]['content']['message']
        else:
            return None
    else:
        return top_comment_data['content']['message']


def write_json(video_info_list: Video_Info_List) -> None:
    data = {'latest_video_bv': video_info_list.latest_video_bv,
            'list': [li.__dict__ for li in video_info_list.video_list]}
    print(data)
    # video_info_list.__dict__
    with open(json_path, 'w', encoding='utf-8') as f:
        # f.write(json.dumps(data))
        json.dump(data, f, ensure_ascii=False)


if __name__ == '__main__':
    # path: /x/space/wbi/arc/search?mid=1637070460&ps=30&tid=0&pn=1&keyword=&order=pubdate&platform=web&web_location=1550101&order_avoided=true&w_rid=5f623e925753e2a2c08c9820ada9a3b9&wts=1698397697
    # path: /x/space/wbi/arc/search?mid=1637070460&ps=30&tid=0&pn=6&keyword=&order=pubdate&platform=web&web_location=1550101&order_avoided=true&w_rid=5763958a6ea4eb77e4f6020ef4fa5814&wts=1698397854
    up_space_url = 'https://api.bilibili.com/x/space/wbi/arc/search?mid=' + \
        up_id + '&order=pubdate&order_avoided=true&platform=web'
    update_video_list(up_space_url)
