#!/usr/bin/python3
# coding=utf-8
# pylint: disable=C0411

""" Method """

import yaml  # pylint: disable=E0401

# pylint: disable=E0401
from tools import web


class Method:  # pylint: disable=E1101,R0903
    """ Method """

    # pylint: disable=W0201,R0912
    @web.method()
    def get_settings(self):
        """ Method """
        try:
            return yaml.load(
                self.descriptor.state["repo_core_settings"],
                Loader=yaml.SafeLoader,
            )
        except:  # pylint: disable=W0702
            return {}
