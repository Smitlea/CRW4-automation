import time

import pyperclip

from logger import logger

class CRW4Automation:
    def __init__(self, app):
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
        

    @staticmethod
    def check_edit_field(edit_field, field_name):
        if edit_field.exists():
            logger.debug(f"{field_name} field found!")
        else:
            logger.error(f"{field_name} not found. Please check the auto_id and control_type.")
        return edit_field
