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

from invenio_records_rest.facets import range_filter, terms_filter

from .contributions.concepts.models import ConceptsIdentifier
from .contributions.gnd.models import GndIdentifier
from .contributions.idref.models import IdrefIdentifier
from .contributions.marctojson.do_gnd_contribution import \
    Transformation as Gnd_transformation
from .contributions.marctojson.do_idref_contribution import \
    Transformation as Idref_transformation
from .contributions.marctojson.do_rero_concepts import \
    Transformation as Concepts_transformation
from .contributions.marctojson.do_rero_contribution import \
    Transformation as Rero_transformation
from .contributions.mef.models import MefIdentifier
from .contributions.rero.models import ReroIdentifier
from .contributions.viaf.models import ViafIdentifier

# Rate limiting
# =============
#: Storage for ratelimiter.
RATELIMIT_STORAGE_URL = 'redis://localhost:6379/3'
RATELIMIT_DEFAULT = '5000/second'
RATELIMIT_ENABLED = False

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
FOOTER_TEMPLATE = 'rero_mef/footer.html'
#: Header base template.
HEADER_TEMPLATE = 'rero_mef/header.html'
#: Settings base template.
SETTINGS_TEMPLATE = 'invenio_theme/page_settings.html'

# Theme configuration
# ===================
#: Site name
THEME_SITENAME = 'RERO MEF'
#: Use default frontpage.
THEME_FRONTPAGE = False
#: Frontpage title.
THEME_FRONTPAGE_TITLE = 'RERO MEF'
#: Frontpage template.
THEME_FRONTPAGE_TEMPLATE = 'rero_mef/frontpage.html'
#: Template for error pages.
THEME_ERROR_TEMPLATE = 'rero_mef/page_error.html'

# Email configuration
# ===================
#: Email address for support.
SUPPORT_EMAIL = "software@rero.ch"
#: Disable email sending by default.
MAIL_SUPPRESS_SEND = True

# Assets
# ======
#: Static files collection method (defaults to copying files).
# COLLECT_STORAGE = 'flask_collect.storage.file'

# Accounts
# ========
#: Email address used as sender of account registration emails.
SECURITY_EMAIL_SENDER = SUPPORT_EMAIL
#: Email subject for account registration emails.
SECURITY_EMAIL_SUBJECT_REGISTER = "Welcome to RERO MEF!"
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
    # We can not run scheduled bulk indexing during initial setup.
    # 'indexer': {
    #     'task': 'rero_mef.tasks.process_bulk_queue',
    #     'schedule': timedelta(minutes=5),
    # },
    # We dont't have accounts to clean.
    # 'accounts': {
    #     'task': 'invenio_accounts.tasks.clean_session_table',
    #     'schedule': timedelta(minutes=60),
    # },
    # We will harvest with a kubernetes cron job.
    # 'idref-harvester': {
    #     'task': 'rero_mef.contributions.idref.tasks.process_records_from_dates',
    #     'schedule': timedelta(minutes=360),
    #     'kwargs': dict(name='idref'),
    # }
}
CELERY_BROKER_HEARTBEAT = 0
INDEXER_BULK_REQUEST_TIMEOUT = 60

# Database
# ========
#: Database URI including user and password
SQLALCHEMY_DATABASE_URI = \
    'postgresql+psycopg2://rero-mef:rero-mef@localhost/rero-mef'

# JSONSchemas
# ===========
#: Hostname used in URLs for local JSONSchemas.
JSONSCHEMAS_URL_SCHEME = 'https'
JSONSCHEMAS_HOST = 'mef.rero.ch'
JSONSCHEMAS_REPLACE_REFS = True
JSONSCHEMAS_LOADER_CLS = 'rero_mef.jsonschemas.utils.JsonLoader'

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
OAISERVER_ID_PREFIX = 'oai:mef.rero.ch:'
# How many times to retry the harvest request
RERO_OAI_RETRIES = 10

# Debug
# =====
# Flask-DebugToolbar is by default enabled when the application is running in
# debug mode. More configuration options are available at
# https://flask-debugtoolbar.readthedocs.io/en/latest/#configuration

#: Switches off incept of redirects by Flask-DebugToolbar.
DEBUG_TB_INTERCEPT_REDIRECTS = False

# ========
BULK_CHUNK_COUNT = 100000

TRANSFORMATION = {
    'concepts': Concepts_transformation,
    'gnd': Gnd_transformation,
    'idref': Idref_transformation,
    'rero': Rero_transformation
}

IDENTIFIERS = {
    'concepts': ConceptsIdentifier,
    'gnd': GndIdentifier,
    'idref': IdrefIdentifier,
    'mef': MefIdentifier,
    'rero': ReroIdentifier,
    'viaf': ViafIdentifier
}

RERO_MEF_APP_BASE_URL = 'https://mef.rero.ch'


