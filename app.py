from flask_restx import Resource
from logger import logger

from payload import (
    api_ns, api, app, api_test,
    task_id_output,
    queue_list_payload,
    add_chemical_input_payload
)
from tasks import CRW4Mechanization,start_crw4_application
from util import handle_request_exception

mechanization = CRW4Mechanization(start_crw4_application())
        
@api.route("/auto")
class Auto(Resource):
    @handle_request_exception
    @api.expect(queue_list_payload)
    @api.marshal_with(task_id_output)
    def post(self):
        data = api.payload
        cas_list = data.get("cas_list")
        id = data.get("id")
        try:
            result = mechanization.automate(cas_list=cas_list, id=id)
            return {'status': 0, "result": result}
        except Exception as e:
            return {"status": 1, "result": e.args[0], "error": e.__class__.__name__}


@api.route("/check")
class Check(Resource):
    @handle_request_exception
    @api.expect(queue_list_payload)
    @api.marshal_with(task_id_output)
    def post(self):
        data = api.payload
        cas_list = data.get("cas_list")
        id = data.get("id")
        try:
            result = mechanization.automate_check(cas_list=cas_list, id=id)
            return {'status': 0, "result": result}
        except Exception as e:
            return {"status": 1, "result": e.args[0], "error": e.__class__.__name__}

@api.route("/add")
class Add(Resource):
    @handle_request_exception
    @api.expect(add_chemical_input_payload)
    @api.marshal_with(task_id_output)
    def post(self):
        data = api.payload
        cas = data.get("cas")
        try:
            result = mechanization.test(cas=cas)
            return result
        except Exception as e:
            return {"status": 1, "result": e.args[0], "error": e.__class__.__name__}

    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000", debug=False, use_reloader=False)
