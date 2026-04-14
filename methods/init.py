#!/usr/bin/python3
# coding=utf-8
# pylint: disable=C0411

""" Method """

import logging

import arbiter  # pylint: disable=E0401

# pylint: disable=E0401
from tools import web, router, context, auth, this, log

from ..utils.task_logs import LogRoomHousekeeper, ExistingEventNodeLogHandler


class Method:  # pylint: disable=E1101,R0902,R0903
    """ Method """

    # pylint: disable=W0201,R0912
    @web.init()
    def init(self):
        """ Init """
        #
        # Core
        #
        auth.add_public_rule({"uri": f"{context.url_prefix}/"})
        #
        self.descriptor.register_tool("repo_core", self)
        #
        router.default_template = f"{this.module_name}:index.html"
        router.default_template_kwargs = {
            "app_title": self.descriptor.config.get("app_title", "Repo"),
        }
        #
        router.target_auth_processor = self.target_auth_processor
        router.access_denied_handler = self.access_denied_handler
        #
        router.register_mode()
        #
        router.register_section(
            key="core",
        )
        router.register_subsection(
            section="core",
            key="users",
            kind="template",
            template_kwargs={
                "head_template": f"{this.module_name}:users/styles.html",
                "content_template": f"{this.module_name}:users/content.html",
                "script_template": f"{this.module_name}:users/scripts.html",
            },
        )
        router.register_subsection(
            section="core",
            key="settings",
            kind="template",
            template_kwargs={
                "head_template": f"{this.module_name}:settings/styles.html",
                "content_template": f"{this.module_name}:settings/content.html",
                "script_template": f"{this.module_name}:settings/scripts.html",
            },
        )
        #
        router.register_section(
            key="user",
            location="right",
        )
        router.register_subsection(
            section="user",
            key="logout",
            kind="redirect",
            url=self.descriptor.config.get("logout_url", f"{context.url_prefix}/auth/logout"),
        )
        #
        # Runtime
        #
        self.remote_runtimes = {}
        #
        router.register_section(
            key="runtime",
        )
        router.register_subsection(
            section="runtime",
            key="pylons",
            kind="template",
            template_kwargs={
                "head_template": f"{this.module_name}:pylons/styles.html",
                "content_template": f"{this.module_name}:pylons/content.html",
                "script_template": f"{this.module_name}:pylons/scripts.html",
            },
        )
        router.register_subsection(
            section="runtime",
            key="remote",
            kind="template",
            template_kwargs={
                "head_template": f"{this.module_name}:remote/styles.html",
                "content_template": f"{this.module_name}:remote/content.html",
                "script_template": f"{this.module_name}:remote/scripts.html",
            },
        )
        #
        # Tasks
        #
        self.tasks = {}  # name -> func
        #
        self.event_node = arbiter.make_event_node(
            config={
                "type": "MockEventNode",
            },
        )
        #
        self.event_node.start()
        #
        self.task_node = arbiter.TaskNode(
            self.event_node,
            pool="repo",
            task_limit=None,
            ident_prefix="repo_",
            multiprocessing_context="threading",
            task_retention_period=86400,
            housekeeping_interval=60,
            thread_scan_interval=0.1,
            start_max_wait=3,
            query_wait=3,
            watcher_max_wait=3,
            stop_node_task_wait=3,
            result_max_wait=3,
            result_transport="memory",
            start_attempts=1,
        )
        #
        self.task_node.start()
        #
        # Logs
        #
        settings = self.get_settings()
        #
        self.log_room_cache_size = settings.get("log_room_cache_size", 1000)
        #
        self.log_room_cache = {}
        self.log_room_timestamp = {}
        #
        self.event_node.subscribe("log_data", self.on_log_data)
        #
        self.log_room_housekeeper = LogRoomHousekeeper(self)
        self.log_room_housekeeper.start()
        #
        self.log_pylon_handler = ExistingEventNodeLogHandler({
            "event_node": self.event_node,
            "labels": {
                "pylon_runtime": f"id:{context.id}",
                # pylon_runtime_group
            }
        })
        #
        log.prepare_handler(self.log_pylon_handler)
        log.state.handlers.append(self.log_pylon_handler)
        logging.root.addHandler(self.log_pylon_handler)
        #
        # Release
        #
        router.register_section(
            key="release",
        )
        router.register_subsection(
            section="release",
            key="tasks",
            kind="template",
            template_kwargs={
                "head_template": f"{this.module_name}:tasks/styles.html",
                "content_template": f"{this.module_name}:tasks/content.html",
                "script_template": f"{this.module_name}:tasks/scripts.html",
                "task_list": self.task_list,
            },
        )

    # pylint: disable=W0201,R0912
    @web.deinit()
    def deinit(self):
        """ De-init """
        #
        # Logs
        #
        logging.root.removeHandler(self.log_pylon_handler)
        self.log_pylon_handler.close()
        #
        self.log_room_housekeeper.stop()
        #
        self.event_node.unsubscribe("log_data", self.on_log_data)
        #
        # Tasks
        #
        for task_name, _ in list(self.tasks.items()):
            self.unregister_task(task_name)
        #
        self.task_node.stop()
        self.event_node.stop()
