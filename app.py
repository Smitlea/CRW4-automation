import json
import os


from pywinauto import Application
from flask_restx import Resource

from logger import logger
from models import api_ns, api, app, insert_input_payload, insert_output_payload, search_output_payload, mulitple_output_payload, new_mixture_payload, new_mixture_output_payload
from util import CRW4Automation, handle_request_exception

with open ("config.json", "r") as f:
    config = json.load(f)
PATH = config["CRW4_PATH"]

crw4_automation = None

def start_crw4_application():
    global crw4_automation
    if crw4_automation is None:
        logger.info(f"Starting CRW4 application at {PATH}")
        app_instance = Application().start(PATH)
        app_instance = Application(backend="uia").connect(path=PATH)
        crw4_automation = CRW4Automation(app_instance)
        logger.info("CRW4 application started successfully")
    else:
        logger.info("CRW4 application already running")

@api_ns.route("/add_mixture")
class add_mixture(Resource):
    @handle_request_exception
    @api.expect(new_mixture_payload)
    @api.marshal_with(new_mixture_output_payload)
    def post(self):
        data = api.payload
        mixture = data.get("mixture")
        try:
            result = crw4_automation.add_mixture(mixture)
            return result
        except Exception as e:
            return {"status": 1, "result": "", "error": str(e)}
        
@api_ns.route("/select")
class select(Resource):
    @handle_request_exception
    def get(self):
        result = crw4_automation.select("1")
        return {"status": 0, "result": result, "error": ""}


@api_ns.route("/search")
class search(Resource):
    @handle_request_exception
    @api.marshal_with(search_output_payload)
    def get(self):
        try:
            crw4_automation.search()
            result = crw4_automation.check_search_results("Field: Chemicals::y_gSearchResults")
            logger.info(f"Search result: {result}")
            return {"status": 0, "result": result, "error": ""}
        except Exception as e:
            return {"status": 1, "result": "", "error": str(e)}
        
@api_ns.route("/muiltiple_search")
class muiltiple_search(Resource):
    @handle_request_exception
    @api.expect(insert_input_payload)
    @api.marshal_with(mulitple_output_payload)
    def post(self):
        data = api.payload
        cas = data.get("cas")
        try:
            crw4_automation.set_edit_field("Field: Chemicals::y_gSearchCAS", cas )
            crw4_automation.search()
            results = crw4_automation.check_search_results("Field: Chemicals::y_gSearchResults")
            if results["status"] != 0:
                return {"status": results["status"], "result": "", "error": results["message"]}
            result = crw4_automation.select("1")
            logger.info(f"Search result: {result}")
            return {"status": result["status"], "result": result["message"]}
        except Exception as e:
            return {"status": 1, "result": "", "error": str(e)}
        

@api_ns.route("/show")
class show(Resource):
    @handle_request_exception
    def get(self):
        result = crw4_automation.show()
        return {"status": 0,"result": result, "error": ""}
    
@api_ns.route("/test")
class test(Resource):
    @handle_request_exception
    def get(self):
        button = crw4_automation.main_window.child_window(title="Compatibility\rChart", control_type="Button")
        button.click()
        if crw4_automation.main_window.child_window(title="No mixture selected", control_type="Window").exists(timeout=3):
            logger.warning("No mixture selected")
            return {"status":1, "message":"使用者尚未選取化合物，請創建化合物後再產生列表"}
        header = crw4_automation.main_window.child_window(title="Header", control_type="Pane")
        crw4_automation.click_button("Export Chart Data", click_type="click", window=header) 
        Export_window = crw4_automation.main_window.child_window(title="Compatibility Chart Data Export", control_type="Window")
        crw4_automation.click_button("Proceed", click_type="click", window=Export_window) 
        crw4_automation.click_button("OK", click_type="click")  
        crw4_automation.click_button("Continue...", click_type="click")
        combo_box = crw4_automation.main_window.child_window(auto_id="IDC_EXPORT_ORDER_MENU", control_type="ComboBox")
        combo_box.expand()
        items = combo_box.descendants(control_type="ListItem")
        for item in items:
            logger.debug(f"item: {item.window_text()}")
            if item.window_text() == "   ChartMixInfoLink":
                item.click_input()
                break
        combo_box.collapse()
        crw4_automation.main_window.child_window(title='::CASNum', control_type="DataItem").click_input()
        if crw4_automation.main_window.child_window(title="» Move »", control_type="Button").is_enabled:
            crw4_automation.click_button("» Move »", click_type="click")
        crw4_automation.click_button("Export", click_type="click")
        return {"status": 0, "result": "success", "error": ""}

    
if __name__ == "__main__":
    # Start the CRW4 application only once, prevent multiple instances
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_crw4_application()
    app.run(host="0.0.0.0", port="5000", debug=True)
# logger.warning("Listing properties of the search results field")
# crw4_automation.show()


# edit_field = main_window.child_window(auto_id="Field: Chemicals::y_gSearchName", control_type="Edit")

