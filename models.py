from flask import Flask
from flask_restx import Api, Namespace, Resource, reqparse, fields

app = Flask("app")
api = Api(app, version='2.0.0', title='奇美CRW4 Automation API模擬', doc='/api/doc')
api_ns = Namespace("Systex", "all right reserve", path="/")
api.add_namespace(api_ns)

insert_input_payload = api_ns.model(
    "Insert Input",
    {
        "name": fields.String(required=True, default="sodium"),
        "cas": fields.String(required=True, default="7440-23-5"),
        "un": fields.String(required=True, default="1428"),
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

search_output_payload = api_ns.model(
    "Search Output",
    {
        "status": fields.Integer(
            required=True, description="0 for success, 1 for failure", default=1
        ),
        "result": fields.String(required=True, default="1"),
        "error": fields.String(required=False, default=""),
    },
)



