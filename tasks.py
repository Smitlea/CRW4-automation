import json

from dotenv import load_dotenv
from logger import logger
from pywinauto import Application
from util import CRW4Automation, file_handler

# 讀取config.json
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
PATH = config["CRW4_PATH"]
OUTPUT_PATH = config["OUTPUT_PATH"]

load_dotenv()

# 全域變數
base_json_path = r"D:\Systex\CRW4-automation\data\algrthom\test1.json"
daily_json_path = r"D:\Systex\CRW4-automation\data\algrthom\daily.json"
output_base = r"D:\Systex\CRW4-automation\data\algrthom\\"


class CRW4Factory:
    """ 用於管理 CRW4 實例的工廠 """
    _crw4_automation_instance = None

    @staticmethod
    def get_crw4_automation():
        """ 確保只會啟動一次 CRW4 """
        if CRW4Factory._crw4_automation_instance is None:
            logger.info(f"Starting CRW4 Launching from: {PATH}, Output CSV to: {OUTPUT_PATH}")
            app_instance = Application().start(PATH)
            app_instance = Application(backend="uia").connect(path=PATH)
            CRW4Factory._crw4_automation_instance = CRW4Automation(app_instance)
            logger.info("CRW4 application started successfully")
        return CRW4Factory._crw4_automation_instance

class CRW4Mechanization(CRW4Automation):
    def __init__(self, automation:CRW4Automation):
        self.crw4_automation = automation
        logger.info("CRW4Mechanization initialized")
        self.crw4_automationoutput_path = OUTPUT_PATH

    def test(self, cas):
        try:
            result = self.crw4_automation.add_chemical(cas)
            return result
        except Exception as e:
            return {"status": 1, "result": e.args[0], "error": e.__class__.__name__}
    
    def automate_check(self, cas_list, id):
        cas_list = list(set(cas_list))
        self.crw4_automationchecked_mixture = False
        try:
            # 創建混合物
            self.crw4_automation.add_mixture(mixture_name=id)

            # 執行多筆檢查
            results = self.crw4_automation.multiple_check(cas_list)

            # 清空混合物
            self.crw4_automation.clear_mixture()

            # 寫入臨時 output.json 檔
            with open("output.json", 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=4)

            # 格式化結果後，寫入檔案
            formatted_check_result = self.crw4_automation.formate_check_output(id, results)
            result = file_handler("json", formatted_check_result, id)

        except Exception as e:
            return {"id": id, "status": 1, "result": e.args[0], "error": e.__class__.__name__}

        return {
            "id": id,
            "status": result["result"],
            "result": f"Json文件成功保存到 {OUTPUT_PATH}"
        }

    def automate(self, cas_list, id):
        cas_list = list(set(cas_list)) # 去除重複 CAS
        self.crw4_automation.checked_mixture = False  # 防呆機制
        try:
            # 創建混合物
            self.crw4_automation.add_mixture(mixture_name=id)

            # 添加化學品
            results = self.crw4_automation.multiple_search(cas_list)

            # 輸出圖表
            self.crw4_automation.output_chart_to_csv()

            # 產生 Excel
            file_handler("xlsx", id=id)

            # 回到主頁面
            self.crw4_automation.click_button("Mixture\rManager")

            # 清空混合物
            self.crw4_automation.clear_mixture()

            # 整理輸出結果
            with open("output.json", 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=4)

            # 格式化結果後，寫入檔案
            formatted_result = self.crw4_automation.format_output(id, results)
            result = file_handler("json", formatted_result, id)

        except Exception as e:
            return {"id": id, "status": 1, "result": e.args[0], "error": e.__class__.__name__}

        return {
            "id": id,
            "status": result["result"],
            "result": f"Json文件成功保存到 {OUTPUT_PATH}"
        }

class CRW4Algorithm(CRW4Mechanization):
    def __init__(self, mechanization:CRW4Mechanization):
        self.mechanization = mechanization
        self.base_json_path = base_json_path
        self.daily_json_path = daily_json_path
        self.output_base = output_base
        self.max_batch_size = 100
        self.sub_chunk_size = 50
        self.base_subgroups = {}

    def split_list(self, data, chunk_size):
        """將 data 切分成每個大小不超過 chunk_size 的子清單"""
        return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

    def split_group_with_labels(self, group, label):
        """將一組資料依 sub_chunk_size 切分，並標記上半部與下半部"""
        subs = self.split_list(group, self.sub_chunk_size)
        result = {}
        if not subs:
            return result
        if len(subs) == 1:
            result[label] = subs[0]
        else:
            result[label] = subs[0]
            result[label + "'"] = subs[1]
        return result

    def process_base_data(self):
        """處理基礎 JSON 資料並進行分組"""
        with open(self.base_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        success_items = data.get("success_item", [])
        cas_list = [list(item.keys())[0] for item in success_items]
        
        logger.debug(f"從基礎 JSON 中抽取到 {len(cas_list)} 筆 CAS 資料。")
        groups = self.split_list(cas_list, self.max_batch_size)
        group_labels = [chr(ord('A') + i) for i in range(len(groups))]
        
        for label, group in zip(group_labels, groups):
            logger.info(f"組 {label} 有 {len(group)} 筆資料")
            file_name = f"{self.output_base}{label}.json"
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(group, f, ensure_ascii=False, indent=4)
        
        for label, group in zip(group_labels, groups):
            subgroups = self.split_group_with_labels(group, label)
            self.base_subgroups.update(subgroups)

    def process_daily_data(self):
        """讀取日新增資料 JSON"""
        with open(self.daily_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        daily_data = data.get("daily", [])
        logger.info(f"從日新增 JSON 中抽取到 {len(daily_data)} 筆資料。")
        if len(daily_data) > 50:
            return logger.error("每日新增資料超過 50 筆，請重新檢查。")
        return daily_data

    def daily_algrthom(self):
        """對基礎資料與日新增資料進行cross-pair處理"""
        self.process_base_data()
        daily_data = self.process_daily_data()
        daily_label = "X"
        
        logger.info("\n=== 日新增資料與基礎資料子組間反應計算 ===")
        for base_label, base_group in self.base_subgroups.items():
            batch = daily_data + base_group
            logger.highlight(f"處理組 {daily_label} 與組 {base_label} 的子組配對 (共 {len(batch)} 筆)")
            result = self.mechanization.automate(batch, 'X'+base_label)
            logger.info(f'result:{result}')

