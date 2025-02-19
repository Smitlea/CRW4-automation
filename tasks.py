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

def start_crw4_application():
    """
    初始化並啟動 CRW4 Application
    """
    global crw4_automation
    logger.info(f"Starting CRW4 Launching from: {PATH}, Output CSV to: {OUTPUT_PATH}")
    # 啟動程式
    Application().start(PATH)
    # 連結至已啟動的程式
    app_instance = Application(backend="uia").connect(path=PATH)
    # 交由自定義的 CRW4Automation 物件管理
    crw4_automation = CRW4Automation(app_instance)
    logger.info("CRW4 application started successfully")
    return crw4_automation

class CRW4Mechanization(CRW4Automation):
    def __init__(self, app_instance):
        super().__init__(app_instance)
        self.output_path = OUTPUT_PATH

    def test(self, cas):
        try:
            result = crw4_automation.add_chemical(cas)
            return result
        except Exception as e:
            return {"status": 1, "result": e.args[0], "error": e.__class__.__name__}
    
    def automate_check(self, cas_list, id):
        cas_list = list(set(cas_list))
        crw4_automation.checked_mixture = False
        try:
            # 創建混合物
            crw4_automation.add_mixture(mixture_name=id)

            # 執行多筆檢查
            results = crw4_automation.multiple_check(cas_list)

            # 清空混合物
            crw4_automation.clear_mixture()

            # 寫入臨時 output.json 檔
            with open("output.json", 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=4)

            # 格式化結果後，寫入檔案
            formatted_check_result = crw4_automation.formate_check_output(id, results)
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
        crw4_automation.checked_mixture = False  # 防呆機制
        try:
            # 創建混合物
            crw4_automation.add_mixture(mixture_name=id)

            # 添加化學品
            results = crw4_automation.multiple_search(cas_list)

            # 輸出圖表
            crw4_automation.output_chart_to_csv()

            # 產生 Excel
            file_handler("xlsx", id=id)

            # 回到主頁面
            crw4_automation.click_button("Mixture\rManager")

            # 清空混合物
            crw4_automation.clear_mixture()

            # 整理輸出結果
            with open("output.json", 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=4)

            # 格式化結果後，寫入檔案
            formatted_result = crw4_automation.format_output(id, results)
            result = file_handler("json", formatted_result, id)

        except Exception as e:
            return {"id": id, "status": 1, "result": e.args[0], "error": e.__class__.__name__}

        return {
            "id": id,
            "status": result["result"],
            "result": f"Json文件成功保存到 {OUTPUT_PATH}"
        }


