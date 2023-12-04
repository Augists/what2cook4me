import requests
import json
import uuid
import random
import os
from functools import reduce
import time
from hashlib import md5
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
            try:
                load_video_list_json = json.load(f)
                self.latest_video_bv = load_video_list_json['latest_video_bv']
                for video_info_json in load_video_list_json['list']:
                    title = video_info_json['title']
                    url = video_info_json['url']
                    top_comment = video_info_json['top_comment']
                    self.video_list.append(Video_Info(title, url, top_comment))
            except JSONDecodeError:
                pass

    # def sort_video_info(self):
    # self.video_list = self.video_list.sort()

    def check_update(self, up_url: str, params: dict) -> bool:
        '''
        no update -> False
        '''
        # self.sort_video_info()
        return True if self.latest_video_bv != get_latest_video(up_url, params) else False

    def add_video_info(self, video_info):
        title = video_info['title']
        url = base_url + video_info['bvid']
        top_comment = get_top_comment(video_info['bvid'])
        self.video_list.append(Video_Info(title, url, top_comment))


def update_video_list(up_url: str, params: dict) -> None:
    '''
    读取本地json文件
    检查up视频是否有更新
    若有 -> 更新video_list.json
    '''
    video_info_list = Video_Info_List()
    if video_info_list.check_update(up_url, params):
        get_all_video(up_url, params, video_info_list)
        write_json(video_info_list)
    else:
        print("no update\nstay unchanged")


def get_latest_video(url: str, params: dict) -> str:
    '''
    return latest bv
    '''
    res = requests.get(
        url=url,
        params = params,
        headers=HEADERS,
        timeout=10,
        cookies=COOKIES
    )
    res.encoding = 'utf-8'
    json_res = json.loads(res.text)
    # print(json_res)
    res_video_list = json_res['data']['list']['vlist']
    return res_video_list[0]['bvid']


def get_all_video(url: str, params: dict, video_info_list: Video_Info_List) -> None:
    ps = get_video_count(url, params)
    pn = 0
    while ps > 0:
        params['ps'] = 30 if ps >= 30 else ps
        params['pn'] = pn
        ps = ps - 30
        pn = pn + 1
        res = requests.get(
            url=url,
            params=params,
            headers=HEADERS,
            timeout=10,
            cookies=COOKIES
        )
        res.encoding = 'utf-8'
        json_res = json.loads(res.text)
        print(json_res)
        res_video_list = json_res['data']['list']['vlist']
        if pn == 0:
            # update latest video info(bv)
            video_info_list.latest_video_bv = res_video_list[0]['bvid']
        for res_video_info in res_video_list:
            video_info_list.add_video_info(res_video_info)


def get_video_count(url: str, params: dict) -> int:
    res = requests.get(
        url=url,
        params=params,
        headers=HEADERS,
        timeout=10,
        cookies=COOKIES
    )
    res.encoding = 'utf-8'
    json_res = json.loads(res.text)
    return json_res['data']['page']['count']


def get_top_comment(bv: str) -> str:
    """
    获取视频的置顶评论，如果没有置顶评论则返回 None
    Source: hacker_news cn
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
        cookies=COOKIES
    )
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
    with open(json_path, 'w', encoding='utf-8') as f:
        # f.write(json.dumps(data))
        json.dump(data, f, ensure_ascii=False, indent=2)


# Wbi sign
# https://github.com/SocialSisterYi/bilibili-API-collect
mixinKeyEncTab = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
]

def getMixinKey(orig: str):
    '对 imgKey 和 subKey 进行字符顺序打乱编码'
    return reduce(lambda s, i: s + orig[i], mixinKeyEncTab, '')[:32]

def encWbi(params: dict, img_key: str, sub_key: str):
    '为请求参数进行 wbi 签名'
    mixin_key = getMixinKey(img_key + sub_key)
    curr_time = round(time.time())
    params['wts'] = curr_time                                   # 添加 wts 字段
    params = dict(sorted(params.items()))                       # 按照 key 重排参数
    # 过滤 value 中的 "!'()*" 字符
    params = {
        k : ''.join(filter(lambda chr: chr not in "!'()*", str(v)))
        for k, v 
        in params.items()
    }
    query = urllib.parse.urlencode(params)                      # 序列化参数
    wbi_sign = md5((query + mixin_key).encode()).hexdigest()    # 计算 w_rid
    params['w_rid'] = wbi_sign
    return params

def getWbiKeys() -> tuple[str, str]:
    '获取最新的 img_key 和 sub_key'
    resp = requests.get('https://api.bilibili.com/x/web-interface/nav')
    resp.raise_for_status()
    json_content = resp.json()
    img_url: str = json_content['data']['wbi_img']['img_url']
    sub_url: str = json_content['data']['wbi_img']['sub_url']
    img_key = img_url.rsplit('/', 1)[1].split('.')[0]
    sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
    return img_key, sub_key


if __name__ == '__main__':
    # path: /x/space/wbi/arc/search?mid=1637070460&ps=30&tid=0&pn=1&keyword=&order=pubdate&platform=web&web_location=1550101&order_avoided=true&w_rid=5f623e925753e2a2c08c9820ada9a3b9&wts=1698397697
    # path: /x/space/wbi/arc/search?mid=1637070460&ps=30&tid=0&pn=6&keyword=&order=pubdate&platform=web&web_location=1550101&order_avoided=true&w_rid=5763958a6ea4eb77e4f6020ef4fa5814&wts=1698397854
    # up_space_url = 'https://api.bilibili.com/x/space/wbi/arc/search?mid=' + \
    # up_id + '&order=pubdate&order_avoided=true&platform=web'
    up_space_url = 'https://api.bilibili.com/x/space/wbi/arc/search'
    img_key, sub_key = getWbiKeys()
    params = {
        'mid': up_id,
        'order': 'pubdate',
        'keyword': '',
        'order_avoided': True,
        'platform': 'web'
    }
    signed_params = encWbi(
        params=params,
        img_key=img_key,
        sub_key=sub_key
    )
    update_video_list(up_space_url, signed_params)
