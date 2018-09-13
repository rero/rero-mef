# -*- coding: utf-8 -*-
#
# This file is part of RERO MEF.
# Copyright (C) 2018 RERO.
#
# RERO MEF is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO MEF is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO MEF; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Default configuration for RERO MEF.

You overwrite and set instance-specific configuration by either:

- Configuration file: ``<virtualenv prefix>/var/instance/invenio.cfg``
- Environment variables: ``APP_<variable name>``
"""

from __future__ import absolute_import, print_function

from datetime import timedelta

from invenio_indexer.api import RecordIndexer
from invenio_search.api import RecordsSearch


def _(x):
    """Identity function used to trigger string extraction."""
    return x


# Rate limiting
# =============
#: Storage for ratelimiter.
RATELIMIT_STORAGE_URL = 'redis://localhost:6379/3'

# I18N
# ====
#: Default language
BABEL_DEFAULT_LANGUAGE = 'en'
#: Default time zone
BABEL_DEFAULT_TIMEZONE = 'Europe/Zurich'
#: Other supported languages (do not include the default language in list).
I18N_LANGUAGES = [
    # ('fr', _('French'))
]

# Base templates
# ==============
#: Global base template.
BASE_TEMPLATE = 'invenio_theme/page.html'
#: Cover page base template (used for e.g. login/sign-up).
COVER_TEMPLATE = 'invenio_theme/page_cover.html'
#: Footer base template.
FOOTER_TEMPLATE = 'invenio_theme/footer.html'
#: Header base template.
HEADER_TEMPLATE = 'invenio_theme/header.html'
#: Settings base template.
SETTINGS_TEMPLATE = 'invenio_theme/page_settings.html'

# Theme configuration
# ===================
#: Site name
THEME_SITENAME = _('RERO MEF')
#: Use default frontpage.
THEME_FRONTPAGE = True
#: Frontpage title.
THEME_FRONTPAGE_TITLE = _('RERO MEF')
#: Frontpage template.
THEME_FRONTPAGE_TEMPLATE = 'invenio_theme/frontpage.html'

# Email configuration
# ===================
#: Email address for support.
SUPPORT_EMAIL = "software@rero.ch"
#: Disable email sending by default.
MAIL_SUPPRESS_SEND = True

# Assets
# ======
#: Static files collection method (defaults to copying files).
COLLECT_STORAGE = 'flask_collect.storage.file'

# Accounts
# ========
#: Email address used as sender of account registration emails.
SECURITY_EMAIL_SENDER = SUPPORT_EMAIL
#: Email subject for account registration emails.
SECURITY_EMAIL_SUBJECT_REGISTER = _("Welcome to RERO MEF!")
#: Redis session storage URL.
ACCOUNTS_SESSION_REDIS_URL = 'redis://localhost:6379/1'

# Celery configuration
# ====================

BROKER_URL = 'amqp://guest:guest@localhost:5672/'
#: URL of message broker for Celery (default is RabbitMQ).
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672/'
#: URL of backend for result storage (default is Redis).
CELERY_RESULT_BACKEND = 'redis://localhost:6379/2'
#: Scheduled tasks configuration (aka cronjobs).
CELERY_BEAT_SCHEDULE = {
    'indexer': {
        'task': 'invenio_indexer.tasks.process_bulk_queue',
        'schedule': timedelta(minutes=5),
    },
    'accounts': {
        'task': 'invenio_accounts.tasks.clean_session_table',
        'schedule': timedelta(minutes=60),
    },
}

# Database
# ========
#: Database URI including user and password
SQLALCHEMY_DATABASE_URI = \
    'postgresql+psycopg2://rero-mef:rero-mef@localhost/rero-mef'

# JSONSchemas
# ===========
#: Hostname used in URLs for local JSONSchemas.
JSONSCHEMAS_HOST = 'mef.test.rero.ch'
# JSONSchemas

# Flask configuration
# ===================
# See details on
# http://flask.pocoo.org/docs/0.12/config/#builtin-configuration-values

#: Secret key - each installation (dev, production, ...) needs a separate key.
#: It should be changed before deploying.
SECRET_KEY = 'CHANGE_ME'
#: Max upload size for form data via application/mulitpart-formdata.
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MiB
#: Sets cookie with the secure flag by default
SESSION_COOKIE_SECURE = True
#: Since HAProxy and Nginx route all requests no matter the host header
#: provided, the allowed hosts variable is set to localhost. In production it
#: should be set to the correct host and it is strongly recommended to only
#: route correct hosts to the application.
APP_ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# OAI-PMH
# =======
OAISERVER_ID_PREFIX = 'oai:mef.test.rero.ch:'

# Debug
# =====
# Flask-DebugToolbar is by default enabled when the application is running in
# debug mode. More configuration options are available at
# https://flask-debugtoolbar.readthedocs.io/en/latest/#configuration

#: Switches off incept of redirects by Flask-DebugToolbar.
DEBUG_TB_INTERCEPT_REDIRECTS = False

# REST API Configuration
# ======================
RECORDS_REST_ENDPOINTS = dict(
    mef=dict(
        pid_type='mef',
        pid_minter='mef',
        pid_fetcher='mef',
        search_class=RecordsSearch,
        indexer_class=RecordIndexer,
        search_index='authorities-mef-person-v0.0.1',
        search_type='mef-person-v0.0.1',
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/mef/',
        item_route='/mef/<pid(mef):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        error_handlers=dict(),
    ),
    gnd=dict(
        pid_type='gnd',
        pid_minter='gnd',
        pid_fetcher='gnd',
        search_class=RecordsSearch,
        indexer_class=RecordIndexer,
        search_index='authorities-gnd-person-v0.0.1',
        search_type='gnd-person-v0.0.1',
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/gnd/',
        item_route='/gnd/<pid(gnd):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        error_handlers=dict(),
    ),
    bnf=dict(
        pid_type='bnf',
        pid_minter='bnf',
        pid_fetcher='bnf',
        search_class=RecordsSearch,
        indexer_class=RecordIndexer,
        search_index='authorities-bnf-person-v0.0.1',
        search_type='bnf-person-v0.0.1',
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/bnf/',
        item_route='/bnf/<pid(bnf):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        error_handlers=dict(),
    ),
    rero=dict(
        pid_type='rero',
        pid_minter='rero',
        pid_fetcher='rero',
        search_class=RecordsSearch,
        indexer_class=RecordIndexer,
        search_index='authorities-rero-person-v0.0.1',
        search_type='rero-person-v0.0.1',
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/rero/',
        item_route='/rero/<pid(rero):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        error_handlers=dict(),
    ),
    viaf=dict(
        pid_type='viaf',
        pid_minter='viaf',
        pid_fetcher='viaf',
        search_class=RecordsSearch,
        indexer_class=RecordIndexer,
        search_index='authorities-viaf-person-v0.0.1',
        search_type='viaf-person-v0.0.1',
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/viaf/',
        item_route='/viaf/<pid(viaf):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        error_handlers=dict(),
    ),
)
