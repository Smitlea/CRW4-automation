import json
import os

from pywinauto import Application
from flask_restx import Resource

from logger import logger
from models import api_ns, api, app, insert_input_payload, insert_output_payload, search_output_payload
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

@api_ns.route("/insert")
class insert(Resource):
    @handle_request_exception
    @api.expect(insert_input_payload)
    @api.marshal_with(insert_output_payload)
    def post(self):
        data = api.payload
        chemical_name = data.get("name")
        cas = data.get("cas")
        un = data.get("un")
        try:
            crw4_automation.set_edit_field("Field: Chemicals::y_gSearchName", chemical_name)
            crw4_automation.set_edit_field("Field: Chemicals::y_gSearchCAS", cas )
            crw4_automation.set_edit_field("Field: Chemicals::y_gSearchUN", un)
            logger.info(f"Inserting chemical: {chemical_name}, CAS: {cas}, UN: {un} successfully")
            return {0, "insert successful", ""}
        except Exception as e:
            return {1, "", str(e)}


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
        
@api_ns.route("/show")
class show(Resource):
    @handle_request_exception
    def get(self):
        result = crw4_automation.show()
        return {"status": 0,"result": result, "error": ""}

if __name__ == "__main__":
    ## Start the CRW4 application only once, prevent multiple instances
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_crw4_application()
    app.run(host="0.0.0.0", port="5050", debug=True)
# logger.warning("Listing properties of the search results field")
# crw4_automation.show()


# edit_field = main_window.child_window(auto_id="Field: Chemicals::y_gSearchName", control_type="Edit")

