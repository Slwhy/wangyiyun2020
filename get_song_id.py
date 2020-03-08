
import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
    'Referer': 'https://music.163.com/',
    'Host': 'music.163.com'
}

# 歌单发现界面，可以获取playlistId
# https://music.163.com/discover/playlist/?order=hot&cat=%E5%85%A8%E9%83%A8&limit=35&offset=0

# 歌单界面，可以获取到歌曲id
# https://music.163.com/playlist?id=4867605145      这个url可以获取到内容
# https://music.163.com/#/playlist?id=4867605145    这个url无法获取到内容

# 歌词url
# https://music.163.com/weapi/song/lyric?csrf_token=eda2b6465c53bafb8133362905ec7f73
# 有两个参数
'''
params: Ki/CtdLUIkySP/gQcxHa9pl16zfHgcsy9raDK4dss4ZtKIdcX9Pa+UU7hosZoEqCApaRme+oFbt1Sbn6SAlCN/YDirGv5veMtLAvZTw/9CfGJ1BYv35mMBagqawy2DSy7cyovmsbwJecv8v5NmtsB4NuTVfslHQ2v8mX1SoHNDV1wWOLpr86IwncuyWyWLTv
encSecKey: 8487d02b51294657b882b2224bb844af408459aa7a2192d8668c8ca892326e6e24e53a34ac7662fc2a6438f7d6fddc6a2d823524fe0c8bd9bc68596ddb02c250b9d92ef4e8c03d845ebb8a863b1ea7a9502118b4213b268dabe4c4192bdd253de6412c05bece8044f97246d6d044fe279d22cabf14e12f0b0a8b1bab998fea6c
'''


def get_htmp(url):
    try:
        r = requests.get(url, headers=headers)
        return r.text
    except:
        print(r.status_code)
        return ""


def get_playList_id(playList_id):
    root_url = "https://music.163.com/discover/playlist/?order=hot&cat=%E5%85%A8%E9%83%A8&limit=35&offset={offset}"
    f = open("playList", 'w', encoding='utf8')
    for i in range(39):
        url = root_url.format(offset=i * 35)
        html = get_htmp(url)
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.findAll("a", class_="tit f-thide s-fc0"):
            try:
                href = a.get("href")
                id = href.split("=")[1]
                playList_id.append(id)
                f.write(id + "\t" + a.get("title") + "\n")
            except:
                print(a)


def get_song_id(playList, song_id_list):
    root_url = "https://music.163.com/playlist?id={playList_id}"
    songList = open("songList", "w", encoding="utf8")
    for id in playList:
        url = root_url.format(playList_id=id)
        html = get_htmp(url)
        soup = BeautifulSoup(html, "html.parser")
        for ul in soup.find_all("ul", class_="f-hide"):
            for a in ul.find_all("a"):
                try:
                    id = a.get("href").split("=")[1]
                    title = a.get_text()
                    song_id_list.append(id)
                    songList.write(id + "\t" + title + "\n")
                except:
                    print("解析歌曲页面失败")


if __name__ == '__main__':
    playList_id = []
    song_id = []
    get_playList_id(playList_id)
    get_song_id(playList_id, song_id)
