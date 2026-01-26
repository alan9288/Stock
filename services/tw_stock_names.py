# 台股代號中文名稱對照表
# 常見的台股代號對應中文名稱

TW_STOCK_NAMES = {
    # 權值股
    "2330": "台積電",
    "2317": "鴻海",
    "2454": "聯發科",
    "2308": "台達電",
    "2881": "富邦金",
    "2882": "國泰金",
    "2891": "中信金",
    "2886": "兆豐金",
    "2884": "玉山金",
    "2303": "聯電",
    "2412": "中華電",
    "3711": "日月光投控",
    "1301": "台塑",
    "1303": "南亞",
    "1326": "台化",
    "6505": "台塑化",
    "2002": "中鋼",
    "1216": "統一",
    "2207": "和泰車",
    "2382": "廣達",
    "2357": "華碩",
    "2609": "陽明",
    "2615": "萬海",
    "2603": "長榮",
    "3008": "大立光",
    "2892": "第一金",
    "5880": "合庫金",
    "2880": "華南金",
    "5871": "中租-KY",
    "2301": "光寶科",
    "2395": "研華",
    "3045": "台灣大",
    "4904": "遠傳",
    "2912": "統一超",
    "2885": "元大金",
    "2379": "瑞昱",
    "3034": "聯詠",
    "2327": "國巨",
    "6415": "矽力-KY",
    "3037": "欣興",
    "2344": "華邦電",
    "3231": "緯創",
    "2324": "仁寶",
    "3017": "奇鋐",
    "2353": "宏碁",
    "2356": "英業達",
    "4938": "和碩",
    "2345": "智邦",
    "6669": "緯穎",
    "2408": "南亞科",
    "3443": "創意",
    "2474": "可成",
    "3529": "力旺",
    "2377": "微星",
    "8046": "南電",
    "6488": "環球晶",
    "2049": "上銀",
    "3533": "嘉澤",
    "2383": "台光電",
    "2646": "星宇航空",
    "6770": "力積電",
    "3661": "世芯-KY",
    "2618": "長榮航",
    "2610": "華航",
    "2105": "正新",
    "3035": "智原",
    "5274": "信驊",
    "6239": "力成",
    "2449": "京元電子",
    "2201": "裕隆",
    "2231": "為升",
    "6409": "旭隼",
    "3665": "貿聯-KY",
    "6531": "愛普",
    "2059": "川湖",
    "3706": "神達",
    "2049": "上銀",
    
    # ETF
    "0050": "元大台灣50",
    "0052": "富邦科技",
    "0056": "元大高股息",
    "00878": "國泰永續高股息",
    "00881": "國泰台灣5G+",
    "00885": "富邦越南",
    "00891": "中信關鍵半導體",
    "00892": "富邦台灣半導體",
    "00893": "國泰智能電動車",
    "00894": "中信小資高價股",
    "00895": "富邦未來車",
    "00896": "中信綠能及電動車",
    "00919": "群益台灣精選高息",
    "00929": "復華台灣科技優息",
    "006208": "富邦台50",
    "006203": "元大MSCI台灣",
}

# 動態快取（從 TWSE 查詢後儲存）
_dynamic_cache = {}


def fetch_tw_stock_name_from_twse(code: str) -> str:
    """從證交所 API 取得台股中文名稱"""
    import requests
    
    try:
        # 證交所 API - 取得股票基本資料
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{code}.tw"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        
        if data.get("msgArray") and len(data["msgArray"]) > 0:
            stock_info = data["msgArray"][0]
            name = stock_info.get("n")  # n = 股票名稱
            if name:
                return name
        
        # 備用：嘗試上櫃股票
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=otc_{code}.tw"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        
        if data.get("msgArray") and len(data["msgArray"]) > 0:
            stock_info = data["msgArray"][0]
            name = stock_info.get("n")
            if name:
                return name
                
    except Exception as e:
        print(f"無法從 TWSE 取得 {code} 的名稱: {e}")
    
    return None


def get_tw_stock_name(symbol: str) -> str:
    """取得台股中文名稱（優先使用本地對照表，沒有則查詢 TWSE API）"""
    # 移除 .TW 後綴
    code = symbol.replace(".TW", "").replace(".tw", "")
    
    # 1. 先查本地對照表
    if code in TW_STOCK_NAMES:
        return TW_STOCK_NAMES[code]
    
    # 2. 查動態快取
    if code in _dynamic_cache:
        return _dynamic_cache[code]
    
    # 3. 從 TWSE API 查詢
    name = fetch_tw_stock_name_from_twse(code)
    if name:
        _dynamic_cache[code] = name
        return name
    
    return None

