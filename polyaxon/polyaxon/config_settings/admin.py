# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from polyaxon.utils import config

admin_name = config.get_string('POLYAXON_ADMIN_NAME')
admin_mail = config.get_string('POLYAXON_ADMIN_MAIL')


ADMINS = (
    (admin_name, admin_mail),
)

MANAGERS = ADMINS
