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
            result = crw4_automation.check_search_results("Field: Chemicals::y_gSearchResults")
            if result["status"] != 0:
                return {"status": result["status"], "result": "", "error": result["message"]}
            result1 = crw4_automation.select("1")
            logger.info(f"Search result: {result}")
            return {"status": result1["status"], "result": result1["message"]}
        except Exception as e:
            return {"status": 1, "result": "", "error": str(e)}
        

@api_ns.route("/show")
class show(Resource):
    @handle_request_exception
    def get(self):
        result = crw4_automation.show()
        return {"status": 0,"result": result, "error": ""}
    

if __name__ == "__main__":
    # Start the CRW4 application only once, prevent multiple instances
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_crw4_application()
    app.run(host="0.0.0.0", port="5000", debug=True)
# logger.warning("Listing properties of the search results field")
# crw4_automation.show()


# edit_field = main_window.child_window(auto_id="Field: Chemicals::y_gSearchName", control_type="Edit")

