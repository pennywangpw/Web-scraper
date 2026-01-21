import requests
from bs4 import BeautifulSoup
import xlsxwriter  # 修改點 1: 使用 xlsxwriter
from urllib.parse import urljoin
from io import BytesIO # 修改點 2: 用於處理圖片二進位資料

# 目標網址
url = "https://www.hydron.com.tw/product"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
response.encoding = response.apparent_encoding
soup = BeautifulSoup(response.text, "html.parser")

category_items = []
categories = soup.find_all("div", class_="col-md-3 col-sm-6 col-xs-12")

for category_div in categories:
    a_tag = category_div.find("a", href=True)
    title_name = category_div.get_text(strip=True)
    if a_tag:
        full_url = urljoin("https://www.hydron.com.tw", a_tag['href'])
        category_items.append({"category": title_name, "url": full_url})

# 準備 Excel 檔案
filename = "eyecontact_products_list.xlsx"
workbook = xlsxwriter.Workbook(filename)
worksheet = workbook.add_worksheet()

# 設定欄寬 (第一欄到第四欄)
worksheet.set_column('A:A', 15)  # 分類
worksheet.set_column('B:B', 40)  # 品名
worksheet.set_column('C:C', 15)  # 價格
worksheet.set_column('D:D', 30)  # 顏色
worksheet.set_column('D:D', 20)  # 圖片欄位寬度

# 寫入標題
headers_list = ["Category", "Name", "Price", "Color", "Image"]
for col_num, header in enumerate(headers_list):
    worksheet.write(0, col_num, header)

row_idx = 1
print("開始抓取各分類的商品資料...", len(category_items), "個分類")

for item in category_items:
    category = item["category"]
    cat_url = item["url"]
    print(f"正在抓取分類: {category}")
    
    res = requests.get(cat_url, headers=headers)
    res.encoding = res.apparent_encoding
    cat_soup = BeautifulSoup(res.text, "html.parser")
    # print("分類頁面抓取成功---cat_soup:", cat_soup)
    product_items = cat_soup.find_all("div", class_="col-xs-6")
    

    for p_item in product_items:
        #設定
        color_info = ""
        # 抓取圖片網址
        img_tag = p_item.find("img")
        img_url = urljoin("https://www.hydron.com.tw", img_tag['src']) if img_tag else ''
        
        #再往下一層,商品細節找資訊-顏色
        item_a_tag=p_item.find("a", href=True)
        item_a_tag_url = urljoin("https://www.hydron.com.tw", item_a_tag['href']) if item_a_tag else ''
        res = requests.get(item_a_tag_url, headers=headers)
        res.encoding = res.apparent_encoding
        item_details_soup = BeautifulSoup(res.text, "html.parser")

        #先找出產品
        product_details =item_details_soup.find("div", class_="product_infor")
        itme_details_text = product_details.get_text(strip=True)


        #找出顏色
        if "顏色" in itme_details_text:
            details_parts = itme_details_text.split("顏色")
            if len(details_parts) == 2:
                details_after_color = details_parts[1]
                color_info = details_after_color.split("材質")[0].strip() if "材質" in details_after_color else details_after_color.strip()



        #找出價格和名稱
        name_h3= product_details.find('h3', class_="title")
        name = name_h3.get_text(strip=True) if name_h3 else ''

        price_p = product_details.find('p',class_="price")
        price = price_p.get_text(strip=True).replace("TWD.","") if price_p else ''


        # 寫入文字資料
        worksheet.write(row_idx, 0, category)
        worksheet.write(row_idx, 1, name)
        worksheet.write(row_idx, 2, price)
        worksheet.write(row_idx, 3, color_info)

        
        # 修改點 3: 下載並插入圖片
        if img_url:
            try:
                img_data = requests.get(img_url).content
                image_file = BytesIO(img_data)
                
                # 設定列高，否則圖片會重疊
                worksheet.set_row(row_idx, 80) 
                
                # 插入圖片並縮小比例以符合單元格 (x_scale, y_scale)
                worksheet.insert_image(row_idx, 3, img_url, {
                    'image_data': image_file,
                    'x_scale': 0.5, 
                    'y_scale': 0.5,
                    'x_offset': 5,
                    'y_offset': 5
                })
            except Exception as e:
                print(f"圖片下載失敗: {img_url}, 錯誤: {e}")
        
        row_idx += 1


workbook.close()
print(f"存檔成功：{filename}")