import re

def parse_price_blocks(price_str):
    """
    解析價格字串，例如：
    '149(5枚)/499(30枚入)'
    回傳:
    [{'price': 149, 'note': '5枚'}, {'price': 499, 'note': '30枚入'}]
    """
    pattern = r'(\d+)(\([^\)]+\))?'
    matches = re.findall(pattern, price_str)
    result = []
    for match in matches:
        price = int(match[0])
        note = match[1] if match[1] else ""
        result.append({'price': price, 'note': note})
    
    return result