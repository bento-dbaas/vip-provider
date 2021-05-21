# -*- coding: utf-8 -*-
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
from vip_provider.models import Vip


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
    vip_dns = data.get("vip_dns", None)
    equipments = data.get("equipments", None)

    if not(group and port):
        return response_invalid_request("Invalid data {}".format(data))

    try:
        provider_cls = get_provider_to(provider_name)
        provider = provider_cls(env)
        vip = provider.create_vip(group, port, equipments, vip_dns)
    except Exception as e:  # TODO What can get wrong here?
        print_exc()  # TODO Improve log
        return response_invalid_request(str(e))
    return response_created(identifier=str(vip.id), ip=vip.vip_ip)


@app.route("/<string:provider_name>/<string:env>/instance-group", 
           methods=['POST'])
@auth.login_required
def create_instance_group(provider_name, env):
    data = request.get_json()
    group = data.get("group", None)
    port = data.get("port", None)
    vip_dns = data.get("vip_dns", None)
    equipments = data.get("equipments", None)

    if not(group and port):
        return response_invalid_request("Invalid data {}".format(data))
    try:
        provider_cls = get_provider_to(provider_name)
        provider = provider_cls(env)
        vip = provider.create_instance_group(group, port, vip_dns, equipments)
    except Exception as e:  # TODO What can get wrong here?
        print_exc()  # TODO Improve log
        return response_invalid_request(str(e))
    return response_created(
        vip_identifier=str(vip[0].id),
        group_identifier=[str(x.id) for x in vip[1]])

@app.route("/<string:provider_name>/<string:env>/add-instance-group/<string:vip>", 
           methods=['POST'])
@auth.login_required
def add_instance_in_group(provider_name, env, vip):
    data = request.get_json()
    equipments = data.get("equipments", None)

    if not(equipments):
        return response_invalid_request("Invalid data {}".format(data))
    try:
        provider_cls = get_provider_to(provider_name)
        provider = provider_cls(env)
        vip = provider.add_instance_in_group(equipments, vip)
    except Exception as e:  # TODO What can get wrong here?
        print_exc()  # TODO Improve log
        return response_invalid_request(str(e))
    return response_ok()


@app.route("/<string:provider_name>/<string:env>/vip/<string:identifier>/reals", methods=['PUT'])
@auth.login_required
def update_vip_reals(provider_name, env, identifier):
    data = request.get_json()
    vip_reals = data.get("vip_reals", None)

    if not(vip_reals):
        return response_invalid_request("Invalid data {}".format(data))

    try:
        provider_cls = get_provider_to(provider_name)
        provider = provider_cls(env)
        vip = provider.update_vip_reals(vip_reals, identifier)
    except Exception as e:  # TODO What can get wrong here?
        print_exc()  # TODO Improve log
        return response_invalid_request(str(e))
    return response_ok(identifier=str(vip.id), ip=vip.vip_ip)


@app.route("/<string:provider_name>/<string:env>/vip/<string:vip_id>/reals", methods=['POST'])
@auth.login_required
def add_vip_real(provider_name, env, vip_id):
    data = request.get_json()
    real_id = data.get("real_id", None)
    port = data.get("port", None)

    if not(real_id and port and vip_id):
        return response_invalid_request("Invalid data {}".format(data))

    return _vip_real_action(
        'add_real',
        provider_name,
        env,
        vip_id,
        real_id,
        **{'port': port}
    )


@app.route("/<string:provider_name>/<string:env>/vip/<string:vip_id>/reals/<string:real_id>", methods=['DELETE'])
@auth.login_required
def remove_vip_real(provider_name, env, vip_id, real_id):
    return _vip_real_action(
        'remove_real',
        provider_name,
        env,
        vip_id,
        real_id
    )


@app.route("/<string:provider_name>/<string:env>/vip/healthy", methods=['POST'])
@auth.login_required
def get_vip_healthy(provider_name, env):
    data = request.get_json()
    vip_id = data.get("vip_id", None)

    if not(vip_id):
        return response_invalid_request("Invalid data {}".format(data))

    try:
        provider_cls = get_provider_to(provider_name)
        provider = provider_cls(env)
        vip = Vip.objects(id=vip_id).get()
        state = provider.get_vip_healthy(vip)
    except Exception as e:  # TODO What can get wrong here?
        print_exc()  # TODO Improve log
        return response_invalid_request(str(e))
    return response_ok(healthy=state)


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

def _vip_real_action(action, provider_name, env, vip_id, real_id, **kw):

    try:
        provider_cls = get_provider_to(provider_name)
        provider = provider_cls(env)
        vip = Vip.objects(id=vip_id).get()
        provider_action = getattr(provider, action)
        vip = provider_action(vip.target_group_id, real_id=real_id, **kw)
    except Exception as e:  # TODO What can get wrong here?
        print_exc()  # TODO Improve log
        return response_invalid_request(str(e))
    return response_ok()
