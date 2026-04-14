#!/usr/bin/python3
# coding=utf-8
# pylint: disable=C0411

""" Route """

import time

# pylint: disable=E0401
from tools import web, context


class Method:  # pylint: disable=E1101,R0903
    """ Method """

    @web.method()
    def log_room_names(self, labels):
        """ Make names of matching rooms """
        rooms = []
        #
        if "tasknode_task" in labels:
            room = f'room:tasknode_task:{labels["tasknode_task"]}'
            rooms.append(room)
        #
        if "pylon_runtime" in labels:
            room = f'room:pylon_runtime:{labels["pylon_runtime"]}'
            rooms.append(room)
        #
        return rooms

    @web.method()
    def on_log_data(self, _, data):
        """ Process log data event """
        if "records" not in data:
            return
        #
        sio_rooms = {}
        #
        for record in data["records"]:
            rooms = self.log_room_names(record["labels"])
            #
            for room in rooms:
                self.log_room_timestamp[room] = time.time()
                #
                if room not in sio_rooms:
                    sio_rooms[room] = []
                #
                if room not in self.log_room_cache:
                    self.log_room_cache[room] = []
                #
                sio_rooms[room].append(record)
                self.log_room_cache[room].append(record)
                #
                while len(self.log_room_cache[room]) > self.log_room_cache_size:
                    self.log_room_cache[room].pop(0)
            #
        #
        for room, records in sio_rooms.items():
            context.sio.emit(
                event="log_data",
                data=records,
                room=room,
            )
