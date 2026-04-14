#!/usr/bin/python3
# coding=utf-8
# pylint: disable=C0411

""" SIO """

from tools import web  # pylint: disable=E0401


class SIO:  # pylint: disable=E1101,R0903
    """ SIO """

    @web.sio("task_logs_subscribe")
    def task_logs_subscribe(self, sid, data):
        """ Event handler """
        rooms = self.log_room_names(data)
        #
        for room in rooms:
            self.context.sio.enter_room(sid, room)
            #
            if room in self.log_room_cache:
                self.context.sio.emit(
                    event="log_data",
                    data=self.log_room_cache[room],
                    room=sid,
                )

    @web.sio("task_logs_unsubscribe")
    def task_logs_unsubscribe(self, sid, data):
        """ Event handler """
        rooms = self.log_room_names(data)
        #
        for room in rooms:
            self.context.sio.leave_room(sid, room)
