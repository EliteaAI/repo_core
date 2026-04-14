#!/usr/bin/python3
# coding=utf-8
# pylint: disable=C0411

""" Event """

import time

# pylint: disable=E0401
from tools import web


class Event:  # pylint: disable=R0903,E1101
    """ Event """

    @web.event("bootstrap_runtime_info")
    def bootstrap_runtime_info(self, context, event, payload):  # pylint: disable=R0914
        """ Handler """
        _ = context, event
        #
        if not isinstance(payload, dict):
            return
        #
        pylon_id = payload.get("pylon_id", "")
        #
        if not pylon_id:
            return
        #
        data = payload.copy()
        data["timestamp"] = time.time()
        self.remote_runtimes[pylon_id] = data

    @web.event("bootstrap_runtime_info_prune")
    def bootstrap_runtime_info_prune(self, context, event, payload):  # pylint: disable=R0914
        """ Handler """
        _ = context, event
        #
        if not isinstance(payload, dict):
            return
        #
        pylon_id = payload.get("pylon_id", "")
        #
        if not pylon_id:
            return
        #
        self.remote_runtimes.pop(pylon_id, None)
