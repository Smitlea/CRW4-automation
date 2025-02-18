
from itertools import combinations

def run_CRW4(batch):
    # 這裡僅列印批次中化學品的數量及前幾筆資料作示範
    print(f"執行 CRW4 批次，包含 {len(batch)} 筆資料，前3筆：{batch[:3]}")

# 1. 將 cas_list 分組（假設總數為400，每組 100 筆）
batch_size = 100
num_groups = (len(cas_list) + batch_size - 1) // batch_size
groups = [cas_list[i * batch_size:(i + 1) * batch_size] for i in range(num_groups)]

print("=== 組內反應計算 ===")
# 組內計算：每組內所有配對都在同一批次內進行
for idx, group in enumerate(groups):
    print(f"處理組 {idx+1} 內部配對")
    run_CRW4(group)

print("\n=== 組間反應計算 ===")
# 組間計算：對每一對不同組，將每組再分成兩個子組 (假設每組正好 100 筆，拆成 50 筆一組)
sub_batch_size = 50

for (i, group1), (j, group2) in combinations(enumerate(groups), 2):
    # 分割 group1 與 group2 為兩個子組
    group1_sub1 = group1[:sub_batch_size]
    group1_sub2 = group1[sub_batch_size:]
    group2_sub1 = group2[:sub_batch_size]
    group2_sub2 = group2[sub_batch_size:]
    
    # 對四種子組組合進行計算，每次合併後的批次數量為 50+50=100
    sub_batches = [
        (group1_sub1, group2_sub1),
        (group1_sub1, group2_sub2),
        (group1_sub2, group2_sub1),
        (group1_sub2, group2_sub2)
    ]
    
    for sub_idx, (sub1, sub2) in enumerate(sub_batches, start=1):
        batch = sub1 + sub2
        print(f"處理組 {i+1} 與組 {j+1} 之間，第 {sub_idx} 個子組配對")
        run_CRW4(batch)
