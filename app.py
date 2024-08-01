import json
import os
import shutil
import time


from pywinauto import Application
from flask_restx import Resource

from logger import logger
from models import api_ns, api, app, insert_input_payload, insert_output_payload, search_output_payload, mulitple_output_payload, new_mixture_payload, new_mixture_output_payload
from util import CRW4Automation, handle_request_exception

with open ("config.json", "r") as f:
    config = json.load(f)
PATH = config["CRW4_PATH"]
EXCEL_PATH = config["EXCEL_PATH"]

crw4_automation = None

def start_crw4_application():
    global crw4_automation
    if crw4_automation is None:
        logger.info(f"Starting CRW4 application at {PATH}")
        app_instance = Application().start(PATH)
        app_instance = Application(backend="uia").connect(path=PATH)
        crw4_automation = CRW4Automation(app_instance)
        logger.info("CRW4 application started successfully")
        logger.info(f"CRW4 PATH: {PATH}")
        logger.info(f"EXCEL PATH: {EXCEL_PATH}")
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
        
@api_ns.route("/add_chemical")
class add_chemical(Resource):
    @handle_request_exception
    @api.expect(insert_input_payload)
    @api.marshal_with(mulitple_output_payload)
    def post(self):
        data = api.payload
        cas = data.get("cas")
        try:
            result = crw4_automation.add_chemical(cas)
            return result
        except Exception as e:
            return {"status": 1, "result": "", "error": str(e)}


### Developing : multiple_search
@api_ns.route("/multiple_search")
class muiltiple_search(Resource):
    @api.expect(insert_input_payload)
    @api.marshal_with(mulitple_output_payload)
    @handle_request_exception
    def post(self):
        data = api.payload
        cas = data.get("cas")
        try:
            result = crw4_automation.add_chemical(cas)
            if result["status"] != 0:
                pass
            return result
        except Exception as e:
            return {"status": 1, "result": "", "error": str(e)}   

@api_ns.route("/show")
class show(Resource):
    @handle_request_exception
    def get(self):
        result = crw4_automation.show()
        return {"status": 0,"result": result, "error": ""}
    
@api_ns.route("/output_to_csv")
class test(Resource):
    @handle_request_exception
    def get(self):
        try:
            result = crw4_automation.output_chart_to_csv()
            time.sleep(3)
            path = PATH.split("\\")[0] + "\\CRW4\\CRW_Data_Export.xlsx"
            logger.debug(f"複製文件: {EXCEL_PATH}")
            if not os.path.exists(path):
                logger.error(f"路徑:{path} csv創建文件失敗")
                return {"status": 1, "result": "", "error": "csv創建文件失敗"}
            if not os.path.exists(EXCEL_PATH) :
                os.makedirs(EXCEL_PATH) 
            destination_path  = os.path.join(EXCEL_PATH, "CRW_Data_Export.xlsx")
            shutil.copy2(PATH, destination_path)
            logger.info("csv創建文件成功")
        except Exception as e:
            return {"status": 1, "result": "", "error": str(e)}
        return result

    
if __name__ == "__main__":
    # Start the CRW4 application only once, prevent multiple instances
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_crw4_application()
    app.run(host="0.0.0.0", port="5000", debug=True)
# logger.warning("Listing properties of the search results field")
# crw4_automation.show()


# edit_field = main_window.child_window(auto_id="Field: Chemicals::y_gSearchName", control_type="Edit")

