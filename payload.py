from flask import Flask
from flask_restx import Api, Namespace, Resource, reqparse, fields

app = Flask("app")
api = Api(app, version='2.0.0', title='奇美CRW4 Automation API模擬', doc='/api/doc')
api_ns = Namespace("Systex", "all right reserve", path="/")
api.add_namespace(api_ns)

add_chemical_input_payload = api_ns.model(
    "Insert Input",
    {
        "cas": fields.String(required=True, default="7440-23-5")
    },
)
insert_output_payload = api_ns.model(
    "Insert Output",
    {
        "status": fields.Integer(
            required=True, description="0 for success, 1 for failure", default=1
        ),
        "result": fields.String(required=True, default="1"),
        "error": fields.String(required=False, default=""),
    },
)

new_mixture_payload = api_ns.model(
    "New Mixture",
    {
        "mixture": fields.String(required=True, default="氰化物")
    },
)
cas_list_payload = api_ns.model(
    "CAS List",
    {
        "cas_list": fields.List(fields.String, required=True, default=[
            "7761-88-8", "7784-27-2", "10043-35-3", "10022-31-8", "7440-69-9", 
            "471-34-1", "7440-43-9", "7440-48-4", "7789-09-5", "7440-50-8",
            "7697-37-2", "10043-35-3", "13138-45-9", "10141-05-6", "3251-23-8",
            "7779-88-6", "10325-94-7", "10099-74-8", "7761-88-8", "10102-45-1"
        ])
    },
)

general_output_payload = api_ns.model(
    "general Output",
    {
        "status": fields.Integer(
            required=True, description="0 for success, 1 for failure", default=1
        ),
        "result": fields.String(required=True, default="1"),
        "error": fields.String(required=False, default=""),
    },
)

