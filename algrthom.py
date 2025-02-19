import os
import json
from app import mechanization
from itertools import combinations

def run_CRW4(batch):
    """
    模擬呼叫封閉式軟體 CRW4 進行反應計算，
    實際應用中請改成呼叫 CRW4 的 API 或其他介面。
    """
    mechanization.automate(batch)
    print(f"執行 CRW4 批次，包含 {len(batch)} 筆資料，前3筆：{batch[:3]}")

def split_list(data, chunk_size):
    """將 data 切分成每個大小不超過 chunk_size 的子清單"""
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

def split_group_with_labels(group, label, sub_chunk_size):
    """
    將一組資料依 sub_chunk_size 切分，並標記上半部與下半部
    若只有一個子組，則只會回傳 {label: subgroup}；若有兩個，則回傳
    {label: first_half, label+"'": second_half}
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

def main():
    # 1. 讀取 JSON 檔案，抽取 success_item 並取出 CAS 號碼列表
    json_path = r"D:\Systex\CRW4-automation\data\json\test1.json"
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # success_item 格式預期為 [ {"10141-05-6": "COBALT NITRATE"}, ... ]
    success_items = data.get("success_item", [])
    cas_list = []
    for item in success_items:
        # 從字典取出 key（CAS 號碼）
        cas_list.extend(list(item.keys()))
    
    print(f"從 JSON 中抽取到 {len(cas_list)} 筆 CAS 號碼。")
    
    # 2. 將 CAS 清單分成 4 組（例如 400 筆資料分成 4 組，每組 100 筆）
    max_batch_size = 100
    groups = split_list(cas_list, max_batch_size)
    # 給每組設定字母標籤：A、B、C、D…
    group_labels = [chr(ord('A') + i) for i in range(len(groups))]
    
    # A.json, B.json, ...
    output_base = r"D:\Systex\CRW4-automation\data\algrthom\\"
    for label, group in zip(group_labels, groups):
        print(f"組 {label} 有 {len(group)} 筆資料")
        file_name = f"{output_base}{label}.json"
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(group, f, ensure_ascii=False, indent=4)
    
    print("\n=== 組內反應計算 ===")
    # 每組內部配對：直接將每組的資料送入 CRW4
    for label, group in zip(group_labels, groups):
        print(f"處理組 {label} 內部配對")
        run_CRW4(group)

    print("\n=== 組間反應計算 ===")
    # 3. 組間反應計算：任兩組之間所有配對
    # 每次 CRW4 最多 100 筆，因此將每組拆分成上半部與下半部 (50 筆一組)
    sub_chunk_size = max_batch_size // 2  # 50 筆
    for (i, group_A), (j, group_B) in combinations(enumerate(groups), 2):
        label_A = group_labels[i]
        label_B = group_labels[j]
        
        # 將 group_A 與 group_B 分別拆分並標記為上半部與下半部
        subs_A = split_group_with_labels(group_A, label_A, sub_chunk_size)
        subs_B = split_group_with_labels(group_B, label_B, sub_chunk_size)
        
        # 子組間兩兩配對，並依照子組標籤印出
        for sub_label_A, sub_group_A in subs_A.items():
            for sub_label_B, sub_group_B in subs_B.items():
                batch = sub_group_A + sub_group_B
                print(f"處理組 {sub_label_A} 與組 {sub_label_B} 的子組配對 (共 {len(batch)} 筆)")
                run_CRW4(batch)

if __name__ == "__main__":
    main()
