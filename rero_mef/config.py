# -*- coding: utf-8 -*-
#
# RERO MEF
# Copyright (C) 2020 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Default configuration for RERO MEF.

You overwrite and set instance-specific configuration by either:

- Configuration file: ``<virtualenv prefix>/var/instance/invenio.cfg``
- Environment variables: ``APP_<variable name>``
"""

from __future__ import absolute_import, print_function

from datetime import timedelta

from invenio_records_rest.facets import terms_filter

from .agents.gnd.models import AgentGndIdentifier
from .agents.idref.models import AgentIdrefIdentifier
from .agents.mef.models import MefIdentifier
from .agents.rero.models import AgentReroIdentifier
from .agents.viaf.models import ViafIdentifier
from .concepts.rero.models import ConceptReroIdentifier
from .filter import exists_filter
from .marctojson.do_gnd_agent import Transformation as AgentGndTransformation
from .marctojson.do_idref_agent import \
    Transformation as AgentIdrefTransformation
from .marctojson.do_rero_agent import Transformation as AgentReroTransformation
from .marctojson.do_rero_concepts import \
    Transformation as ConceptReroTransformation

APP_THEME = ['bootstrap3']

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
    'accounts': {
        'task': 'invenio_accounts.tasks.clean_session_table',
        'schedule': timedelta(minutes=60),
    }
    # We will harvest with a kubernetes cron job.
    # 'idref-harvester': {
    #     'task': 'rero_mef.agents.idref.tasks.process_records_from_dates',
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
    'corero': ConceptReroTransformation,
    'aggnd': AgentGndTransformation,
    'aidref': AgentIdrefTransformation,
    'agrero': AgentReroTransformation
}

IDENTIFIERS = {
    'mef': MefIdentifier,
    'viaf': ViafIdentifier,
    'corero': ConceptReroIdentifier,
    'aggnd': AgentGndIdentifier,
    'aidref': AgentIdrefIdentifier,
    'agrero': AgentReroIdentifier
}

RERO_MEF_APP_BASE_URL = 'https://mef.rero.ch'

SEARCH_CLIENT_CONFIG = dict(
    timeout=30,
    max_retries=5,
)

MAX_RESULT_WINDOW = 100000000
# REST API Configuration
# ======================
RECORDS_REST_ENDPOINTS = dict(
    mef=dict(
        pid_type='mef',
        pid_minter='mef_id',
        pid_fetcher='mef_id',
        search_class="rero_mef.agents.mef.api:AgentMefSearch",
        indexer_class="rero_mef.agents.mef.api:AgentMefIndexer",
        record_class="rero_mef.agents.mef.api:AgentMefRecord",
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
        list_route='/agents/mef/',
        item_route=('agents//mef/<pid(mef, record_class='
                    '"rero_mef.agents.mef.api:AgentMefRecord"):pid_value>'),
        default_media_type='application/json',
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers=dict(),
    ),
    viaf=dict(
        pid_type='viaf',
        pid_minter='viaf_id',
        pid_fetcher='viaf_id',
        search_class="rero_mef.agents.viaf.api:AgentViafSearch",
        indexer_class="rero_mef.agents.viaf.api:AgentViafIndexer",
        record_class="rero_mef.agents.viaf.api:AgentViafRecord",
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
        list_route='/agents/viaf/',
        item_route=('/agents/viaf/<pid(viaf, record_class='
                    '"rero_mef.agents.viaf.api:AgentViafRecord"):pid_value>'),
        default_media_type='application/json',
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers=dict(),
    ),
    aggnd=dict(
        pid_type='aggnd',
        pid_minter='agent_gnd_id',
        pid_fetcher='agent_gnd_id',
        search_class="rero_mef.agents.gnd.api:AgentGndSearch",
        indexer_class="rero_mef.agents.gnd.api:AgentGndIndexer",
        record_class="rero_mef.agents.gnd.api:AgentGndRecord",
        search_index='agents_gnd',
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
        list_route='/agents/gnd/',
        item_route=('/agents/gnd/<pid(aggnd, record_class='
                    '"rero_mef.agents.gnd.api:AgentGndRecord"):pid_value>'),
        default_media_type='application/json',
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers=dict()
    ),
    aidref=dict(
        pid_type='aidref',
        pid_minter='agent_idref_id',
        pid_fetcher='agent_idref_id',
        search_class="rero_mef.agents.idref.api:AgentIdrefSearch",
        indexer_class="rero_mef.agents.idref.api:AgentIdrefIndexer",
        record_class="rero_mef.agents.idref.api:AgentIdrefRecord",
        search_index='agents_idref',
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
        list_route='/agents/idref/',
        item_route=(
            '/agents/idref/<pid(aidref, record_class='
            '"rero_mef.agents.idref.api:AgentIdrefRecord"):pid_value>'),
        default_media_type='application/json',
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers=dict()
    ),
    agrero=dict(
        pid_type='agrero',
        pid_minter='agent_rero_id',
        pid_fetcher='agent_rero_id',
        search_class="rero_mef.agents.rero.api:AgentReroSearch",
        indexer_class="rero_mef.agents.rero.api:AgentReroIndexer",
        record_class="rero_mef.agents.rero.api:AgentReroRecord",
        search_index='agents_rero',
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
        list_route='/agents/rero/',
        item_route=('/agents/rero/<pid(agrero, record_class='
                    '"rero_mef.agents.rero.api:AgentReroRecord"):pid_value>'),
        default_media_type='application/json',
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers=dict(),
    ),
    corero=dict(
        pid_type='corero',
        pid_minter='concept_rero_id',
        pid_fetcher='concept_rero_id',
        search_class="rero_mef.concepts.rero.api:ConceptReroSearch",
        indexer_class="rero_mef.concepts.rero.api:ConceptReroIndexer",
        record_class="rero_mef.concepts.rero.api:ConceptReroRecord",
        search_index='concepts_rero',
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
        list_route='/concepts/rero/',
        item_route=(
            '/concepts/rero/<pid(corero, record_class='
            '"rero_mef.concepts.rero.api:ConceptReroRecord"):pid_value>'),
        default_media_type='application/json',
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers=dict(),
    )
)

RECORDS_JSON_SCHEMA = {
    'corero': '/concepts_rero/rero-concept-v0.0.1.json',
    'aggnd': '/agents_gnd/gnd-agent-v0.0.1.json',
    'agrero': '/agents_rero/rero-agent-v0.0.1.json',
    'aidref': '/agents_idref/idref-agent-v0.0.1.json',
    'mef': '/mef/mef-v0.0.1.json',
    'viaf': '/viaf/viaf-v0.0.1.json'
}

RECORDS_REST_FACETS = dict(
    mef=dict(
        aggs=dict(
            agent_type=dict(
                terms=dict(field='type', size=30)
            ),
            sources=dict(
                terms=dict(field='sources', size=30)
            ),
            deleted=dict(
                filter=dict(exists=dict(field="deleted"))
            ),
        ),
        filters={
            'agent_type': terms_filter('type'),
            'agent_sources': terms_filter('sources'),
            'deleted': exists_filter('deleted'),
            'rero_double': terms_filter('rero.pid')
        }
    ),
    viaf=dict(
        aggs=dict(
            gnd=dict(
                filter=dict(exists=dict(field="gnd_pid"))
            ),
            idref=dict(
                filter=dict(exists=dict(field="idref_pid"))
            ),
            rero=dict(
                filter=dict(exists=dict(field="rero_pid"))
            ),

        ),
        filters={
            'gnd': exists_filter('gnd_pid'),
            'idref': exists_filter('idref_pid'),
            'rero': exists_filter('rero_pid'),
        }
    ),
    agents_gnd=dict(
        aggs=dict(
            agent_type=dict(
                terms=dict(field='bf:Agent', size=30)
            ),
            deleted=dict(
                filter=dict(exists=dict(field="deleted"))
            )
        ),
        filters={
            'agent_type': terms_filter('bf:Agent'),
            'deleted': exists_filter('deleted'),
        },
    ),
    agents_idref=dict(
        aggs=dict(
            agent_type=dict(
                terms=dict(field='bf:Agent', size=30)
            ),
            deleted=dict(
                filter=dict(exists=dict(field="deleted"))
            )
        ),
        filters={
            'agent_type': terms_filter('bf:Agent'),
            'deleted': exists_filter('deleted'),
        }
    ),
    agents_rero=dict(
        aggs=dict(
            agent_type=dict(
                terms=dict(field='bf:Agent', size=30)
            ),
            deleted=dict(
                filter=dict(exists=dict(field="deleted"))
            )
        ),
        filters={
            'agent_type': terms_filter('bf:Agent'),
            'deleted': exists_filter('deleted'),
        }
    ),
    concepts_rero=dict(
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
            'classification': terms_filter('classification.name'),
            'classificationPortion': terms_filter(
                'classification.classificationPortion'
            )
        }
    )

)