MAX_RESULT_WINDOW = 100000000
# REST API Configuration
# ======================
RECORDS_REST_ENDPOINTS = dict(
    mef=dict(
        pid_type='mef',
        pid_minter='mef',
        pid_fetcher='mef',
        search_class="rero_mef.contributions.mef.api:MefSearch",
        indexer_class="rero_mef.contributions.mef.api:MefIndexer",
        record_class="rero_mef.contributions.mef.api:MefRecord",
        search_index='mef',
        search_type=None,
        record_serializers={
            'application/json': ('rero_mef.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        search_factory_imp='rero_mef.query:and_search_factory',
        list_route='/mef/',
        item_route=('/mef/<pid(mef, record_class='
                    '"rero_mef.contributions.mef.api:MefRecord"):pid_value>'),
        default_media_type='application/json',
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers=dict(),
    ),
    viaf=dict(
        pid_type='viaf',
        pid_minter='viaf',
        pid_fetcher='viaf',
        search_class="rero_mef.contributions.viaf.api:ViafSearch",
        indexer_class="rero_mef.contributions.viaf.api:ViafIndexer",
        record_class="rero_mef.contributions.viaf.api:ViafRecord",
        search_index='viaf',
        search_type=None,
        record_serializers={
            'application/json': ('rero_mef.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        search_factory_imp='rero_mef.query:and_search_factory',
        list_route='/viaf/',
        item_route=('/viaf/<pid(viaf, record_class='
                    '"rero_mef.contributions.viaf.api:ViafRecord"):pid_value>'),
        default_media_type='application/json',
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers=dict(),
    ),
    gnd=dict(
        pid_type='gnd',
        pid_minter='gnd',
        pid_fetcher='gnd',
        search_class="rero_mef.contributions.gnd.api:GndSearch",
        indexer_class="rero_mef.contributions.gnd.api:GndIndexer",
        record_class="rero_mef.contributions.gnd.api:GndRecord",
        search_index='gnd',
        search_type=None,
        record_serializers={
            'application/json': ('rero_mef.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        search_factory_imp='rero_mef.query:and_search_factory',
        list_route='/gnd/',
        item_route=('/gnd/<pid(gnd, record_class='
                    '"rero_mef.contributions.gnd.api:GndRecord"):pid_value>'),
        default_media_type='application/json',
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers=dict()
    ),
    idref=dict(
        pid_type='idref',
        pid_minter='idref',
        pid_fetcher='idref',
        search_class="rero_mef.contributions.idref.api:IdrefSearch",
        indexer_class="rero_mef.contributions.idref.api:IdrefIndexer",
        record_class="rero_mef.contributions.idref.api:IdrefRecord",
        search_index='idref',
        search_type=None,
        record_serializers={
            'application/json': ('rero_mef.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        search_factory_imp='rero_mef.query:and_search_factory',
        list_route='/idref/',
        item_route=('/idref/<pid(idref, record_class='
                    '"rero_mef.contributions.idref.api:IdrefRecord"):pid_value>'),
        default_media_type='application/json',
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers=dict()
    ),
    rero=dict(
        pid_type='rero',
        pid_minter='rero',
        pid_fetcher='rero',
        search_class="rero_mef.contributions.rero.api:ReroSearch",
        indexer_class="rero_mef.contributions.rero.api:ReroIndexer",
        record_class="rero_mef.contributions.rero.api:ReroRecord",
        search_index='rero',
        search_type=None,
        record_serializers={
            'application/json': ('rero_mef.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        search_factory_imp='rero_mef.query:and_search_factory',
        list_route='/rero/',
        item_route=('/rero/<pid(rero, record_class='
                    '"rero_mef.contributions.rero.api:ReroRecord"):pid_value>'),
        default_media_type='application/json',
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers=dict(),
    ),
    concpt=dict(
        pid_type='concpt',
        pid_minter='concepts',
        pid_fetcher='concepts',
        search_class="rero_mef.contributions.concepts.api:ConceptsSearch",
        indexer_class="rero_mef.contributions.concepts.api:ConceptsIndexer",
        record_class="rero_mef.contributions.concepts.api:ConceptsRecord",
        search_index='concepts',
        search_type=None,
        record_serializers={
            'application/json': ('rero_mef.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        search_factory_imp='rero_mef.query:and_search_factory',
        list_route='/concepts/',
        item_route=('/concepts/<pid(concepts, record_class='
                    '"rero_mef.contributions.concepts.api:ConceptsRecord"):pid_value>'),
        default_media_type='application/json',
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers=dict(),
    )
)

RECORDS_JSON_SCHEMA = {
    'concpt': '/concepts/concept-v0.0.1.json',
    'gnd': '/gnd/gnd-contribution-v0.0.1.json',
    'rero': '/rero/rero-contribution-v0.0.1.json',
    'idref': '/idref/idref-contribution-v0.0.1.json',
    'mef': '/mef/mef-contribution-v0.0.1.json',
    'viaf': '/viaf/viaf-contribution-v0.0.1.json'
}

RECORDS_REST_FACETS = dict(
    mef=dict(
        aggs=dict(
            agent_type=dict(
                terms=dict(field='type', size=30)
            ),
            sources=dict(
                terms=dict(field='sources', size=30)
            )
        ),
        filters={
            'agent_type': terms_filter('type'),
            'agent_sources': terms_filter('sources'),
            'deleted': range_filter('deleted'),
        }
    ),
    gnd=dict(
        aggs=dict(
            agent_type=dict(
                terms=dict(field='bf:Agent', size=30)
            ),
        ),
        filters={
            'agent_type': terms_filter('bf:Agent'),
            'deleted': range_filter('deleted'),
        }
    ),
    idref=dict(
        aggs=dict(
            agent_type=dict(
                terms=dict(field='bf:Agent', size=30)
            ),
        ),
        filters={
            'agent_type': terms_filter('bf:Agent'),
            'deleted': range_filter('deleted'),
        }
    ),
    rero=dict(
        aggs=dict(
            agent_type=dict(
                terms=dict(field='bf:Agent', size=30)
            ),
        ),
        filters={
            'agent_type': terms_filter('bf:Agent'),
            'deleted': range_filter('deleted'),
        }
    ),
    concepts=dict(
        aggs=dict(
            classification=dict(
                terms=dict(field='classification.name', size=30)
            ),
            classificationPortion=dict(
                terms=dict(
                    field='classification.classificationPortion', size=30
                )
            ),
        ),
        filters={
            'classification_name': terms_filter('classification.name'),
            'classificationPortion': terms_filter(
                'classification.classificationPortion'
            )
        }
    )
)
