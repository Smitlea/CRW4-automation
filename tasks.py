import time
import os
import json
import datetime

from dotenv import load_dotenv
from celery import Celery, Task
from celery.signals import worker_process_init

from logger import logger
from pywinauto import Application
from util import CRW4Automation

load_dotenv()
#broker是用來傳遞任務的訊息代理，backend是用來存儲任務執行結果的資料庫，兩者可以是相同的
Celery_app = Celery(
    __name__,
    include=['tasks'],
    broker_connection_retry_on_startup=True,
    broker=os.environ.get("redis_broker"),
    backend=os.environ.get("redis_broker")
)

with open ("config.json", "r") as f:
    config = json.load(f)
PATH = config["CRW4_PATH"]
OUTPUT_PATH = config["OUTPUT_PATH"]
    
crw4_automation = None
    
class CRW4Add(Task):
    def run(self, cas):
        try:
            result = crw4_automation.add_chemical(cas)
            return result
        except Exception as e:
            return {"status": 1, "result": e.args[0], "error": e.__class__.__name__}

class CRW4Task(Task):
    def run(self, cas_list, id):
        cas_list = list(set(cas_list))
        crw4_automation.checked_mixture = False #防呆機制
        try:
            #創建混合物
            crw4_automation.add_mixture(mixture_name=id)
            #添加化學品
            results = crw4_automation.multiple_search(cas_list) 
            #輸出圖表
            crw4_automation.output_chart_to_csv()
            #回到主頁面
            crw4_automation.click_button("Mixture\rManager")
            #清空混合物
            crw4_automation.clear_mixture()
            #整理輸出結果
            formatted_result = crw4_automation.format_output(id, results)
            current_time = datetime.datetime.now().strftime("%Y%m%d")
            #創建data資料夾
            if not os.path.exists(OUTPUT_PATH) :
                os.makedirs(OUTPUT_PATH) 
            #存到data 範例"data\SDS_911058_001_20240826.json" 
            destnation_path = f"{OUTPUT_PATH}\SDS_911058_{id}_{current_time}.json"
            with open(destnation_path, 'w', encoding='utf-8') as f:
                json.dump(formatted_result, f, ensure_ascii=False, indent=4)
        except Exception as e:
            return {"id":id ,'status': 1, "result": e.args[0], "error": e.__class__.__name__}
        
        return {"id":id ,'status': 0, "result": f"Json文件成功保存到{OUTPUT_PATH}"}



CRW4Auto = Celery_app.register_task(CRW4Task())
CRW4add = Celery_app.register_task(CRW4Add())

#當worker啟動時，初始化CRW4應用程式
@worker_process_init.connect
def initialize_crw4_automation(**kwargs): 
    if crw4_automation is None:
        start_crw4_application()

@Celery_app.task(bind=True)
def count(self):
    for i in range(20):
        self.update_state(status='PROGRESS', meta={'current': i, 'total': 20})
        time.sleep(1)
    return {'status': 'complete'}


def start_crw4_application():
    global crw4_automation
    logger.info(f"Starting CRW4 Launching from: {PATH}, Output CSV to: {OUTPUT_PATH}")
    Application().start(PATH)
    app_instance = Application(backend="uia").connect(path=PATH)
    crw4_automation = CRW4Automation(app_instance)
    logger.info("CRW4 application started successfully")

# def check_CRW4_connection():
#     if crw4_automation is None:
#         try:
#             logger.info("CRW4 application not running, starting now")
#             app_instance=Application(backend="uia").connect(path=PATH)
#             main_window=Application().connect(title_re="CRW4.*")
#             crw4_automation = CRW4Automation(app_instance, window=main_window)
#         except Exception as e:
#             logger.error(f"Failed to connect to CRW4 application, whether celery is not active or application init failed: {e}")
#             return {"status": 1, "result": "", "error": e}
#     return {"status": 0, "result": "CRW4 application connected successfully", "error": ""}