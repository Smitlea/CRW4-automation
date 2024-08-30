import json
import time
import os
import shutil

from functools import wraps
from flask_restx import abort
from http import HTTPStatus
from pywinauto import Application
from werkzeug.exceptions import BadRequest
from tqdm import tqdm
import pyperclip

from logger import logger

with open ("config.json", "r") as f:
    config = json.load(f)
PATH = config["CRW4_PATH"]
OUTPUT_PATH = config["OUTPUT_PATH"]

crw4_automation = None

class CRW4Automation:
    def __init__(self, app:Application, window=None):
        self.app = app
        self.main_window = window
        self.current_task = None  
        self.checked_mixture = False
        if self.main_window == None :
            self.start()
    
    def start(self):
        try:
            self.main_window = self.app.window(title_re="CRW4.*")
            self.main_window.wait('visible', timeout=20)
            self.click_button("OK")
        except Exception as e:
            logger.error(f"Failed to initialize CRW4 main window: {e}")
    
    def set_task(self, task):
        """
        這個功能是為了讓CRW4Automation能夠抓到Celery目前的進度所設置的
        """
        self.current_task = task

    def set_edit_field(self, auto_id, chemical_name):
        edit_field = self.main_window.child_window(auto_id=auto_id, control_type="Edit")
        pyperclip.copy(chemical_name) 
        edit_field.click_input()  
        edit_field.type_keys('^v') 
        current_text = edit_field.get_value()
        if current_text != chemical_name:
            logger.error(f"Word copy and past Failed to set text in {auto_id}. Current text: '{current_text}'")
        logger.debug(f"Text '{chemical_name}' set successfully in {auto_id}!")

    def click_button(self, title, control_type="Button", window=None):
        """根據標題(control identifiers)點擊按鈕 輸入方式click_buttion("標題")"""
        try:
            window = self.main_window if window == None else window
            button = window.child_window(title=title, control_type=control_type)
            button.click()
            logger.debug(f"{title} button clicked successfully")
        except Exception as e:
            logger.error(f"Error clicking {title} button: {e}")
            raise

    def show(self):
        """
        此功能僅供開發者使用，不會被使用者呼叫
        使用此功能將會創建一個control_identifiers.txt檔案
        裡面包含了所有的control identifiers
        方便開發者找到需要的control identifiers自動化行程
        """
        result = self.main_window.print_control_identifiers(filename="D:\\Systex\\CRW4-automation\\control_identifiers.txt")
        logger.info(f"result message: {result}")
        return result
    
    def check_search_results(self, cas):
        """檢查搜尋結果是否為一筆準確資料"""
        control = self.main_window.child_window(auto_id="Field: Chemicals::y_gSearchResults", control_type="Edit")
        legacy_value = control.legacy_properties().get("Value", "")
        status = legacy_value.split('g')[0] + 'g'

        if status == "0 chemicals found exactly matching":
            result = f"cas:{cas} 無相對應的資料"
            logger.warning(result)
            return {"status": 1, "result": result}
        
        if status != "1 chemical found exactly matching":
            result = f"cas:{cas} 找到複數筆資料"
            logger.warning(result)
            return {"status": 2, "result": result}
        
        chemical = legacy_value.split('>')[1].split('\\r')[0]
        result = f"cas:{cas} 找到一筆準確資料: {chemical}"
        logger.info(result)
        return {"status": 0, "result": result}

    def add_mixture(self, mixture_name):
        """
        新增化合物至CRW4 
        mixture_name:str
        """
        self.click_button("New Mixture") 
        edit_control = self.main_window.child_window(auto_id="IDC_SHOW_CUSTOM_MESSAGE_EDIT1", control_type="Edit")
        if not edit_control.is_visible() and edit_control.is_enabled():
            return {"status": 1, "error": "創建化合物視窗未彈出"}
        edit_control.set_edit_text(mixture_name)
        logger.info("Mixture control set successfully")
        self.click_button("OK")
        logger.info("Mixture added successfully")
        return {"status": 0, "result": f"化合物{mixture_name}創建成功"}

    def add_chemical(self, cas):
        """新增化學品至CRW4
        payload:{
            "cas": "7440-23-5"
        }
        
        output:{
            "status": 0, 
            "result": {"cas": "7440-23-5", "chemical_name": "soldium"},
            "error": ""
        }
        status 0=成功 1=失敗 2=找到複數筆資料 3=使用者尚未選取化合物
        """
        self.set_edit_field("Field: Chemicals::y_gSearchCAS", cas)
        self.click_button("Search") 
        result = self.check_search_results(cas)

        if result["status"] == 2 :
            result = {}
            logger.debug(f"cas:{cas}進入複數判定")
            for i in range(1, 11):
                control = self.main_window.child_window(title=f"Portal Row View {str(i)}", control_type="DataItem", found_index=0)
                chemical_field=control.child_window(auto_id="Field: SearchResults::OfficialChemicalName", control_type="Edit", found_index=0)
                if chemical_field.exists():
                    chemical_name = chemical_field.legacy_properties()['Value']
                    result[f"{cas}_{i}"] = chemical_name
                else:
                    logger.debug(f"{cas} 總共有 {i-1} 筆相同的資料")
                    break
            logger.info(f"cas 複數結果: {result}")
            return {"status": 2, "result": result}

        elif result["status"] != 0:
            logger.warning(f"Search result: {result}")
            return {"status": result["status"], "result": result["result"]}
        
        ##找到化學品視窗以點擊兩次
        ##portal_view有複數個相同名稱的視窗，所以指定index=0，也就是找到的第一個。
        portal_view = self.main_window.child_window(title="Portal View", control_type="Pane", found_index=0)
        target_item = portal_view.child_window(title="Portal Row View 1", control_type="DataItem")
        target_item.window().set_focus() ## developing
        target_item.click_input()

        ##防呆機制
        if not self.checked_mixture:
            logger.debug("檢查是否選取化學品")
            if self.main_window.child_window(title="No mixture selected", control_type="Window").exists(timeout=1):
                logger.warning("No mixture selected")
                return {"status": 3, "result": "使用者尚未選取化合物，請創建化合物後再選取化學品"}
            self.checked_mixture = True

        ##成功回傳化學品名稱及CAS
        ## v0.0.15 本來想要新增根據選取化合物裡面是否有相對名稱來判斷確定新增成功，但是發現CRW4化合物資料會根據ABCD順序排序，太複雜故先不做此判斷
        offical_name = self.main_window.child_window(auto_id="Field: SearchResults::OfficialChemicalName", control_type="Edit", found_index=0).legacy_properties()['Value']
        # chemical_name = self.main_window.child_window(auto_id="Field: MixtureInfo::ChemName", control_type="Edit").legacy_properties()['Value']
        # current_cas = self.main_window.child_window(auto_id="Field: MixtureInfo::CASNum", control_type="Edit").legacy_properties()['Value']

        # if current_cas == cas:
        logger.info("Selected item successfully")
        return {"status": 0, "result": {"cas": cas, "chemical_name": offical_name}}

        # logger.error(f"Failed to select item: {cas}")
        # return {"status": 1, "result": f"檢查到選取化學品 {chemical_name} 新增失敗"}

    def output_chart_to_csv(self):
        self.click_button("Compatibility\rChart")
        if self.main_window.child_window(title="No mixture selected", control_type="Window").exists(timeout=3):
            logger.warning("No mixture selected")
            return {"status":1, "result":"使用者尚未選取化合物，請創建化合物後再產生列表"}
        ###點選複數確認按鈕
        header = self.main_window.child_window(title="Header", control_type="Pane")
        self.click_button("Export Chart Data", window=header) 
        Export_window = self.main_window.child_window(title="Compatibility Chart Data Export", control_type="Window")
        self.click_button("Proceed", window=Export_window) 
        self.click_button("OK")  
        self.click_button("Continue...")
        ## 新增cas至輸出欄位
        combo_box = self.main_window.child_window(auto_id="IDC_EXPORT_ORDER_MENU", control_type="ComboBox")
        combo_box.expand()
        items = combo_box.descendants(control_type="ListItem")
        for item in items:
            if item.window_text() == "   ChartMixInfoLink":
                item.click_input()
                break
        combo_box.collapse()
        self.main_window.child_window(title='::CASNum', control_type="DataItem").click_input()
        if self.main_window.child_window(title="» Move »", control_type="Button").is_enabled:
            self.click_button("» Move »")
        self.click_button("Export")
        return {"status": 0, "result": "文件創建成功", "error": ""}

    def format_output(self, id, results):
        """Payload:
        id: str
        results: list  -> look output.json for example
        Output format
        {
            "id": "123456",
            "cas_list": [
                {
                    "status": 0,
                    "7440-23-5": "sodium"
                },
                {
                    "status": 1,
                    "7440-23-6": ""
                },
                {
                    "status": 2,
                    "7440-23-5_1": "NITRATING ACID, MIXTURE, (WITH <= 50% NITRIC ACID)"
                },
                {
                    "status": 2,
                    "7440-23-5_2": "NITRATING ACID, MIXTURE, (WITH > 50% NITRIC ACID)"
                },
            ]
        } 
        """
        formatted_result = {
            "id": id,  
            "cas_list": []
        }
        try:

            for item in results["result"]:
                status = item["status"]
                cas = item["cas"]
                
                if status == 0:
                    chemical_name = item["result"].get("chemical_name", "")
                    formatted_result["cas_list"].append({
                        "status": status,
                        cas: chemical_name
                    })
                elif status == 1:
                    formatted_result["cas_list"].append({
                        "status": status,
                        cas: ""
                    })
                elif status == 2:
                    result = item["result"]["result"]
                    for key, value in result.items():
                        formatted_result["cas_list"].append({
                            "status": status,
                            key: value
                        })
        except KeyError as e:
            logger.error(f"KeyError: {e} in item: {item}")
        except TypeError as e:
            logger.error(f"TypeError: {e} in item: {item}")
        except Exception as e:
            logger.error(f"Unexpected error: {e} in item: {item}")
        return formatted_result

    def clear_mixture(self):
        """在下一次使用之前將所有化學品全部刪除"""
        try:
            ##點擊化學品選取視窗
            dropdown_menu = self.main_window.child_window(control_type="Menu", auto_id="Field: Chemicals::y_gMixtureNameSelect")
            dropdown_menu.click_input()
            ###CRW4 這裡有個設計缺陷 在選取化學品的視窗和主視窗是分開的，所以要先選取路徑位置視窗才能找到裡面的MenuItem
            combobox = self.app.window(title_re="路徑位置")
            if not combobox.exists(timeout=1):
                return {"status": 1, "result": "刪除化學品時找不到路徑位置，可能是化學品選取視窗未完全開啟"}
            menu_items = combobox.children(control_type="MenuItem")
            for i in range(len(menu_items)-1):
                try: 
                    menu_item = combobox.child_window(auto_id="1", control_type="MenuItem")
                    if not menu_item.exists():
                        logger.debug(f"找不到第{i+1}個化學品MenuItem")
                        break
                    menu_item.click_input()
                    self.click_button("Delete  Mixture")
                    lock_window = self.main_window.child_window(title="This mixture is locked", control_type="Window")
                    if lock_window.exists():  ###CRW4 在化學品選項預設都會有個被鎖定的Reactive Group Matrix 這是偵測到鎖定時的例外處理
                        logger.debug(f"偵測到選擇為reactive matrix化學品被鎖定, 正在解鎖")
                        self.click_button("OK")
                        dropdown_menu.click_input()
                        menu_item = combobox.child_window(auto_id="2", control_type="MenuItem")
                        menu_item.click_input()
                        self.click_button("Delete  Mixture")
                    self.click_button("OK")
                    logger.info(f"成功刪除了第{i+1}個化學品")
                    dropdown_menu.click_input()

                except Exception as e:
                    logger.debug(f"{e.args[0]}.error:{e.__class__.__name__}")
            return {"status": 0, "result": "已清除所有化學品"}
        except Exception as e:
            return {"status": 1, "result": f"刪除化合物失敗: {e}" , "error": e.__class__.__name__}
  
    def multiple_search(self, cas_list):
        results = []
        i = 0
        for cas in tqdm(cas_list):
            try:
                result = self.add_chemical(cas)
                self.current_task.update_state(state='PROGRESS', meta={'current': i, 'total': len(cas_list)})
                i += 1
                logger.debug(f"Adding chemical: {cas} result: {result}")
                
                status = result.get("status")
                if status == 3:
                    return {"status": 1, "result": "使用者尚未選取化合物"}
                elif status == 2:
                    results.append({"cas": cas, "status": 2, "result": {key: result[key] for key in result if key != "status"}})
                else:
                    results.append({"cas": cas, "status": status, "result": result.get("result")})
            
            except Exception as e:
                results.append({"cas": cas, "status": 1, "error": str(e)})

        return {"status": 0, "result": results}


