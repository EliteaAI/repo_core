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
        result = []
        #
        with this.module.task_node.lock:
            for state in this.module.task_node.global_task_state.values():
                meta = state.get("meta", None)
                if meta is not None:
                    meta = str(meta)
                #
                status = state.get("status", None)
                #
                result.append({
                    "task_id": state.get("task_id", None),
                    "requestor": state.get("requestor", None),
                    "runner": state.get("runner", None),
                    "status": status,
                    "meta": meta,
                    "node": f"{this.module_name}.task_node",
                })
        #
        return result

    def put(self):
        """ PUT """
        if not this.module.user_has_role(role="admin"):
            return {"ok": False}
        #
        data = flask.request.json
        #
        task_name = data["task"]
        #
        task_id = this.module.task_node.start_task(
            task_name,
            kwargs={
                "param": data["param"],
            },
            pool="repo",
            meta={
                "task": task_name,
            },
        )
        #
        return {"ok": task_id is not None}

    def delete(self):
        """ DELETE """
        if not this.module.user_has_role(role="admin"):
            return {"ok": False}
        #
        data = flask.request.args
        #
        this.module.task_node.stop_task(data["task_id"])
        #
        return {"ok": True}
