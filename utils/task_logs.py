#!/usr/bin/python3
# coding=utf-8
# pylint: disable=C0411

""" Utils """

import time
import logging
import traceback
import threading

from centry_logging.emitters.eventnode import EventNodeLogEmitter  # pylint: disable=E0401

# pylint: disable=E0401
from tools import log, this


class LogRoomHousekeeper(threading.Thread):  # pylint: disable=R0903
    """ Perform cleanup """

    def __init__(self, module):
        super().__init__(daemon=True)
        #
        self.module = module
        self.stop_event = threading.Event()
        #
        settings = this.module.get_settings()
        #
        self.room_ttl = settings.get("log_room_ttl", 86400)
        #
        self.housekeeping_interval = settings.get(
            "log_room_housekeeping_interval", 3600,
        )
        self.housekeeping_ts = time.time()

    def stop(self):
        """ Request to stop """
        self.stop_event.set()

    def run(self):
        """ Run housekeeper thread """
        while not self.stop_event.is_set():
            time.sleep(1.0)
            current_ts = time.time()
            #
            if current_ts - self.housekeeping_ts >= self.housekeeping_interval:
                self.housekeeping_ts = current_ts
                #
                try:
                    self._clean_rooms()
                except:  # pylint: disable=W0702
                    pass

    def _clean_rooms(self):
        now = time.time()
        for room_name, room_timestamp in list(self.module.log_room_timestamp.items()):
            if abs(now - room_timestamp) >= self.room_ttl:
                log.info("Room TTL expired: %s", room_name)
                #
                self.module.log_room_cache.pop(room_name, None)
                self.module.log_room_timestamp.pop(room_name, None)


class ExistingEventNodeLogHandler(logging.Handler):
    """ Log handler - send logs to EventNode """

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        #
        self.emitter = EventNodeLogEmitter(
            event_node=settings.get("event_node"),
            default_labels=self.settings.get("labels", {}),
        )

    def emit(self, record):
        try:
            log_line = self.format(record)
            log_time = record.created
            #
            additional_labels = {}
            if self.settings.get("include_level_name", True):
                additional_labels["level"] = record.levelname
            if self.settings.get("include_logger_name", True):
                additional_labels["logger"] = record.name
            #
            self.emitter.emit(log_line, log_time, additional_labels)
        except:  # pylint: disable=W0702
            # In this case we should NOT use logging to log logging error. Only print()
            print("[FATAL] Exception during sending logs")
            traceback.print_exc()
