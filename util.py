from functools import wraps
from flask_restx import abort
from http import HTTPStatus
from pywinauto import Application
from werkzeug.exceptions import BadRequest
import pyperclip

from logger import logger

class CRW4Automation:
    def __init__(self, app:Application):
        self.app = app
        self.main_window = None
        self.start()
    
    def start(self):
        self.main_window = self.app.window(title_re="CRW4.*")
        self.main_window.wait('visible', timeout=20)
        ok_button = self.main_window.child_window(title="OK", control_type="Button")
        ok_button.click()
    
    def set_edit_field(self, auto_id, text):
        edit_field = self.main_window.child_window(auto_id=auto_id, control_type="Edit")
        self.check_edit_field(edit_field, "Edit Field")
        pyperclip.copy(text) 
        edit_field.click_input()  
        edit_field.type_keys('^v') 
        current_text = edit_field.get_value()
        if current_text == text:
            logger.debug(f"Text '{text}' set successfully in {auto_id}!")
        else:
            logger.error(f"Failed to set text in {auto_id}. Current text: '{current_text}'")

    def search(self):
        search_button = self.main_window.child_window(title="Search", control_type="Button")
        search_button.click()

    def photo(self):
        pic = self.app.capture_as_image()
        print(pic)
        pic.save("D:\\Systex\\CRW4-automation")

    def show(self):
        result = self.main_window.print_control_identifiers(filename="D:\\Systex\\CRW4-automation\\control_identifiers.txt")
        logger.info(f"result message: {result}")
        return result
    
    def check_search_results(self, auto_id):
        control = self.main_window.child_window(auto_id=auto_id, control_type="Edit")
        legacy_value = control.legacy_properties().get("Value", None)
        status = legacy_value[0:legacy_value.find('g')+1]
        if status == "0 chemicals found exactly matching":
            return logger.warning(f"無相對應的資料: {status}")
        elif status !="1 chemical found exactly matching":
            return logger.warning(f"找到複數筆資料: {status}")
        
        chemical = legacy_value[legacy_value.find('>')+1:legacy_value.find('\\r')]
        logger.info(f"找到一筆準確資料:{chemical}")
        return f"找到一筆準確資料:{chemical}"


    def list_properties(self, auto_id):
        control = self.main_window.child_window(auto_id=auto_id, control_type="Edit")
        legacy_value = control.legacy_properties().get("Value", None)
        logger.info(f"result message: {legacy_value}")
        # props = control.get_properties()
        # for prop, value in props.items():
        #     print(f"{prop}: {value}")

    @staticmethod
    def check_edit_field(edit_field, field_name):
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