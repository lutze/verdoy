import config
import json

from flask import Blueprint, jsonify, request, g

from utils.utils import generic_api_requests

activities = Blueprint(name="activities", import_name=__name__)


@activities.route("/", methods=["POST"], strict_slashes=False)
def create_activity():
    try:

        request_body = request.get_json()

        is_success, response = generic_api_requests(
            "post", config.URL_ACTIVITIES, request_body
        )

        response_body = {
            "success": is_success,
            "data": response["json"] if is_success else {"message": str(response)},
        }

        return jsonify(response_body)

    except Exception as error:

        response_body = {
            "success": 0,
            "data": {"message": "Error : {}".format(error)},
        }

        return jsonify(response_body), 400