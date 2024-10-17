import requests
import re
from lxml import html
import json
from datetime import datetime

# import requests_cache
# session = requests_cache.CachedSession('.cache', expire_after=9999999) # file name is .cache.sqlite
session = requests.Session()

stocks = []
for i in range(0, 100):
    url = f"""https://advance.quote.nomura.co.jp/meigara/nomura2/qsearch.exe?F=users/nomura/fs_stklist&TARGET3=NULL&TARGET4=NULL&KEY7=%2FUR%2C%2FHK_D%2C%2FXE%2C%2FXE_D%2C%2FAUI_D&SEARCHTYPE=0&MAXDISP=50&GO_BEFORE=&BEFORE={
        i*50}"""
    response = requests.get(url)
    body = response.content.decode("utf-8")
    tree = html.fromstring(body)
    javascript_tags = tree.xpath("//script[@type='text/javascript']")
    for tag in javascript_tags:
        stock = {}
        code = tag.text_content()
        if "getMeigaraName" not in code:
            continue
        # nameLists = getMeigaraName("@322/HK_D", 'TINGYI (CAYMAN ISLANDS) HOLDING', "康師傅ＨＤ（ティンイー＝ケイマン・アイランズ＝）");
        regex = r"getMeigaraName\(.+?\)"
        for match in re.finditer(regex, code):
            names = match.group().replace("getMeigaraName(\"", "").replace("\")", "").split('","')
            stock["original_code"] = names[0]
            stock["original_name"] = names[1]
            stock["japanese_name"] = names[2] if len(names) > 2 else None
            break  # コメントアウトで２個目が定義されており２個ヒットしてしまうので、最初の１個だけを取得する
        # <a href="qsearch.exe?F=users/nomura/fs_detail&KEY1=Z1109" class="link -forward">
        regex = r"qsearch\.exe\?F=users/nomura/fs_detail&KEY1=[a-zA-Z0-9]+"
        for match in re.finditer(regex, code):
            path = match.group()
            stock["nomura_url"] = f"https://advance.quote.nomura.co.jp/meigara/nomura2/{
                path}"
            stock["nomura_code"] = path.split("=")[2]
            break  # 複数ヒットするので、最初の１個だけを取得する
        stocks.append(stock)
    # showHit("1269"); 件数表示
    regex = r"showHit\(\"[0-9]+\"\);"
    for match in re.finditer(regex, body):
        total = int(match.group().split('"')[1])
        break
    print("index", i, "fetched", len(stocks), "total", total)
    if (i+1) * 50 >= total:
        break
else:
    raise Exception("Loop is too many")

stocks = sorted(stocks, key=lambda x: x["nomura_code"])

# print(stocks)

with open("nomura_foreign_stock_list.json", "w", encoding="utf-8") as json_file:
    json_file.write(json.dumps(stocks, ensure_ascii=False, indent=4))
