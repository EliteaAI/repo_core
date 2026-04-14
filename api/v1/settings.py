#!/usr/bin/python3
# coding=utf-8

""" API """

import flask  # pylint: disable=E0401
from flask_restful import Resource  # pylint: disable=E0401

from tools import this  # pylint: disable=E0401


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
        return {"settings": this.descriptor.state.get("repo_core_settings", "")}

    def post(self):
        """ POST """
        if not this.module.user_has_role(role="admin"):
            return {"ok": False}
        #
        data = flask.request.json
        #
        this.descriptor.state["repo_core_settings"] = data["settings"]
        this.descriptor.save_state()
        #
        return {"ok": True}
