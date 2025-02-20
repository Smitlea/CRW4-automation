import json
from app import mechanization
from logger import logger

def split_list(data, chunk_size):
    """將 data 切分成每個大小不超過 chunk_size 的子清單"""
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

def split_group_with_labels(group, label, sub_chunk_size):
    """
    將一組資料依 sub_chunk_size 切分，並標記上半部與下半部
    例如若 group 共有 100 筆，切成兩個 50 筆的子組，分別標記為 label 與 label + "'"
    """
    subs = split_list(group, sub_chunk_size)
    result = {}
    if not subs:
        return result
    if len(subs) == 1:
        result[label] = subs[0]
    else:
        result[label] = subs[0]
        result[label + "'"] = subs[1]
    return result

def process_base_data(base_json_path, max_batch_size=100):
    """
    分組結果與標籤，將A拆分50比成'A': [前50], "A'": [後50], 'B': [前50], "B'": [後50], ...}
    """
    with open(base_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # JSON 中存放的是 success_item，格式為 [ {"10141-05-6": "NAME"}, ... ]
    success_items = data.get("success_item", [])
    cas_list = []
    for item in success_items:
        cas_list.extend(list(item.keys()))
    
    logger.debug(f"從基礎 JSON 中抽取到 {len(cas_list)} 筆 CAS 資料。")
    groups = split_list(cas_list, max_batch_size)
    group_labels = [chr(ord('A') + i) for i in range(len(groups))]
    
    # A.json, B.json, ...
    output_base = r"D:\Systex\CRW4-automation\data\algrthom\\"
    for label, group in zip(group_labels, groups):
        logger.info(f"組 {label} 有 {len(group)} 筆資料")
        file_name = f"{output_base}{label}.json"
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(group, f, ensure_ascii=False, indent=4)
    
    # 將每組拆分成兩個子組（上半部與下半部），每組數量約 100 筆，則子組大小為 50
    base_subgroups = {}
    sub_chunk_size = 50
    for label, group in zip(group_labels, groups):
        subgroups = split_group_with_labels(group, label, sub_chunk_size)
        base_subgroups.update(subgroups)
    return base_subgroups

def process_daily_data(daily_json_path):
    """
    讀取日新增資料 JSON
    """
    with open(daily_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    daily_data = data.get("daily", [])
    logger.info(f"從日新增 JSON 中抽取到 {len(daily_data)} 筆資料。")
    if len(daily_data) > 50:
        return logger.error("每日新增資料超過 50 筆，請重新檢查。")
    return daily_data

def main():
    # 設定檔案路徑
    base_json_path = r"D:\Systex\CRW4-automation\data\json\test1.json"   # 基礎400筆資料
    daily_json_path = r"D:\Systex\CRW4-automation\data\json\daily.json"  # 每日新增資料 10~30筆


    # 1. 處理基礎資料：取得分組後的子組，標籤如 A, A', B, B', C, C', D, D'
    base_subgroups = process_base_data(base_json_path, max_batch_size=100)

    # 印出各子組的數量
    for label, subgroup in base_subgroups.items():
        logger.debug(f"基礎資料組 {label} 共 {len(subgroup)} 筆資料")

    # 2. 處理每日新增資料：假設視為一個整體群組，標記為 X
    daily_data = process_daily_data(daily_json_path)
    daily_label = "X"
    
    logger.info("\n=== 日新增資料與基礎資料子組間反應計算 ===")
    # 3. 對於每日新增資料 X 與每一個基礎資料子組（例如 A, A', B, B', …）進行比對
    # 每次組合為 daily_data 與某一基礎子組合併，確保總數不超過 100 筆
    for base_label, base_group in base_subgroups.items():
        batch = daily_data + base_group
        logger.highlight(f"處理組 {daily_label} 與組 {base_label} 的子組配對 (共 {len(batch)} 筆)")
        result = mechanization.automate(batch, base_label)
        logger.info(f'result:{result}')

if __name__ == "__main__":
    main()
