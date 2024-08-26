import json

from flask import request
from flask_restx import Resource
from celery.result import AsyncResult
from tqdm.tk import trange
from pywinauto import Application

from logger import logger
from payload import (
    api_ns, api, app, api_test,
    cas_list_payload,
    task_id_output,
    queue_list_payload,
    add_chemical_input_payload, 
    general_output_payload,
    new_mixture_payload
)
from tasks import CRW4Auto, Celery_app, CRW4add, count
from celery.app.control import Inspect
from util import handle_request_exception

@api.route("/queue")
class Register(Resource):
    @handle_request_exception
    @api.expect(queue_list_payload)
    @api.marshal_with(task_id_output)
    def post(self):
        data = api.payload
        cas_list = data.get("cas_list")
        id = data.get("id")
        try:
            task = CRW4Auto.apply_async((cas_list ,id))

            logger.info(f"Task created ID:{task.id}")
            return {'status': 0,'task_id': task.id}
        except Exception as e:
            return {"status": 1, "result": e.args[0], "error": e.__class__.__name__}

@api.route("/search")
class Search(Resource):
    @handle_request_exception
    @api.marshal_with(task_id_output)
    def get(self):
        try:
            task = count.delay()
            logger.debug(task.id)
            i = Celery_app.control.inspect()
            # active_lst = insp.active()
            # for key in active_lst.keys():
            #     print(key)
            pending_tasks = i.reserved() or {}
            active_tasks = i.active() or {}
            scheduled_tasks = i.scheduled() or {}
            tasks_ahead = 1
            logger.debug(pending_tasks.items())
            logger.debug(active_tasks.items())
            logger.debug(scheduled_tasks.items())
            for worker, tasks in pending_tasks.items():
                for task in tasks:
                    if task['id'] == task.id:
                        break
                    tasks_ahead += 1
            return {'status': 0,'task_id': task.id, 'order': tasks_ahead}
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
            result = CRW4add.apply_async((cas,))
            return result
        except Exception as e:
            return {"status": 1, "result": e.args[0], "error": e.__class__.__name__}



@api.route('/result')
class Result(Resource):
    @api.doc(params={'task_id': 'input'})
    def get(self):
        getTask = request.args.get('task_id')
        result = AsyncResult(getTask, app=Celery_app)

        if result.state == 'PENDING' and result.info is None:
            logger.warning(f"task_id:{getTask} task is pending...")
            response = {
                'state': result.state,
                'current': result.current,
                'status': 'pending...'
            }
        elif result.state != 'SUCCESS':
            logger.warning("Task is processing")
            logger.debug(result)
            response = {
                'state': result.state,
                'current': result.info.get('current', 0) ,
                'total': result.info.get('total', 1) ,
            }
            if result.result:
                response['result'] = result.result
        else:
            response = {
                'state': result.state,
                'status': result.info if result.info else 'Task failed'
            }
        
        return response
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000", debug=True)

