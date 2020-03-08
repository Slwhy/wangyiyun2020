import csv
import json
import re
from copy import deepcopy
from lxml import etree
import requests
import time
# import csv
from selenium import webdriver


class WangYiYun:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36"
        }
        self.start_url = "https://music.163.com/discover/playlist"
        self.file = open("lyrics.txt",'a',encoding="utf8")
        # self.proxy_ip = {"https":"https://222.182.56.41:8118"}

    def parse_url(self, url):
        time.sleep(1)
        resp = requests.get(url, headers=self.headers)
        return resp.content.decode()

    def get_category_list(self):
        """获取大分类名称，小分类名称， 小分类链接"""
        resp = self.parse_url(self.start_url)
        html = etree.HTML(resp)
        dl_list = html.xpath("""//div[@class="bd"]/dl""")  # 大分类
        category_list = []
        for dl in dl_list:
            big_cate_name = dl.xpath("./dt/text()") if len(dl.xpath("./dt/text()")) > 0 else None  # 大分类名字,单独列表
            small_cate_list = dl.xpath("./dd/a")  # 小分类列表 单独列表
            # 循环小分类列表
            for small_cate in small_cate_list:
                item = {}
                # 大分类名字
                item["big_cate_name"] = big_cate_name
                # 小分类名字
                item["small_cate_name"] = small_cate.xpath("./text()")[0] if len(
                    small_cate.xpath("./text()")) > 0 else None
                # print(item)
                # 小分类连接
                item["small_cate_href"] = "https://music.163.com" + small_cate.xpath("./@href")[0] if len(
                    small_cate.xpath("./@href")) > 0 else None
                # print(item)
                category_list.append(item)
        return category_list  # 存着大小分类名字，小分类连接

    def get_playlist_list(self, item, total_playlist_list):
        """
        获取小分类列表的palylist列表和链接
        :param item: item中包含小分类的跳转链接
        :return:
        """
        playlist_list = []
        if item["small_cate_href"] is not None:
            small_cate_resp = self.parse_url(item["small_cate_href"])
            small_cate_html = etree.HTML(small_cate_resp)
            li_list = small_cate_html.xpath("""//ul[@id="m-pl-container"]/li""")  # 得到小分类里面的每一页的歌单列表
            # print(li_list)
            for li in li_list:
                # 歌单标题
                item["playlist_title"] = li.xpath("""./p[@class="dec"]/a/@title""")[0] if len(
                    li.xpath("""./p[@class="dec"]/a/@title""")[0]) > 0 else None
                # 歌单链接
                item["playlist_href"] = "http://music.163.com" + li.xpath("./p[@class='dec']/a/@href")[0] if len(
                    li.xpath("./p[@class='dec']/a/@href")) > 0 else None
                # 歌单作者
                item["playlist_auth"] = li.xpath("""./p[last()]/a/@title""")[0] if len(
                    li.xpath("""./p[last()]/a/@title""")[0]) > 0 else None
                # 作者链接
                item["playlist_auth_href"] = "https://music.163.com" + li.xpath("""./p[2]/a/@href""")[0] if \
                li.xpath("""./p[2]/a/@href""")[0] else None
                playlist_list.append(deepcopy(item))
            total_playlist_list.extend(playlist_list)
            next_url = small_cate_html.xpath("""//a[text()="下一页"]/@href""")[0] if len(
                small_cate_html.xpath("""//a[text()="下一页"]/@href""")[0]) else None
            if next_url is not None and next_url != "javascript:void(0)":
                item["small_cate_href"] = "http://music.163.com" + next_url
                return self.get_playlist_list(item, total_playlist_list)
        return total_playlist_list

    def playlist_brief_info(self, playlist):
        """
        获取每首歌的详细信息
        :param playlist:
        :return:
        """
        if playlist["playlist_href"] is not None:
            playlist_resp = self.parse_url(playlist["playlist_href"])
            # 歌单封面
            playlist["covers"] = re.findall("\"images\": .*?\[\"(.*?)\"\],", playlist_resp)
            playlist["covers"] = playlist["covers"][0] if len(playlist["covers"]) > 0 else None
            # 歌单创建时间
            playlist["create_time"] = re.findall("\"pubDate\": \"(.*?)\"", playlist_resp)
            playlist["create_time"] = playlist["create_time"][0] if len(playlist["create_time"]) > 0 else None
            playlist_html = etree.HTML(playlist_resp)
            # 喜欢次数
            playlist["like_count"] = playlist_html.xpath("//a[@data-res-action='fav']/@data-count")[0] if len(
                playlist_html.xpath("//a[@data-res-action='fav']/@data-count")) > 0 else None
            # 分享次数
            playlist["share_count"] = playlist_html.xpath("//a[@data-res-action='share']/@data-count")[0] if len(
                playlist_html.xpath("//a[@data-res-action='share']/@data-count")) > 0 else None
            # 歌单介绍
            playlist["playlist_desc"] = playlist_html.xpath("//p[@id='album-desc-more']/text()")[0] if len(
                playlist_html.xpath("//p[@id='album-desc-more']/text()")) > 0 else None
            # 播放次数
            playlist["played_count"] = playlist_html.xpath("//strong[@id = 'play-count']/text()")[0] if len(
                playlist_html.xpath("//strong[@id = 'play-count']/text()")) > 0 else None
            # 歌单内容
            playlist["playlist_song_brief_info"] = self.playlist_song_brief_info(playlist["playlist_href"])
        return playlist

    def playlist_song_brief_info(self, href):
        driver = webdriver.Chrome(executable_path="E:\code\chorme\chromedriver")
        driver2 = webdriver.Chrome(executable_path="E:\code\chorme\chromedriver")
        driver.get(href)
        driver.switch_to.frame("g_iframe")
        # 网易云的详情页时用iframe写的
        tr_list = driver.find_elements_by_xpath("//tbody/tr")
        playlist_track = []
        for tr in tr_list:
            try:
                track = {}
                # 歌曲名称
                track["song_name"] = tr.find_element_by_xpath("./td[2]//b").get_attribute("title")
                # 歌曲名字
                track["song_href"] = tr.find_element_by_xpath("./td[2]//a").get_attribute("href")
                # 获取歌词
                driver2.get(track["song_href"])
                driver2.switch_to.frame("g_iframe")
                driver2.find_element_by_xpath('//*[@id="flag_ctrl"]').click()
                lyrics = driver2.find_element_by_xpath('//*[@id="lyric-content"]').text
                song_id = track["song_href"].split("=")[1]
                print(json.dumps({"song_id":song_id,"lyrics":lyrics}))
                self.file.write(lyrics)
                self.file.write("&&this a dividing line&&\n")
                # print("******"*50)
                # print(track["song_name"])
                # 歌曲时间
                track["song_time"] = tr.find_element_by_xpath("./td[3]/span").text
                # 演唱者
                track["song_auth"] = tr.find_element_by_xpath("./td[4]/div").get_attribute("title")
                # 专辑名字
                track["album_name"] = tr.find_element_by_xpath("./td[5]//a").get_attribute("title")
                playlist_track.append(track)
            except:
                print("error")
        # 为了防止还没有加载完数据就关闭浏览器
        time.sleep(3)
        driver.quit()
        driver2.quit()
        return playlist_track

    def run(self):
        big_list = []
        super_big_list = []
        cate_list = self.get_category_list()  # 获取分类 print(cate_list) # 打印出大分类下面的所有二级分类的名称与链接
        for cate in cate_list:  # print(cate) # 打印出打印出大分类下面的所有二级分类的名称与链接
            try:
                total_playlist_list = self.get_playlist_list(cate, [])  # 获得歌单链接和
                for playlist in total_playlist_list:
                    playlist_infos = self.playlist_brief_info(playlist)
                    small_list = []
                    # 将歌单的详细信息添加在small_list列表中
                    small_list.append(playlist_infos["small_cate_name"])
                    small_list.append(playlist_infos["small_cate_href"])
                    small_list.append(playlist_infos["playlist_title"])
                    small_list.append(playlist_infos["playlist_href"])
                    small_list.append(playlist_infos["playlist_auth"])
                    small_list.append(playlist_infos["playlist_auth_href"])
                    small_list.append(playlist_infos["covers"])
                    small_list.append(playlist_infos["create_time"])
                    small_list.append(playlist_infos["like_count"])
                    small_list.append(playlist_infos["share_count"])
                    small_list.append(playlist_infos["playlist_desc"])
                    small_list.append(playlist_infos["played_count"])
                    # 循环歌单中的所有歌曲（所有歌曲存放在一个大列表中，并且每首歌的信息是一个字典
                    for playlist_info in playlist_infos["playlist_song_brief_info"]:
                        play_list_infos = []
                        # 将循环出来的每首歌曲的歌名、歌手名、时长、专辑添加在play_list_infos中
                        play_list_infos.append(playlist_info["song_name"])
                        play_list_infos.append(playlist_info["song_time"])
                        play_list_infos.append(playlist_info["song_auth"])
                        play_list_infos.append(playlist_info["album_name"])
                        play_list_infos.append(playlist_info["song_href"])
                        # 设置一个大列表，将每歌单的详细信息和歌单中的每首歌加在big_list中
                        big_list = small_list + play_list_infos
                        # 将big_list添加在super_big_list中，然后行程[[],[],[],[]....]这样的格式，使用csv保存
                        super_big_list.append(big_list)

                    # print(big_small)
                    import csv
                    with open('some.csv', 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerows(super_big_list)
            except:
                print("error")


if __name__ == "__main__":
    wangyiyun = WangYiYun()
    wangyiyun.run()
