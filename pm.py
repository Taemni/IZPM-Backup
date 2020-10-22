#-*- coding: utf-8 -*-
import os, re, json, requests, dbms
from datetime import datetime

#Private Mail Credentials
PM_USERID = ""
PM_ACCESSTOKEN = "" 

PM_APPVER = ""
PM_DEVICE = ""
PM_OSTYPE = ""
PM_OSVERSION = ""
PM_USERAGENT = ""

pm_headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Application-Version": PM_APPVER,
    "User-Id": PM_USERID,
    "Accept-Language": "ko-kr",
    "Accept-Encoding": "gzip, deflate, br",
    "Device-Version": PM_DEVICE,
    "Os-Type": PM_OSTYPE,
    "Os-Version": PM_OSVERSION,
    "Application-Language": "ko",
    "Access-Token": PM_ACCESSTOKEN,
    "User-Agent": PM_USERAGENT,
    "Connection": "keep-alive",
    "Terms-Version": "1",
}

def pmGet(url):
    return requests.get(url, headers=pm_headers)

img_ptn = re.compile('img/.*?\\.(?:jpeg|jpg|png|gif)')

class PrivateMail:
    def __init__(self):
        self.id = ""
        self.member = ""
        self.image = False
        self.time = ""
        self.subject = ""
        self.body = ""
        self.body_preview = ""

    def fetch(self):
        if self.id == "":
            raise Exception("PrivateMail ID cannot be null")

        url = "https://app-web.izone-mail.com/mail/%s" % self.id
        res = pmGet(url).text

        # resolve relative path
        res = res.replace('<link href="/css/starship.css" rel="stylesheet">', '').replace('<script type="text/javascript" src="/js/jquery-3.3.1.min.js"></script>', '').replace('<script type="text/javascript" src="/js/mail-detail.js"></script>', '')

        #found all image
        if self.image:
            print("[*] Processing image of mail %s" % self.id)
            imgs = img_ptn.findall(res)
            print(imgs)
            for img in imgs:
                output_path = "output/" + img
                remote_path = "https://img.izone-mail.com/upload/" + img
                if not os.path.exists(os.path.dirname(output_path)):
                    os.makedirs(os.path.dirname(output_path))

                with open(output_path, "wb") as f:
                    resp = pmGet(remote_path)
                    f.write(resp.content)

            res = res.replace("https://img.izone-mail.com/upload/", "../")

        self.body = res

    def writeOut(self):
        if self.body == "":
            self.fetch()

        if not os.path.exists("output/mail/"):
            os.makedirs("output/mail/")

        with open("output/mail/%s.html" % self.id, "w", encoding="UTF-8") as f:
            f.write(self.body)

        # 이미지 첨부 여부
        if self.image:
            img = 'Y'
        else:
            img = 'N'

        # 오늘 날짜 처리
        today_year = datetime.today().year
        if str(today_year) not in self.time:
            self.time = f'{datetime.today().year}/{datetime.today().month}/{datetime.today().day} {self.time}'

        # 데이터베이스 등록
        sql = f"INSERT INTO private_mail (`id`, `member`, `subject`, `preview`, `content`, `time`, `img`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        sql_data = (self.id, self.member, self.subject, self.body_preview, self.body, self.time.replace('/', '-'), img)
        dbms.ExecuteWriteSQL(sql, sql_data)

def getPMList():
    pm_list = []
    idx = 1
    is_break = 0
    target = "https://app-api.izone-mail.com/v1/inbox?is_star=0&is_unread=0&page=%d"
    last_id = dbms.ExecuteReadSQL(f"SELECT id FROM private_mail order by idx desc limit 1")[0][0]

    while True:
        whole_data = json.loads(pmGet(target % idx).text)
        print("[+] Fetching page %d" % idx)
        for pm_data in whole_data["mails"]:
            # 마지막으로 저장한 메일 ID
            if pm_data['id'] == last_id:
                is_break = 1
                break

            pm = PrivateMail()
            
            pm.id = pm_data["id"]

            pm.member = pm_data["member"]["name"]
            pm.image = pm_data["is_image"]
            pm.time = pm_data["receive_time"]
            pm.subject = pm_data["subject"]
            pm.body_preview = pm_data["content"][:45]

            pm_list.append(pm)

        if is_break:
            break

        if not whole_data["has_next_page"]:
            break
        idx += 1

    print("[*] Fetching done - %d mails loaded" % len(pm_list))
    return pm_list

def wroteBack(pmlist):
    with open("output/pm.js", "w", encoding="UTF-8") as f:
        f.write("var pm_list = Array();")
        for pm in pmlist:
            fmt = 'pm_list.push({"id": "%s", "member": "%s", "subject": "%s", "preview": "%s", "time": "%s"});'
            f.write(fmt % (pm.id, pm.member, pm.subject.replace("\"", "\\\""), pm.body_preview.replace("\"", "\\\""), pm.time))

if __name__ == "__main__":
    pm_list = getPMList()

    # DB에 등록되지 않은 메일이 있으면 실행
    if pm_list:
        for x in reversed(pm_list):
            x.writeOut()

        print("[*] Writing local database")
        wroteBack(pm_list)
        print("[*] Writing done")