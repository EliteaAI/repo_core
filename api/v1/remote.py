#!/usr/bin/python3
# coding=utf-8

""" API """

import io
import json
import time
import zipfile

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
            runtime_info = data["runtime_info"]
            #
            for plugin in sorted(runtime_info, key=lambda x: x["name"]):
                item = plugin.copy()
                #
                item["pylon_id"] = pylon_id
                #
                item.pop("config", None)
                item.pop("config_data", None)
                #
                if "git_head" in item.get("metadata", {}):
                    item_version = item.get("local_version", "-")
                    item_git_head = item["metadata"]["git_head"][:7]
                    item["local_version"] = f"{item_version} ({item_git_head})"
                #
                result.append(item)
        #
        return result

    def post(self):  # pylint: disable=R0911,R0912,R0914,R0915
        """ POST """
        if not this.module.user_has_role(role="admin"):
            return {"ok": False}
        #
        # Form: export/import
        #
        if "action" in flask.request.form:
            action = flask.request.form["action"]
            #
            if action == "export_configs":
                data = json.loads(flask.request.form.get("data", "[]"))
                #
                # ---
                #
                targets = {}
                #
                for item in data:
                    pylon_id = item.get("pylon_id", "")
                    #
                    if not pylon_id:
                        continue
                    #
                    if pylon_id not in targets:
                        targets[pylon_id] = []
                    #
                    plugin_state = item.get("state", False)
                    plugin_name = item.get("name", "")
                    #
                    if not plugin_state or not plugin_name:
                        continue
                    #
                    if plugin_name not in targets[pylon_id]:
                        targets[pylon_id].append(plugin_name)
                #
                # ---
                #
                file_obj = io.BytesIO()
                #
                with zipfile.ZipFile(file_obj, mode="w", compression=zipfile.ZIP_DEFLATED) as zfile:
                    for pylon_id in list(sorted(self.module.remote_runtimes.keys())):
                        if pylon_id not in targets:
                            continue
                        #
                        data = self.module.remote_runtimes[pylon_id]
                        #
                        try:
                            pylon_settings = data["pylon_settings"]["tunable"]
                            #
                            if pylon_settings:
                                zfile.writestr(f"{pylon_id}/pylon.yml", pylon_settings)
                        except:  # pylint: disable=W0702
                            pass
                        #
                        runtime_info = data["runtime_info"]
                        for plugin in sorted(runtime_info, key=lambda x: x["name"]):
                            plugin_name = plugin["name"]
                            #
                            if plugin_name not in targets[pylon_id]:
                                continue
                            #
                            config_data = plugin.get("config_data", "")
                            #
                            if not config_data:
                                continue
                            #
                            zfile.writestr(f"{pylon_id}/{plugin_name}.yml", config_data)
                #
                file_obj.seek(0)
                #
                # ---
                #
                return flask.send_file(
                    file_obj,
                    mimetype="application/zip",
                    as_attachment=True,
                    download_name=f"config_export_{int(time.time())}.zip",
                )
            #
            if action == "import_configs":
                if "file" in flask.request.files:
                    file_data = flask.request.files["file"]
                    #
                    log.info("Importing config from: %s", file_data.filename)
                    #
                    zip_data = io.BytesIO(file_data.stream.read())
                    target_events = {}
                    #
                    with zipfile.ZipFile(zip_data) as zfile:
                        for item in zfile.namelist():
                            if "/" not in item:
                                continue
                            #
                            pylon_id, name = item.split("/", 1)
                            #
                            if pylon_id not in target_events:
                                target_events[pylon_id] = {
                                    "pylon_id": pylon_id,
                                    "configs": {},
                                    "actions": [],
                                    "restart": False,
                                }
                            #
                            if not name.endswith(".yml"):
                                continue
                            #
                            base_name = name.rsplit(".", 1)[0]
                            #
                            with zfile.open(item) as ifile:
                                base_data = ifile.read().decode()
                            #
                            if base_name == "pylon":
                                target_events[pylon_id]["actions"].append(
                                    ["update_pylon_config", base_data]
                                )
                            else:
                                target_events[pylon_id]["configs"][base_name] = base_data
                    #
                    for event_data in target_events.values():
                        self.module.context.event_manager.fire_event(
                            "bootstrap_runtime_update",
                            event_data,
                        )
                #
                return {"ok": True}
            #
            return {"ok": False}
        #
        # Data: actions
        #
        data = flask.request.json
        action = data["action"]
        #
        if action in ["load", "load_raw", "save"]:
            target_pylon_id = data["pylon_id"]
            target_plugin = data["name"]
        #
        if action in ["load", "load_raw"]:
            for pylon_id in list(sorted(self.module.remote_runtimes.keys())):
                if pylon_id != target_pylon_id:
                    continue
                #
                pylon_data = self.module.remote_runtimes[pylon_id]
                runtime_info = pylon_data["runtime_info"]
                #
                for plugin in sorted(runtime_info, key=lambda x: x["name"]):
                    if plugin["name"] != target_plugin:
                        continue
                    #
                    if action == "load":
                        config_data = yaml.dump(plugin.get("config", ""))
                    else:
                        config_data = plugin.get("config_data", "")
                    #
                    return {"config": config_data}
            #
            return {"config": ""}
        #
        if action == "save":
            log.info("Requesting config update: %s -> %s", target_pylon_id, target_plugin)
            #
            self.module.context.event_manager.fire_event(
                "bootstrap_runtime_update",
                {
                    "pylon_id": target_pylon_id,
                    "configs": {
                        target_plugin: data["data"],
                    },
                    "restart": False,
                },
            )
            return {"ok": True}
        #
        if action in ["update", "update_with_reqs", "purge_reqs", "delete", "reload"]:
            targets = {}
            #
            for item in data["data"]:
                pylon_id = item.get("pylon_id", "")
                #
                if not pylon_id:
                    continue
                #
                if pylon_id not in targets:
                    targets[pylon_id] = []
                #
                plugin_state = item.get("state", False)
                plugin_name = item.get("name", "")
                #
                if not plugin_state or not plugin_name:
                    continue
                #
                if plugin_name not in targets[pylon_id]:
                    targets[pylon_id].append(plugin_name)
            #
            events = []
            #
            for pylon_id, plugins in targets.items():
                if not plugins:
                    continue
                #
                event_data = None
                #
                if action == "update":
                    log.info("Requesting plugin update(s): %s -> %s", pylon_id, plugins)
                    #
                    event_data = {
                        "pylon_id": pylon_id,
                        "plugins": plugins,
                        "restart": True,
                        "pylon_pid": 1,
                    }
                #
                if action == "update_with_reqs":
                    log.info("Requesting plugin update(s)+req(s): %s -> %s", pylon_id, plugins)
                    #
                    event_data = {
                        "pylon_id": pylon_id,
                        "plugins": plugins,
                        "actions": [
                            ["delete_requirements", plugins],
                        ],
                        "restart": True,
                        "pylon_pid": 1,
                    }
                #
                if action == "purge_reqs":
                    log.info("Requesting reqs purge(s): %s -> %s", pylon_id, plugins)
                    #
                    event_data = {
                        "pylon_id": pylon_id,
                        "actions": [
                            ["delete_requirements", plugins],
                        ],
                        "restart": True,
                        "pylon_pid": 1,
                    }
                #
                if action == "delete":
                    log.info("Requesting plugin delete(s): %s -> %s", pylon_id, plugins)
                    #
                    plugins_del = [f"!{plugin}" for plugin in plugins]
                    #
                    event_data = {
                        "pylon_id": pylon_id,
                        "plugins": plugins_del,
                        "restart": True,
                        "pylon_pid": 1,
                    }
                #
                if action == "reload":
                    log.info("Requesting plugin reload(s): %s -> %s", pylon_id, plugins)
                    #
                    event_data = {
                        "pylon_id": pylon_id,
                        "reload": plugins,
                        "restart": False,
                    }
                #
                if event_data is not None:
                    if pylon_id == self.module.context.id:
                        events.append(event_data)
                    else:
                        events.insert(0, event_data)
            #
            for event_item in events:
                self.module.context.event_manager.fire_event(
                    "bootstrap_runtime_update",
                    event_item,
                )
            #
            return {"ok": True}
        #
        return {"ok": False}
