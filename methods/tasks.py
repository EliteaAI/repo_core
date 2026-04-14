#!/usr/bin/python3
# coding=utf-8
# pylint: disable=C0411

""" Route """

import time
import functools

# pylint: disable=E0401
from tools import web, log

from ..utils.task_logs import ExistingEventNodeLogHandler


class Method:  # pylint: disable=E1101,R0903
    """ Method """

    @web.method()
    def register_task(self, name, func):
        """ Method """
        if name in self.tasks:
            raise RuntimeError(f"Task already registered: {name}")
        #
        partial_func = functools.partial(self.execute_task, func)
        #
        self.tasks[name] = partial_func
        self.task_node.register_task(partial_func, name)

    @web.method()
    def unregister_task(self, name):
        """ Method """
        if name not in self.tasks:
            raise RuntimeError(f"Task is not registered: {name}")
        #
        partial_func = self.tasks.pop(name)
        #
        self.task_node.unregister_task(partial_func, name)

    # pylint: disable=W0201,R0912
    @web.method()
    def task_list(self):
        """ Method """
        return list(self.tasks)

    @web.method()
    def execute_task(self, func, *args, **kwargs):
        """ Method """
        import tasknode_task  # pylint: disable=E0401,C0415
        #
        handler = ExistingEventNodeLogHandler({
            "event_node": self.event_node,
            "labels": {
                "tasknode_task": f"id:{tasknode_task.id}",
            }
        })
        #
        log.prepare_handler(handler)
        log.state.local.handler = handler
        #
        log.info("Starting")
        start_ts = time.time()
        #
        try:
            return func(*args, **kwargs)
        except:  # pylint: disable=W0702
            log.exception("Got exception, stopping")
            raise
        #
        finally:
            end_ts = time.time()
            log.info("Exiting (duration = %s)", end_ts - start_ts)
            #
            delattr(log.state.local, "handler")
            handler.close()
