import json
import os
import shutil
import time
import datetime

from pywinauto import Application
from flask_restx import Resource
from dotenv import load_dotenv

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

load_dotenv()

with open ("config.json", "r") as f:
    config = json.load(f)

def get_absolute_path(relative_path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))

PATH = config["CRW4_PATH"]
OUTPUT_PATH = config["OUTPUT_PATH"]
# EXCEL_PATH = get_absolute_path(os.environ.get("EXCEL_PATH"))
db_manager = DatabaseManager()

crw4_automation = None

def start_crw4_application():
    global crw4_automation
    if crw4_automation is None:
        logger.info(f"Starting CRW4 Launching from: {PATH}, Output CSV to: {OUTPUT_PATH}")
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
    @api.marshal_with(general_output_payload)
    def post(self):
        data = api.payload
        mixture = data.get("mixture")
        try:
            result = crw4_automation.add_mixture(mixture)
            return result
        except Exception as e:
            return {"status": 1, "result": e.args[0], "error": e.__class__.__name__}
        
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
                        session.add(new_cas)
                session.commit()
                logger.info(f"{len(cas_list)} item's update successfully")
            return {"status": 0, "result": "CAS numbers inserted successfully"}
        except Exception as e:
            return {"status": 1, "result": e.args[0], "error": e.__class__.__name__}
        
@api_ns.route("/start")
class start(Resource):
    @handle_request_exception
    @api.marshal_with(general_output_payload)
    def get(self):
        start_crw4_application()
        return {"status": 0, "result": "CRW4 application started successfully", "error": ""}

# @api_ns.route("/search")
# class search(Resource):
#     @handle_request_exception
#     @api.marshal_with(general_output_payload)
#     def get(self):
#         try:
#             crw4_automation.search()
#             result = crw4_automation.check_search_results("Field: Chemicals::y_gSearchResults")
#             logger.info(f"Search result: {result}")
#             return {"status": 0, "result": result, "error": ""}
#         except Exception as e:
#             return {"status": 1, "result": e.args[0], "error": e.__class__.__name__}

        
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
            return {"status": 1, "result": e.args[0], "error": e.__class__.__name__}


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
                        return {"status": 1, "result":"使用者尚未選取化合物"}
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
            current_time = datetime.datetime.now().strftime("%Y%m%d")

            ##檢查csv是否有被CRW4成功創建
            if not os.path.exists(path):
                logger.error(f"路徑:{path} csv創建文件失敗")
                return {"status": 1, "result": "", "error": "csv創建文件失敗"}
            
            ##創建輸出資料夾
            if not os.path.exists(OUTPUT_PATH) :
                os.makedirs(OUTPUT_PATH) 

            logger.debug(f"複製文件: {path}至 {OUTPUT_PATH}")

            destination_path  = os.path.join(OUTPUT_PATH,  f"{current_time} CRW_Data_Export.xlsx")
            
            if not os.path.isfile(path):
                return {"status": 1, "result": "", "error": "文件不存在或不可讀"}
            shutil.copy2(path, destination_path)
            logger.info(f"文件成功複製到 {destination_path}")
        except Exception as e:
            return {"status": 1, "result": e.args[0], "error": e.__class__.__name__}

        return result

    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000", debug=True)
# logger.warning("Listing properties of the search results field")
# crw4_automation.show()


# edit_field = main_window.child_window(auto_id="Field: Chemicals::y_gSearchName", control_type="Edit")

