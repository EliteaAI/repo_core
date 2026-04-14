#!/usr/bin/python3
# coding=utf-8

""" API """

import time

import yaml  # pylint: disable=E0401
import flask  # pylint: disable=E0401
from flask_restful import Resource  # pylint: disable=E0401

from tools import this, log  # pylint: disable=E0401


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
        for pylon_id in list(sorted(this.module.remote_runtimes.keys())):
            data = this.module.remote_runtimes[pylon_id]
            #
            if time.time() - data["timestamp"] > 60:  # 4 announces missing (for 15s interval)
                this.module.remote_runtimes.pop(pylon_id, None)
                continue
            #
            result.append({"pylon_id": pylon_id})
        #
        return result

    def post(self):
        """ POST """
        if not this.module.user_has_role(role="admin"):
            return {"ok": False}
        #
        data = flask.request.json
        #
        pylon_id = data["pylon_id"]
        pylon_data = self.module.remote_runtimes[pylon_id]
        #
        action = data["action"]
        #
        if action == "load":
            pylon_settings = pylon_data.get("pylon_settings", {})
            config_data = yaml.dump(pylon_settings.get("active", ""))
            return {"config": config_data}
        #
        if action == "load_raw":
            pylon_settings = pylon_data.get("pylon_settings", {})
            config_data = pylon_settings.get("tunable", "")
            return {"config": config_data}
        #
        if action == "restart":
            log.info("Requesting pylon restart: %s", pylon_id)
            self.module.context.event_manager.fire_event(
                "bootstrap_runtime_update",
                {
                    "pylon_id": pylon_id,
                    "restart": True,
                    "pylon_pid": 1,
                },
            )
            return {"ok": True}
        #
        if action == "save":
            log.info("Requesting pylon config update: %s", pylon_id)
            self.module.context.event_manager.fire_event(
                "bootstrap_runtime_update",
                {
                    "pylon_id": pylon_id,
                    "actions": [
                        ["update_pylon_config", data["data"]],
                    ],
                    "restart": False,
                },
            )
            return {"ok": True}
        #
        return {"ok": False}
