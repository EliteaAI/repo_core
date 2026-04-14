#!/usr/bin/python3
# coding=utf-8

""" API """

import flask  # pylint: disable=E0401
from flask_restful import Resource  # pylint: disable=E0401

from tools import this, auth  # pylint: disable=E0401


# pylint: disable=R0903
class API(Resource):
    """ API """

    def __init__(self, module):
        self.module = module

    def get(self):
        """ GET """
        if not this.module.user_has_role(role="admin"):
            return {"ok": False}
        #
        result = []
        #
        for user in auth.list_users():
            user.pop("last_login", None)
            result.append(user)
        #
        return result

    def put(self):
        """ PUT """
        if not this.module.user_has_role(role="admin"):
            return {"ok": False}
        #
        data = flask.request.json
        #
        user_id = auth.add_user(data["email"], data["name"])
        auth.add_token(user_id, "repo")
        #
        return {"ok": True}

    def delete(self):
        """ DELETE """
        if not this.module.user_has_role(role="admin"):
            return {"ok": False}
        #
        data = flask.request.args
        #
        user_id = int(data["user_id"])
        #
        for token in auth.list_tokens(user_id):
            auth.delete_token(token["id"])
        #
        auth.delete_user(user_id)
        #
        return {"ok": True}

    def post(self):
        """ POST """
        if not this.module.user_has_role(role="admin"):
            return {"ok": False}
        #
        data = flask.request.json
        #
        user_id = int(data["user_id"])
        #
        user = auth.get_user(user_id)
        tokens = auth.list_tokens(user_id)
        #
        if tokens:
            token = auth.encode_token(tokens[0]["id"])
        else:
            token = ""
        #
        return {
            "ok": True,
            "user_id": user_id,
            "user_email": user["email"],
            "user_name": user["name"],
            "user_token": token,
        }

    def patch(self):
        """ PATCH """
        if not this.module.user_has_role(role="admin"):
            return {"ok": False}
        #
        data = flask.request.json
        #
        user_id = int(data["id"])
        #
        auth.update_user(user_id, data["name"])
        #
        return {"ok": True}
