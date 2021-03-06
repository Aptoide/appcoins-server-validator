import re

from flask import request
from flask_restx import Resource, abort, Namespace

import settings
from classes.api_validator import (
    APIValidator, APIValidatorException
)
from classes.cache import Cache
from classes.catappult_api import CatappultApi
from classes.purchase_entity import PurchaseEntity
from flaskws.example_dumper import ExampleDumper
from flaskws.example_parser import ExampleParser

example_api = Namespace("purchase", description="Purchase operations")
example_parser = ExampleParser()
catappult_api = CatappultApi(settings.CATAPPULT_API_HOST, Cache())
api_validator = APIValidator(catappult_api)
dumper = ExampleDumper()


def parse_purchase_check_url(url):
    match = re.fullmatch(
        r"http.*://(?P<domain>[0-9a-zA-Z.:-]+)/purchase/(?P<package>["
        r"0-9a-zA-Z.]+)/check",
        url)
    return match.group("domain"), match.group("package")


@example_api.route("/com.appcoins.trivialdrivesample/check")
@example_api.route("/com.appcoins.sample/check")
@example_api.route("/test.unity.serverside/check")
@example_api.route("/com.appcoins.trivialdrivesample.test/check")
class ExampleCheck(Resource):
    @example_api.expect(example_parser.get_parser_adder())
    @example_api.response(200, "Purchase successfully validated")
    @example_api.response(400, "Bad purchase input")
    @example_api.response(404, "Unable to find purchase")
    @example_api.response(503, "Service Unavailable")
    @example_api.response(504, "Gateway timeout")
    def get(self):
        args = example_parser.get_parser_adder().parse_args()
        _, package_name = parse_purchase_check_url(request.base_url)

        purchase = PurchaseEntity(package_name, args.token, args.product)

        if not purchase.package_name or not purchase.sku \
                or not purchase.purchase_token:
            abort(code=400, error="ERROR-400-1", status=None,
                  message="A valid purchase must be provided")

        try:
            raw_result = api_validator.validate(purchase)
            return dumper.get_output(raw_result)
        except APIValidatorException as e:
            abort(code=503, error="ERROR-503-1", status=None, message=str(e))
