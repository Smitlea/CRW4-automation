from pywinauto import Application
import json

from logger import logger
from util import CRW4Automation

with open ("config.json", "r") as f:
    config = json.load(f)


PATH = config["CRW4_PATH"]
# 啟動CRW4應用程序
logger.info(f"Starting CRW4 application at {PATH}")
app = Application().start(PATH)
app = Application(backend="uia").connect(path=PATH)

crw4_automation = CRW4Automation(app)

logger.info("CRW4 application started successfully")

crw4_automation.set_edit_field("Field: Chemicals::y_gSearchName", "sodium")

crw4_automation.set_edit_field("Field: Chemicals::y_gSearchCAS", "7440-23-5" )

crw4_automation.set_edit_field("Field: Chemicals::y_gSearchUN", "1428")

crw4_automation.search()

# edit_field = main_window.child_window(auto_id="Field: Chemicals::y_gSearchName", control_type="Edit")

