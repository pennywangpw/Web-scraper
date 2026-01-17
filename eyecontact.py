import requests
from bs4 import BeautifulSoup
import csv 
from urllib.parse import urljoin

# 目標網址（主頁）
url = "https://www.hydron.com.tw/product"

# 設定 headers 避免被擋掉 (可選)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
response.encoding = response.apparent_encoding  # 避免亂碼

soup = BeautifulSoup(response.text, "html.parser")

products = []
category_items=[]

#先找出所有的category
categories = soup.find_all("div",class_="col-md-3 col-sm-6 col-xs-12")

for category_div in categories:
    a_tag = category_div.find("a", href=True)
    title_name = category_div.get_text(strip=True)
    print("Debug category title:", title_name)

    if a_tag:
        url = urljoin("https://www.hydron.com.tw", a_tag['href'])
        category_items.append({"category": title_name, "url": url})
    
print("Total category URLs found:", len(category_items), category_items)

#從每一個category 的url 拿取資料
for item in category_items:
    category = item["category"]
    url = item["url"]
    print("Processing category:", category, "URL:", url)
    response = requests.get(url, headers=headers)
    response.encoding = response.apparent_encoding  # 避免亂碼

    soup = BeautifulSoup(response.text, "html.parser")

    product_items = soup.find_all("div", class_="col-xs-6")

    for item in product_items:
        text = item.get_text(strip=True)
        print("Debug text:", text)
        if "TWD." in text:
            name_price = text.split("TWD.")
            if len(name_price) == 2:
                name = name_price[0].strip()
                price = name_price[1].strip()
                products.append({"Category": category, "Name":name, "Price":price})

print('Total products found:', len(products))
print(products)



#匯出一個csv
filename = "eyecontact_products_list.csv"
with open(filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=["Category","Name", "Price"])
    writer.writeheader()
    for product in products:
        writer.writerow(product)