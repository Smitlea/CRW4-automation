import time
import json

from celery import Celery, Task
from celery.signals import worker_process_init
from tqdm.tk import trange

from logger import logger
from pywinauto import Application
from util import CRW4Automation


Celery_app = Celery(
    __name__,
    broker_connection_retry_on_startup=True,
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

with open ("config.json", "r") as f:
    config = json.load(f)
PATH = config["CRW4_PATH"]
OUTPUT_PATH = config["OUTPUT_PATH"]
    
crw4_automation = None
def start_crw4_application():
    global crw4_automation
    if crw4_automation is None:
        logger.info(f"Starting CRW4 Launching from: {PATH}, Output CSV to: {OUTPUT_PATH}")
        Application().start(PATH)
        app_instance = Application(backend="uia").connect(path=PATH)
        crw4_automation = CRW4Automation(app_instance)
        logger.info("CRW4 application started successfully")
    else:
        logger.info("CRW4 application already running")

class CRW4Add(Task):
    def run(self, cas):
        try:
            result = crw4_automation.add_chemical(cas)
            return result
        except Exception as e:
            return {"status": 1, "result": e.args[0], "error": e.__class__.__name__}

class CRW4AutoSelect(Task):
    def run(self, cas_list, id):
        results = []

        logger.debug(cas_list)
        for i in trange(len(cas_list)):
            try:
                cas = cas_list[i]
                result = crw4_automation.add_chemical(cas)
                self.update_state(state='processing', meta={'current': i, 'total': len(cas_list)})
                print((f"Adding chemical: {cas} result :{result}"))
                logger.debug(f"Adding chemical: {cas} result :{result}")
                if result["status"] == 3:
                    return {"status": 1, "result":"使用者尚未選取化合物"}
                results.append({"cas": cas, "status": result["status"], "result": result['result']})
            except Exception as e:
                results.append({"cas": cas, "status": 1, "error": str(e)})
                
        return {"id":id ,'status': 'complete', "result": result}



CRW4Auto = Celery_app.register_task(CRW4AutoSelect())
CRW4add = Celery_app.register_task(CRW4Add())


@worker_process_init.connect
def initialize_crw4_automation(**kwargs): 
    logger.info("Initializing CRW4 Automation")
    start_crw4_application()

@Celery_app.task(bind=True)
def count(self):
    for i in range(20):
        self.update_state(status='PROGRESS', meta={'current': i, 'total': 20})
        time.sleep(1)
    return {'status': 'complete'}


#Celery_register = Celery_app.register_task(MyCelery())

# Register a task in the task registry.
# The task will be automatically instantiated if not already an instance. Name must be configured prior to registration.
