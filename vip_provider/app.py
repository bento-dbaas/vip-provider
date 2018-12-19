import json
from traceback import print_exc
from bson import json_util
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from mongoengine import connect
from vip_provider.settings import APP_USERNAME, APP_PASSWORD, \
    MONGODB_PARAMS, MONGODB_DB
from vip_provider.providers import get_provider_to


app = Flask(__name__)
auth = HTTPBasicAuth()
cors = CORS(app)
connect(MONGODB_DB, **MONGODB_PARAMS)


@auth.verify_password
def verify_password(username, password):
    if APP_USERNAME and username != APP_USERNAME:
        return False
    if APP_PASSWORD and password != APP_PASSWORD:
        return False
    return True


@app.route(
    "/<string:provider_name>/<string:env>/credential/new", methods=['POST']
)
@auth.login_required
def create_credential(provider_name, env):
    data = request.get_json()
    if not data:
        return response_invalid_request("No data".format(data))

    try:
        provider_cls = get_provider_to(provider_name)
        provider = provider_cls(env)
        success, message = provider.credential_add(data)
    except Exception as e:
        print_exc()  # TODO Improve log
        return response_invalid_request(str(e))

    if not success:
        return response_invalid_request(message)
    return response_created(success=success, id=str(message))


@app.route(
    "/<string:provider_name>/credentials", methods=['GET']
)
@auth.login_required
def get_all_credential(provider_name):
    try:
        provider_cls = get_provider_to(provider_name)
        provider = provider_cls(None)
        return make_response(
            json.dumps(
                list(map(lambda x: x, provider.credential.all())),
                default=json_util.default
            )
        )
    except Exception as e:
        print_exc()  # TODO Improve log
        return response_invalid_request(str(e))


@app.route(
    "/<string:provider_name>/<string:env>/credential", methods=['GET']
)
@auth.login_required
def get_credential(provider_name, env):
    try:
        provider_cls = get_provider_to(provider_name)
        provider = provider_cls(env)
        credential = provider.credential.get_by(environment=env)
    except Exception as e:
        print_exc()  # TODO Improve log
        return response_invalid_request(str(e))

    if credential.count() == 0:
        return response_not_found('{}/{}'.format(provider_name, env))
    return make_response(json.dumps(credential[0], default=json_util.default))


@app.route("/<string:provider_name>/<string:env>/credential", methods=['PUT'])
@auth.login_required
def update_credential(provider_name, env):
    return create_credential(provider_name, env)


@app.route(
    "/<string:provider_name>/<string:env>/credential", methods=['DELETE']
)
@auth.login_required
def destroy_credential(provider_name, env):
    try:
        provider_cls = get_provider_to(provider_name)
        provider = provider_cls(env)
        deleted = provider.credential.delete()
    except Exception as e:
        print_exc()  # TODO Improve log
        return response_invalid_request(str(e))

    if deleted['n'] > 0:
        return response_ok()
    return response_not_found("{}-{}".format(provider_name, env))


@app.route("/<string:provider_name>/<string:env>/vip/new", methods=['POST'])
@auth.login_required
def create_vip(provider_name, env):
    data = request.get_json()
    group = data.get("group", None)
    port = data.get("port", None)

    if not(group and port):
        return response_invalid_request("Invalid data {}".format(data))

    try:
        provider_cls = get_provider_to(provider_name)
        provider = provider_cls(env)
        vip = provider.create_vip(group, port)
    except Exception as e:  # TODO What can get wrong here?
        print_exc()  # TODO Improve log
        return response_invalid_request(str(e))
    return response_created(identifier=str(vip.id), ip=vip.vip_ip)


@app.route(
    "/<string:provider_name>/<string:env>/vip/<string:identifier>",
    methods=['DELETE']
)
@auth.login_required
def delete_vip(provider_name, env, identifier):
    try:
        provider_cls = get_provider_to(provider_name)
        provider = provider_cls(env)
        provider.delete_vip(identifier)
    except Exception as e:  # TODO What can get wrong here?
        print_exc()  # TODO Improve log
        return response_invalid_request(str(e))
    return response_ok()


@app.route(
    "/<string:provider_name>/<string:env>/vip/<string:identifier>",
    methods=['GET']
)
@auth.login_required
def get_vip(provider_name, env, identifier):
    try:
        provider_cls = get_provider_to(provider_name)
        provider = provider_cls(env)
    except Exception as e:  # TODO What can get wrong here?
        print_exc()  # TODO Improve log
        return response_invalid_request(str(e))

    vip = provider.get_vip(identifier)
    if not vip:
        return response_not_found(identifier)
    return response_ok(**vip.get_json)


def response_invalid_request(error, status_code=500):
    return _response(status_code, error=error)


def response_not_found(identifier):
    error = "Could not found with {}".format(identifier)
    return _response(404, error=error)


def response_created(status_code=201, **kwargs):
    return _response(status_code, **kwargs)


def response_ok(**kwargs):
    if kwargs:
        return _response(200, **kwargs)
    return _response(200, message="ok")


def _response(status, **kwargs):
    content = jsonify(**kwargs)
    return make_response(content, status)