def handle_request_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BadRequest as bad_request:
            logger.error("Bad Request: %s", bad_request.data)
            return abort(
                HTTPStatus.BAD_REQUEST,
                "",
                error=bad_request.data,
                status=1,
                result=None,
            )
        except Exception as e:
            error_message = f"{e.__class__.__name__}: {e}"
            logger.error("An error occurred: %s", error_message)
            return abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "",
                error=error_message,
                status=1,
                result=None,
            )

    return wrapper

def file_handler(file_type: str, data=None, id=None):
    if file_type not in ["json", "xlsx"]:
        logger.error(f"Invalid file type: {file_type}")
        return {"status": 1, "result": "Invalid file type"}

    os.makedirs(OUTPUT_PATH, exist_ok=True)
    current_time = time.strftime("%Y%m%d")
    base_filename = f"SDS_911058_{id}_{current_time}"
    
    try:
        if file_type == "json":
            json_path = os.path.join(OUTPUT_PATH, "json")
            os.makedirs(json_path, exist_ok=True)
            destination_path = os.path.join(json_path, f"{base_filename}.json")
            with open(destination_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"JSON file successfully saved to {destination_path}")
            result = {"status": 0, "result": f"JSON file successfully saved to {destination_path}"}
        
        elif file_type == "xlsx":
            xlsx_path = os.path.join(OUTPUT_PATH, "xlsx")
            os.makedirs(xlsx_path, exist_ok=True)
            source_path = os.path.join(PATH.split("\\")[0], "\\CRW4", "CRW_Data_Export.xlsx")
            max_attempts = 5
            for attempt in range(max_attempts):
                if os.path.exists(source_path):
                    break
                logger.info(f"等待CRW4 xlsx文件創建 次數: {attempt + 1}/{max_attempts}")
                time.sleep(3)
            else:
                logger.error(f"Source file not found after {max_attempts} attempts")
                return {"status": 1, "result": "xlsx文件沒有被CRW4成功創建，等待時間逾時"}

            destination_path = os.path.join(xlsx_path, f"{base_filename}_CRW_Data_Export.xlsx")
            shutil.copy2(source_path, destination_path)
            logger.info(f"XLSX file successfully saved to {destination_path}")
            result = {"status": 0, "result": f"XLSX file successfully saved to {destination_path}"}

    except Exception as e:
        logger.error(f"Error saving file: {e}")
        result = {"status": 1, "result": f"Error saving file: {e}"}
    
    return result
