# coding:utf-8
import os
import binascii
from Crypto.Cipher import AES
import base64
import json
import requests
import re

first_param = {"ids": "[1353194608]", "level": "standard", "encodeType": "aac", "csrf_token": ""}
second_param = "010001"
third_param = "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"
fourth_param = "0CoJUm6Qyw8W8jud"
headers = {
    "Referer": "https://music.163.com/",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.81 Mobile Safari/537.36"
}


def random_str(size):
    return binascii.hexlify(os.urandom(size))[:16]  # binascii.hexlify()接受byte字符窜，返回ascii字符窜


def get_params(text, key):  # AES对称加密
    iv = b'0102030405060708'
    pad = 16 - len(text) % 16
    text = text + pad * chr(pad)
    text = text.encode('utf-8')
    try:
        key = key.encode('utf-8')
    except:
        pass
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    result = encryptor.encrypt(text)
    result_str = base64.b64encode(result).decode('utf-8')
    return result_str


def get_encSecKey(text, pubkey, modulus):  # rsa不对称加密
    text = text[::-1]
    rs = pow(int(binascii.hexlify(text), 16), int(pubkey, 16), int(modulus, 16))
    return format(rs, 'x').zfill(256)


def encrypt_data(first_param, second_param, third_param, fourth_param):
    data = {}
    i = random_str(16)
    temp = get_params(json.dumps(first_param), fourth_param)
    params = get_params(temp, i)
    encSecKey = get_encSecKey(i, second_param, third_param)
    data['params'] = params.encode("utf-8")
    data['encSecKey'] = encSecKey
    return data


# 获取歌曲名称
def get_song_title(id):
    url = "https://music.163.com/song?id=%s" % (id)
    response = requests.get(url, headers=headers)
    title = re.search(r'<title>(.*?)\s-', response.text).group(1)  # 匹配歌曲标题
    # print(title)
    return title


# 获取歌曲的下载地址，大小等信息
def get_song_info(id):
    first_param['ids'] = "[%s]" % id
    data = encrypt_data(first_param, second_param, third_param, fourth_param)
    url = "https://music.163.com/weapi/song/enhance/player/url/v1?csrf_token="
    response = requests.post(url, headers=headers, data=data)
    print(response.url)
    # print response.status_code
    json_data = json.loads(response.text)
    return json_data


def get_lyrics(id):
    url = "http://music.163.com/api/song/lyric?id={id}&lv=1&kv=1&tv=-1"
    r = requests.get(url.format(id=id), headers=headers)
    json_data = json.loads(r.text)
    lyrics = json_data["lrc"]['lyric']
    return lyrics


# 下载歌曲
def down_song(id, down_url, song_title, size):
    filename = str(id) + ".mp3"
    print("歌曲大小为：%0.2f Mb" % (size / (1024 * 1024)))
    try:
        result = requests.get(down_url, headers=headers)
        with open(filename, "wb") as f:
            for chunk in result.iter_content(1024):
                f.write(chunk)
                f.flush()
    except Exception as e:
        print("下载失败,id值为：%s" % id)
        print(e)
    print("下载完成")


if __name__ == "__main__":
    lyrics_file = open("lyrics", "w", encoding="utf8")
    with open("songList2", 'r', encoding="utf8") as f:
        for line in f.readlines():
            try:
                id = line.strip().split("\t")[0].strip()
                song_title = get_song_title(id)
                song_info = get_song_info(id)
                down_url = song_info["data"][0]["url"]
                size = song_info["data"][0]["size"]
                down_song(id, down_url, song_title, size)
                lyrics = get_lyrics(id)
                res = {"id": id, "lyrics": lyrics}
                lyrics_file.write(json.dumps(res) + "\n")
            except:
                print("获取失败")
