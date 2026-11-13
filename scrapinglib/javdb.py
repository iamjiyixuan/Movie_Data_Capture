# -*- coding: utf-8 -*-

import re
from urllib.parse import urljoin
from lxml import etree
from .httprequest import get_html_by_uc
from .parser import Parser


class Javdb(Parser):
    source = 'javdb'

    expr_number = '//strong[contains(text(),"番號")]/../span/text()'
    expr_number2 = '//strong[contains(text(),"番號")]/../span/a/text()'
    expr_title = "/html/head/title/text()"
    expr_title_no = '//*[contains(@class,"movie-list")]/div/a/div[contains(@class, "video-title")]/text()'
    expr_runtime = '//strong[contains(text(),"時長")]/../span/text()'
    expr_runtime2 = '//strong[contains(text(),"時長")]/../span/a/text()'
    expr_uncensored = '//strong[contains(text(),"類別")]/../span/a[contains(@href,"/tags/uncensored?") or contains(@href,"/tags/western?")]'
    expr_actor = '//span[@class="value"]/a[contains(@href,"/actors/")]/text()'
    expr_actor2 = '//span[@class="value"]/a[contains(@href,"/actors/")]/../strong/@class'
    expr_release = '//strong[contains(text(),"日期")]/../span/text()'
    expr_release_no = '//*[contains(@class,"movie-list")]/div/a/div[contains(@class, "meta")]/text()'
    expr_studio = '//strong[contains(text(),"片商")]/../span/a/text()'
    expr_studio2 = '//strong[contains(text(),"賣家:")]/../span/a/text()'
    expr_director = '//strong[contains(text(),"導演")]/../span/text()'
    expr_director2 = '//strong[contains(text(),"導演")]/../span/a/text()'
    expr_cover = "//div[contains(@class, 'column-video-cover')]/a/img/@src"
    expr_cover2 = "//div[contains(@class, 'column-video-cover')]/img/@src"
    expr_cover_no = '//*[contains(@class,"movie-list")]/div/a/div[contains(@class, "cover")]/img/@src'
    expr_trailer = '//span[contains(text(),"預告片")]/../../video/source/@src'
    expr_extrafanart = "//article[@class='message video-panel']/div[@class='message-body']/div[@class='tile-images preview-images']/a[contains(@href,'/samples/')]/@href"
    expr_tags = '//strong[contains(text(),"類別")]/../span/a/text()'
    expr_tags2 = '//strong[contains(text(),"類別")]/../span/text()'
    expr_series = '//strong[contains(text(),"系列")]/../span/text()'
    expr_series2 = '//strong[contains(text(),"系列")]/../span/a/text()'
    expr_label = '//strong[contains(text(),"系列")]/../span/text()'
    expr_label2 = '//strong[contains(text(),"系列")]/../span/a/text()'
    expr_userrating = '//span[@class="score-stars"]/../text()'
    expr_uservotes = '//span[@class="score-stars"]/../text()'
    expr_actorphoto = '//strong[contains(text(),"演員:")]/../span/a[starts-with(@href,"/actors/")]'

    def extraInit(self):
        self.fixstudio = False
        self.noauth = False

    def updateCore(self, core):
        if core.proxies:
            self.proxies = core.proxies
        if core.verify:
            self.verify = core.verify
        if core.morestoryline:
            self.morestoryline = True
        if core.specifiedSource == self.source:
            self.specifiedUrl = core.specifiedUrl
        # special
        if core.dbcookies:
            self.cookies = core.dbcookies
        else:
            self.cookies =  {'over18':'1', 'theme':'auto', 'locale':'zh'}
        if core.dbsite:
            self.dbsite = core.dbsite
        else:
            self.dbsite = 'javdb'

    def search(self, number: str):
        print(f"[DEBUG] search() ... {number}")
        self.number = number
        print("[DEBUG] Creating UC driver...")
        self.driver = get_html_by_uc(cookies=self.cookies)
        print(f"[DEBUG] Driver created: {self.driver}")
        if self.specifiedUrl:
            self.detailurl = self.specifiedUrl
        else:
            self.detailurl = self.queryNumberUrl(number)
        self.driver.get(self.detailurl)
        import time
        time.sleep(3)
        self.deatilpage = self.driver.page_source
        if '此內容需要登入才能查看或操作' in self.deatilpage or '需要VIP權限才能訪問此內容' in self.deatilpage:
            self.noauth = True
            self.imagecut = 0
            result = self.dictformat(self.querytree)
        else:
            htmltree = etree.fromstring(self.deatilpage, etree.HTMLParser())
            print(f"[DEBUG] Detail page title: {self.driver.title}")
            # Test getNum directly
            try:
                test_num = self.getNum(htmltree)
                print(f"[DEBUG] getNum result: {test_num}")
            except Exception as e:
                print(f"[DEBUG] getNum error: {e}")
            # Check XPath on detail page
            test_part1 = htmltree.xpath('//strong[contains(text(),"番號")]/../span/text()')
            test_part2 = htmltree.xpath('//strong[contains(text(),"番號")]/../span/a/text()')
            print(f"[DEBUG] Detail expr_number (span): {test_part1}")
            print(f"[DEBUG] Detail expr_number2 (span/a): {test_part2}")
            result = self.dictformat(htmltree)
            print(f"[DEBUG] dictformat result: {result[:200] if result else 'None'}")
        self.driver.quit()
        return result

    def queryNumberUrl(self, number):
        print(f"[DEBUG] queryNumberUrl() ... {number}")
        javdb_url = 'https://' + self.dbsite + '.com/search?q=' + number + '&f=all'
        try:
            print(f"[DEBUG] Navigating to: {javdb_url}")
            self.driver.get(javdb_url)
            import time
            time.sleep(3)
            print(f"[DEBUG] Page source length: {len(self.driver.page_source)}")
            # Check if movie-list exists
            tree = etree.fromstring(self.driver.page_source, etree.HTMLParser())
            urls = tree.xpath('//*[contains(@class,"movie-list")]/div/a/@href')
            print(f"[DEBUG] Found {len(urls)} movie items")
            ids = tree.xpath('//*[contains(@class,"movie-list")]/div/a/div[contains(@class, "video-title")]/strong/text()')
            print(f"[DEBUG] Movie IDs found: {ids}")
            print(f"[DEBUG] Raw URLs: {urls}")
        except Exception as e:
            print(f"[DEBUG] Exception in queryNumberUrl: {e}")
            #print(e)
            raise Exception(f'[!] {self.number}: page not fond in javdb')

        if re.search(r'[a-zA-Z]+\.\d{2}\.\d{2}\.\d{2}', number):
            correct_url = urls[0]
        else:
            # ids = self.getTreeAll(self.querytree, '//*[contains(@class,"movie-list")]/div/a/div[contains(@class, "video-title")]/strong/text()')
            try:
                self.queryid = ids.index(number)
                correct_url = urls[self.queryid]
            except:
                # 为避免获得错误番号，只要精确对应的结果
                if ids[0].upper() != number.upper():
                    raise ValueError("number not found in javdb")
                correct_url = urls[0]
        print(f"[DEBUG] correct_url: {correct_url}")
        return urljoin('https://javdb.com', correct_url)

    def getNum(self, htmltree):
        if self.noauth:
            return self.number
        # 番号被分割开，需要合并后才是完整番号
        part1 = self.getTreeElement(htmltree, self.expr_number)
        part2 = self.getTreeElement(htmltree, self.expr_number2)
        dp_number = part2 + part1
        # NOTE 检测匹配与更新 self.number
        if dp_number.upper() != self.number.upper():
            raise Exception(f'[!] {self.number}: find [{dp_number}] in javdb, not match')
        self.number = dp_number
        return self.number

    def getTitle(self, htmltree):
        if self.noauth:
            return self.getTreeElement(htmltree, self.expr_title_no, self.queryid)
        browser_title = super().getTitle(htmltree)
        title = browser_title[:browser_title.find(' | JavDB')].strip()
        return title.replace(self.number, '').strip()

    def getCover(self, htmltree):
        if self.noauth:
            return self.getTreeElement(htmltree, self.expr_cover_no, self.queryid)
        return super().getCover(htmltree)

    def getRelease(self, htmltree):
        if self.noauth:
            return self.getTreeElement(htmltree, self.expr_release_no, self.queryid).strip()
        return super().getRelease(htmltree)

    def getDirector(self, htmltree):
        return self.getTreeElementbyExprs(htmltree, self.expr_director, self.expr_director2)
    
    def getSeries(self, htmltree):
        # NOTE 不清楚javdb是否有一部影片多个series的情况，暂时保留
        results = self.getTreeAllbyExprs(htmltree, self.expr_series, self.expr_series2)
        result = ''.join(results)
        if not result and self.fixstudio:
            result = self.getStudio(htmltree)
        return result

    def getLabel(self, htmltree):
        results = self.getTreeAllbyExprs(htmltree, self.expr_label, self.expr_label2)
        result = ''.join(results)
        if not result and self.fixstudio:
            result = self.getStudio(htmltree)
        return result

    def getActors(self, htmltree):
        actors = self.getTreeAll(htmltree, self.expr_actor)
        genders = self.getTreeAll(htmltree, self.expr_actor2)
        r = []
        idx = 0
        # NOTE only female, we dont care others
        actor_gendor = 'female'
        for act in actors:
            if((actor_gendor == 'all')
            or (actor_gendor == 'both' and genders[idx] in ['symbol female', 'symbol male'])
            or (actor_gendor == 'female' and genders[idx] == 'symbol female')
            or (actor_gendor == 'male' and genders[idx] == 'symbol male')):
                r.append(act)
            idx = idx + 1
        if re.match(r'FC2-[\d]+', self.number, re.A) and not r:
            r = '素人'
            self.fixstudio = True
        return r

    def getOutline(self, htmltree):
        if self.morestoryline:
            from .storyline import getStoryline
            return getStoryline(self.number, self.getUncensored(htmltree),
                                proxies=self.proxies, verify=self.verify)
        return ''

    def getTrailer(self, htmltree):
        video = super().getTrailer(htmltree)
        # 加上数组判空
        if video:
            if not 'https:' in video:
                video_url = 'https:' + video
            else:
                video_url = video
        else:
            video_url = ''
        return video_url

    def getTags(self, htmltree):
        return self.getTreeAllbyExprs(htmltree, self.expr_tags, self.expr_tags2)

    def getUserRating(self, htmltree):
        try:
            numstrs = self.getTreeElement(htmltree, self.expr_userrating)
            nums = re.findall('[0-9.]+', numstrs)
            return float(nums[0])
        except:
            return ''

    def getUserVotes(self, htmltree):
        try:
            result = self.getTreeElement(htmltree, self.expr_uservotes)
            v = re.findall('[0-9.]+', result)
            return int(v[1])
        except:
            return ''

    def getaphoto(self, url):
        driver = get_html_by_uc()
        driver.get(url)
        import time
        time.sleep(2)
        html_page = driver.page_source
        driver.quit()
        img_url = re.findall(r'<span class\=\"avatar\" style\=\"background\-image\: url\((.*?)\)', html_page)
        return img_url[0] if img_url else ''

    def getActorPhoto(self, htmltree):
        actorall = self.getTreeAll(htmltree, self.expr_actorphoto)
        if not actorall:
            return {}
        actors = self.getActors(htmltree)
        actor_photo = {}
        for i in actorall:
            x = re.findall(r'/actors/(.*)', i.attrib['href'], re.A)
            if not len(x) or not len(x[0]) or i.text not in actors:
                continue
            # NOTE: https://c1.jdbstatic.com 会经常变动，直接使用页面内的地址获取
            # actor_id = x[0]
            # pic_url = f"https://c1.jdbstatic.com/avatars/{actor_id[:2].lower()}/{actor_id}.jpg"
            # if not self.session.head(pic_url).ok:
            try:
                pic_url = self.getaphoto(urljoin('https://javdb.com', i.attrib['href']))
                if len(pic_url):
                    actor_photo[i.text] = pic_url
            except:
                pass
        return actor_photo

