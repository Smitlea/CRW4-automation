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
        self.id_mapping = {"1": "View: 393", "2": "Portal Row View 2"}
        self.start()
    
    def start(self):
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            self.main_window = self.app.window(title_re="CRW4.*")
            self.main_window.wait('visible', timeout=20)
            ok_button = self.main_window.child_window(title="OK", control_type="Button")
            ok_button.click() if ok_button.exists() else None
            
              
    def set_edit_field(self, auto_id, chemical_name):
        edit_field = self.main_window.child_window(auto_id=auto_id, control_type="Edit")
        self.check_if_field_found(edit_field, "Edit Field")
        pyperclip.copy(chemical_name) 
        edit_field.click_input()  
        edit_field.type_keys('^v') 
        current_text = edit_field.get_value()
        if current_text != chemical_name:
            logger.error(f"Failed to set text in {auto_id}. Current text: '{current_text}'")
        logger.debug(f"Text '{chemical_name}' set successfully in {auto_id}!")

    def select(self, mapping_id):
        auto_id = self.id_mapping.get(mapping_id)
        if not auto_id:
            return logger.error(f"Mapping ID {mapping_id} not found in the id_mapping dictionary")
        target_item = self.main_window.child_window(auto_id=auto_id, control_type="DataItem")
        target_item.click_input()
        time.sleep(0.5)
        target_item.click_input()
        if self.main_window.child_window(title="No mixture selected", control_type="Window").exists(timeout=3):
            logger.warning("No mixture selected")
            return {"status":1, "message":"使用者尚未選取化合物，請創建化合物後再選取化學品"}
        else:
            logger.info(f"Selected item {mapping_id} successfully")
            return {"status":0, "message":"選取化學品成功"}


    def search(self):
        search_button = self.main_window.child_window(title="Search", control_type="Button")
        self.check_if_field_found(search_button, "Search Button")
        search_button.click()

    def click_button(self, title, control_type="Button", click_type="click", window=None):
        try:
            window = self.main_window if window == None else window
            logger.debug(f"window:{window}")
            button = window.child_window(title=title, control_type=control_type)
            if click_type == "click":
                button.click()
            elif click_type == "click_input":
                button.click_input()
            else:
                raise ValueError(f"Unsupported click_type: {click_type}")
            logger.info(f"{title} button clicked successfully")
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
            message = f"無相對應的資料: {status}"
            logger.warning(message)
            return {"status": 1, "message": message}
        
        if status != "1 chemical found exactly matching":
            message = f"找到複數筆資料: {status}"
            logger.warning(message)
            return {"status": 2, "message": message}
        
        chemical = legacy_value.split('>')[1].split('\\r')[0]
        message = f"找到一筆準確資料: {chemical}"
        logger.info(message)
        return {"status": 0, "message": message}

    
    def add_mixture(self, mixture_name):
        Mixture_botton = self.main_window.child_window(title="New Mixture", control_type="Button")
        Mixture_botton.click()
        edit_control = self.main_window.child_window(auto_id="IDC_SHOW_CUSTOM_MESSAGE_EDIT1", control_type="Edit")
        if not edit_control.is_visible() and edit_control.is_enabled():
            return {"status": 1, "error": "創建化合物視窗未彈出"}
        edit_control.set_edit_text(mixture_name)
        logger.info("Mixture control set successfully")
        ok_button = self.main_window.child_window(title="OK", control_type="Button")
        ok_button.click()
        logger.info("Mixture added successfully")
        return {"status": 0, "result": f"化合物{mixture_name}創建成功"}


    def list_properties(self, auto_id):
        control = self.main_window.child_window(auto_id=auto_id, control_type="Edit")
        legacy_value = control.legacy_properties().get("Value", None)
        logger.info(f"result message: {legacy_value}")
        # props = control.get_properties()
        # for prop, value in props.items():
        #     print(f"{prop}: {value}")

    @staticmethod
    def check_if_field_found(edit_field, field_name):
        if edit_field.exists():
            logger.debug(f"{field_name} field found!")
        else:
            logger.error(f"{field_name} not found. Please check the auto_id and control_type.")
        return edit_field
    

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