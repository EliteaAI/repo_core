#!/usr/bin/python3
# coding=utf-8
# pylint: disable=C0411

""" Method """

import json

import flask  # pylint: disable=E0401

# pylint: disable=E0401
from tools import web, router, auth, this


class Method:  # pylint: disable=E1101,R0903
    """ Method """

    # pylint: disable=W0201,R0912
    @web.method()
    def user_has_release(self, release):
        """ Method """
        releases = self.user_releases()
        return release in releases or self.user_has_role(role="admin")

    # pylint: disable=W0201,R0912
    @web.method()
    def user_releases(self):
        """ Method """
        user = auth.current_user()
        name = user["name"]
        #
        try:
            meta = json.loads(name)
        except:  # pylint: disable=W0702
            meta = {}
        #
        return meta.get("releases", [])

    # pylint: disable=W0201,R0912
    @web.method()
    def user_has_role(self, role):
        """ Method """
        roles = self.user_roles()
        return role in roles

    # pylint: disable=W0201,R0912
    @web.method()
    def user_roles(self):
        """ Method """
        user = auth.current_user()
        roles = []
        #
        if user["id"] is not None:
            roles = auth.get_user_roles(user["id"])
        #
        return roles

    # pylint: disable=W0201,R0912
    @web.method()
    def target_auth_processor(self, target, router_state):
        """ Method """
        _ = target, router_state
        return self.user_has_role(role="admin")

    # pylint: disable=W0201,R0912
    @web.method()
    def access_denied_handler(self):
        """ Method """
        template_kwargs = router.default_template_kwargs.copy()
        return flask.render_template(f"{this.module_name}:blank.html", **template_kwargs)
