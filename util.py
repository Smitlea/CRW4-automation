import time
import os

from functools import wraps
from flask_restx import abort
from http import HTTPStatus
from pywinauto import Application
from pywinauto.timings import Timings
from werkzeug.exceptions import BadRequest
import pyperclip

from logger import logger

class CRW4Automation:
    def __init__(self, app:Application):
        self.app = app
        self.main_window = None
        self.checked_mixture = False
        self.start()
    
    def start(self):
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            self.main_window = self.app.window(title_re="CRW4.*")
            self.main_window.wait('visible', timeout=20)
            ok_button = self.main_window.child_window(title="OK", control_type="Button")
            ok_button.click() if ok_button.exists() else None
                       
    def set_edit_field(self, auto_id, chemical_name):
        edit_field = self.main_window.child_window(auto_id=auto_id, control_type="Edit")
        pyperclip.copy(chemical_name) 
        edit_field.click_input()  
        edit_field.type_keys('^v') 
        current_text = edit_field.get_value()
        if current_text != chemical_name:
            logger.error(f"Word copy and past Failed to set text in {auto_id}. Current text: '{current_text}'")
        logger.debug(f"Text '{chemical_name}' set successfully in {auto_id}!")

    def select(self):
        portal_view = self.main_window.child_window(title="Portal View", control_type="Pane",found_index=0)
        target_item = portal_view.child_window(title="Portal Row View 1", control_type="DataItem")
        target_item.click_input()
        target_item.click_input()
        if not self.checked_mixture:
            logger.debug(f"檢查是否選取化學品")
            if self.main_window.child_window(title="No mixture selected", control_type="Window").exists(timeout=1):
                logger.warning("No mixture selected")
                return {"status":3, "result":"使用者尚未選取化合物，請創建化合物後再選取化學品"}
            else:
                self.checked_mixture = True
        logger.info(f"Selected item successfully")
        return {"status":0, "result":"選取化學品成功"}

    def click_button(self, title, control_type="Button", click_type="click", window=None):
        try:
            window = self.main_window if window == None else window
            button = window.child_window(title=title, control_type=control_type)
            if click_type == "click":
                button.click()
            else:
                raise ValueError(f"Unsupported click_type: {click_type}")
            logger.debug(f"{title} button clicked successfully")
        except Exception as e:
            logger.error(f"Error clicking {title} button: {e}")
            raise

    def show(self):
        result = self.main_window.print_control_identifiers(filename="D:\\Systex\\CRW4-automation\\control_identifiers.txt")
        logger.info(f"result message: {result}")
        return result
    
    def check_search_results(self, auto_id):
        control = self.main_window.child_window(auto_id=auto_id, control_type="Edit")
        legacy_value = control.legacy_properties().get("Value", "")
        status = legacy_value.split('g')[0] + 'g'

        if status == "0 chemicals found exactly matching":
            result = f"無相對應的資料"
            logger.warning(result)
            return {"status": 1, "result": result}
        
        if status != "1 chemical found exactly matching":
            result = f"找到複數筆資料"
            logger.warning(result)
            return {"status": 2, "result": result}
        
        chemical = legacy_value.split('>')[1].split('\\r')[0]
        result = f"找到一筆準確資料: {chemical}"
        logger.info(result)
        return {"status": 0, "result": result}

    def add_mixture(self, mixture_name):
        self.click_button("New Mixture", click_type="click") 
        edit_control = self.main_window.child_window(auto_id="IDC_SHOW_CUSTOM_MESSAGE_EDIT1", control_type="Edit")
        if not edit_control.is_visible() and edit_control.is_enabled():
            return {"status": 1, "error": "創建化合物視窗未彈出"}
        edit_control.set_edit_text(mixture_name)
        logger.info("Mixture control set successfully")
        self.click_button("OK", click_type="click")
        logger.info("Mixture added successfully")
        return {"status": 0, "result": f"化合物{mixture_name}創建成功"}

    def add_chemical(self, cas):
        self.set_edit_field("Field: Chemicals::y_gSearchCAS", cas )
        self.click_button("Search", click_type="click") 
        result = self.check_search_results("Field: Chemicals::y_gSearchResults")

        logger.debug(f"debug:{result}")
        if result["status"] == 0:
            result = self.select()
            logger.info(f"Search result: {result}")

        return {"status": result["status"], "result": result["result"]}

    def output_chart_to_csv(self):
        self.click_button("Compatibility\rChart", click_type="click")
        if self.main_window.child_window(title="No mixture selected", control_type="Window").exists(timeout=3):
            logger.warning("No mixture selected")
            return {"status":1, "result":"使用者尚未選取化合物，請創建化合物後再產生列表"}
        header = self.main_window.child_window(title="Header", control_type="Pane")
        self.click_button("Export Chart Data", click_type="click", window=header) 
        Export_window = self.main_window.child_window(title="Compatibility Chart Data Export", control_type="Window")
        self.click_button("Proceed", click_type="click", window=Export_window) 
        self.click_button("OK", click_type="click")  
        self.click_button("Continue...", click_type="click")
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
            self.click_button("» Move »", click_type="click")
        self.click_button("Export", click_type="click")
        return {"status": 0, "result": "文件創建成功", "error": ""}

    def list_properties(self, auto_id):
        control = self.main_window.child_window(auto_id=auto_id, control_type="Edit")
        legacy_value = control.legacy_properties().get("Value", None)
        logger.info(f"result message: {legacy_value}")
        # props = control.get_properties()
        # for prop, value in props.items():
        #     print(f"{prop}: {value}")

    

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