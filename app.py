import json
import os
import shutil
import time


from pywinauto import Application
from flask_restx import Resource

from logger import logger
from model import DatabaseManager, TestTable
from payload import (
    api_ns, api, app, 
    cas_list_payload,
    add_chemical_input_payload, 
    general_output_payload,
    new_mixture_payload
)
from util import CRW4Automation, handle_request_exception

with open ("config.json", "r") as f:
    config = json.load(f)
PATH = config["CRW4_PATH"]
EXCEL_PATH = config["EXCEL_PATH"]


db_manager = DatabaseManager()

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
    @api.marshal_with(general_output_payload)
    def post(self):
        data = api.payload
        mixture = data.get("mixture")
        try:
            result = crw4_automation.add_mixture(mixture)
            return result
        except Exception as e:
            return {"status": 1, "result": "", "error": str(e)}
        
@api_ns.route("/insert")
class insert(Resource):
    @handle_request_exception
    @api.expect(cas_list_payload)
    @api.marshal_with(general_output_payload)
    def post(self):
        data = api.payload
        cas_list = data.get("cas_list")
        try:
            with DatabaseManager().Session() as session:
                session.query(TestTable).delete()
                for cas in cas_list:
                    if not session.query(TestTable).filter_by(cas=cas).first():
                        new_cas = TestTable(cas=cas)
                        result = session.add(new_cas)
                        logger.debug(f"CAS number {cas} result: {result}")
                session.commit()
            return {"status": 0, "result": "CAS numbers inserted successfully"}
        except Exception as e:
            return {"status": 1, "result": e.args[0], "error": e.__class__.__name__}

@api_ns.route("/search")
class search(Resource):
    @handle_request_exception
    @api.marshal_with(general_output_payload)
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
    @api.expect(add_chemical_input_payload)
    @api.marshal_with(general_output_payload)
    def post(self):
        data = api.payload
        cas = data.get("cas")
        try:
            result = crw4_automation.add_chemical(cas)
            return result
        except Exception as e:
            return {"status": 1, "result": "", "error": str(e)}

@api_ns.route("/multiple_search")
class muiltiple_search(Resource):
    @api.marshal_with(general_output_payload)
    @handle_request_exception
    def get(self):
        crw4_automation.checked_mixture = False
        with DatabaseManager().Session() as session:
            chemicals = session.query(TestTable).all()
            if not chemicals:
                return {"status": 1, "result": "No CAS numbers found in the database", "error": ""}
            results = []
            for chemical in chemicals:
                cas = chemical.cas
                logger.debug(f"Searching for CAS number: {cas}")
                try:
                    result = crw4_automation.add_chemical(cas)
                    if result["status"] == 3:
                        results.append({"status": 1, "result":"使用者尚未選取化合物"})
                        break
                    results.append({"cas": cas, "status": result["status"], "result": result['result']})
                except Exception as e:
                    results.append({"cas": cas, "status": 1, "error": str(e)})
        return {"cas":cas, "result": results}


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
            time.sleep(5)
            path = PATH.split("\\")[0] + "\\CRW4\\CRW_Data_Export.xlsx"
            logger.debug(f"複製文件: {EXCEL_PATH}")

            if not os.path.exists(path):
                logger.error(f"路徑:{path} csv創建文件失敗")
                return {"status": 1, "result": "", "error": "csv創建文件失敗"}
            
            if not os.path.exists(EXCEL_PATH) :
                os.makedirs(EXCEL_PATH) 
            
            destination_path  = os.path.join(EXCEL_PATH, "CRW_Data_Export.xlsx")
            if not os.path.isfile(path):
                return {"status": 1, "result": "", "error": "文件不存在或不可讀"}
            with open(path, 'rb') as src_file:
                with open(destination_path, 'wb') as dst_file:
                    shutil.copyfileobj(src_file, dst_file)
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

