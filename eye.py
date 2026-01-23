import requests
from bs4 import BeautifulSoup
import xlsxwriter  # 修改點 1: 使用 xlsxwriter
from urllib.parse import urljoin
from io import BytesIO # 修改點 2: 用於處理圖片二進位資料
import logging
from untils import * 

# 加上logging設定
logging.basicConfig(
    level=logging.INFO,   # DEBUG / INFO / WARNING
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename="scraper.log",
    encoding="utf-8"
)



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
worksheet.set_column('E:E', 50)  # 備註
worksheet.set_column('F:F', 15)  # 產品size
worksheet.set_column('G:G', 15)  # 每片價格
worksheet.set_column('H:H', 20)  # 圖片欄位寬度

# 寫入標題
headers_list = ["Category", "Name", "Price", "Color", "Note","Size","Price per lens/per ml","Image"]
for col_num, header in enumerate(headers_list):
    worksheet.write(0, col_num, header)

row_idx = 1
logging.info("開始抓取各分類的商品資料... 共 %d 個分類", len(category_items))
cat_cnt= 0

for item in category_items:
    cat_cnt+=1
    category = item["category"]
    cat_url = item["url"]
    logging.info("正在抓取分類: %s , %s",cat_cnt,  category)
    
    res = requests.get(cat_url, headers=headers)
    res.encoding = res.apparent_encoding
    cat_soup = BeautifulSoup(res.text, "html.parser")
    product_items = cat_soup.find_all("div", class_="col-xs-6")
    
    # 每個類別裡面還有多項itemsm,例如透明鏡片有多款
    for p_item in product_items:
        #設定
        color_info = ""
        # 抓取圖片網址
        img_tag = p_item.find("img")
        img_url = urljoin("https://www.hydron.com.tw", img_tag['src']) if img_tag else ''
        
        #再往下一層,商品細節找資訊
        item_a_tag=p_item.find("a", href=True)
        item_a_tag_url = urljoin("https://www.hydron.com.tw", item_a_tag['href']) if item_a_tag else ''
        res = requests.get(item_a_tag_url, headers=headers)
        res.encoding = res.apparent_encoding
        item_details_soup = BeautifulSoup(res.text, "html.parser")

        #找出產品size
        product_size =item_details_soup.find("div", class_="product_size")
        product_size_text = product_size.get_text(strip=True)
        
        #先找出產品
        product_details =item_details_soup.find("div", class_="product_infor")
        itme_details_text = product_details.get_text(strip=True)

        #從產品裡面再去找出價格和名稱
        # 1. 產品名稱
        name_h3= product_details.find('h3', class_="title")       
        if not name_h3:
            logging.warning("找不到商品名稱於網址: %s", item_a_tag_url)
        else:
            name = name_h3.get_text(strip=True)

        # 2. 產品價格
        price_p = product_details.find('p',class_="price")
        if not price_p:
            logging.warning("找不到價格資訊於商品: %s", name)
        else:
            price = price_p.get_text(strip=True).replace("TWD.","")
        
        logging.debug("商品 尺寸: %s, 名稱: %s, 價格: %s, 顏色: %s, 圖片網址: %s", product_size_text, name, price, color_info, img_url)


        # 3. 產品顏色
        if "顏色" in itme_details_text:
            details_parts = itme_details_text.split("顏色")
            if len(details_parts) == 2:
                details_after_color = details_parts[1]
                color_info = details_after_color.split("字號")[0].strip() if "字號" in details_after_color else details_after_color.strip()
        else:
            logging.warning("找不到顏色資訊於商品: %s", name)

        # ----上面找到的資訊再做處理
        # price 可能包含多個價格區塊，需要解析 再寫入
        price_blocks = parse_price_blocks(price)
        
        # 從product_size_text 中拿取每個尺寸的數字部分
        pattern = '\d+'
        sizes = re.findall(pattern, product_size_text)

        #同個產品有不同size包裝,對應到的價格也不同,需要分別寫入
        for idx,product_size in enumerate(sizes):
            price_per_lens = caculate_each_price(price_blocks[idx]['price'], int(sizes[idx]) if sizes[idx] else 0)

            # 寫入文字資料
            worksheet.write(row_idx, 0, category)
            worksheet.write(row_idx, 1, name)
            worksheet.write(row_idx, 2, price_blocks[idx]['price'])  # 將價格轉為整數寫入
            worksheet.write(row_idx, 3, color_info)
            worksheet.write(row_idx, 4, price_blocks[idx]['note']) #寫入備註 例如 5枚 / 30枚入
            worksheet.write(row_idx, 5, sizes[idx])  # 寫入產品尺寸
            worksheet.write(row_idx, 6, price_per_lens)  # 寫入單價

            row_idx += 1


        # # 修改點 3: 下載並插入圖片
        # if img_url:
        #     try:
        #         img_data = requests.get(img_url).content
        #         image_file = BytesIO(img_data)
                
        #         # 設定列高，否則圖片會重疊
        #         worksheet.set_row(row_idx, 80) 
                
        #         # 插入圖片並縮小比例以符合單元格 (x_scale, y_scale)
        #         worksheet.insert_image(row_idx, 3, img_url, {
        #             'image_data': image_file,
        #             'x_scale': 0.5, 
        #             'y_scale': 0.5,
        #             'x_offset': 5,
        #             'y_offset': 5
        #         })
        #     except Exception as e:
        #         logging.error("圖片下載失敗: %s, 錯誤: %s", img_url, e)

workbook.close()
logging.info("所有資料已寫入 Excel 檔案。")
