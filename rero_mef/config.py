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

from .agents import AgentViafRecord
from .agents.gnd.models import AgentGndIdentifier
from .agents.idref.models import AgentIdrefIdentifier
from .agents.rero.models import AgentReroIdentifier
from .agents.viaf.models import ViafIdentifier
from .concepts.idref.models import ConceptIdrefIdentifier
from .concepts.rero.models import ConceptReroIdentifier
from .filter import exists_filter
from .marctojson.do_gnd_agent import Transformation as AgentGndTransformation
from .marctojson.do_idref_agent import Transformation as AgentIdrefTransformation
from .marctojson.do_idref_concepts import Transformation as ConceptIdrefTransformation
from .marctojson.do_idref_places import Transformation as PlaceIdrefTransformation
from .marctojson.do_rero_agent import Transformation as AgentReroTransformation
from .marctojson.do_rero_concepts import Transformation as ConceptReroTransformation
from .models import MefIdentifier
from .places.idref.models import PlaceIdrefIdentifier

APP_THEME = ["bootstrap3"]

# RERO Services
RERO_SERVICE_ILS = "https://bib.rero.ch"
RERO_SERVICE_SONAR = "https://sonar.rero.ch"

# Rate limiting
# =============
#: Storage for ratelimiter.
RATELIMIT_STORAGE_URL = "redis://localhost:6379/3"
RATELIMIT_DEFAULT = "5000/second"
RATELIMIT_ENABLED = False

# I18N
# ====
#: Default language
BABEL_DEFAULT_LANGUAGE = "en"
#: Default time zone
BABEL_DEFAULT_TIMEZONE = "Europe/Zurich"
#: Other supported languages (do not include the default language in list).
I18N_LANGUAGES = [
    # ('fr', _('French'))
]

# Base templates
# ==============
#: Global base template.
BASE_TEMPLATE = "invenio_theme/page.html"
#: Cover page base template (used for e.g. login/sign-up).
COVER_TEMPLATE = "invenio_theme/page_cover.html"
#: Footer base template.
FOOTER_TEMPLATE = "rero_mef/footer.html"
#: Header base template.
HEADER_TEMPLATE = "rero_mef/header.html"
#: Settings base template.
SETTINGS_TEMPLATE = "invenio_theme/page_settings.html"

# Theme configuration
# ===================
#: Site name
THEME_SITENAME = "RERO MEF"
#: Use default frontpage.
THEME_FRONTPAGE = False
#: Frontpage title.
THEME_FRONTPAGE_TITLE = "RERO MEF"
#: Frontpage template.
THEME_FRONTPAGE_TEMPLATE = "rero_mef/frontpage.html"
#: Template for error pages.
THEME_ERROR_TEMPLATE = "rero_mef/page_error.html"

WEBPACKEXT_PROJECT = "rero_mef.theme.webpack:project"

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
ACCOUNTS_SESSION_REDIS_URL = "redis://localhost:6379/1"

# Celery configuration
# ====================

BROKER_URL = "amqp://guest:guest@localhost:5672/"
#: URL of message broker for Celery (default is RabbitMQ).
CELERY_BROKER_URL = "amqp://guest:guest@localhost:5672/"
#: URL of backend for result storage (default is Redis).
CELERY_RESULT_BACKEND = "redis://localhost:6379/2"
#: Scheduled tasks configuration (aka cronjobs).
CELERY_BEAT_SCHEDULE = {
    # We can not run scheduled bulk indexing during initial setup.
    # 'indexer': {
    #     'task': 'rero_mef.tasks.process_bulk_queue',
    #     'schedule': timedelta(minutes=5),
    # },
    "accounts": {
        "task": "invenio_accounts.tasks.clean_session_table",
        "schedule": timedelta(minutes=60),
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
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://rero-mef:rero-mef@localhost/rero-mef"

# JSONSchemas
# ===========
#: Hostname used in URLs for local JSONSchemas.
JSONSCHEMAS_URL_SCHEME = "https"
JSONSCHEMAS_HOST = "mef.rero.ch"
JSONSCHEMAS_REPLACE_REFS = True
JSONSCHEMAS_LOADER_CLS = "rero_mef.jsonschemas.utils.JsonLoader"

# Flask configuration
# ===================
# See details on
# http://flask.pocoo.org/docs/0.12/config/#builtin-configuration-values

#: Secret key - each installation (dev, production, ...) needs a separate key.
#: It should be changed before deploying.
SECRET_KEY = "CHANGE_ME"
#: Max upload size for form data via application/mulitpart-formdata.
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MiB
#: Sets cookie with the secure flag by default
SESSION_COOKIE_SECURE = True
#: Since HAProxy and Nginx route all requests no matter the host header
#: provided, the allowed hosts variable is set to localhost. In production it
#: should be set to the correct host and it is strongly recommended to only
#: route correct hosts to the application.
APP_ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# OAI-PMH
# =======
OAISERVER_ID_PREFIX = "oai:mef.rero.ch:"
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
    "aggnd": AgentGndTransformation,
    "aidref": AgentIdrefTransformation,
    "agrero": AgentReroTransformation,
    "corero": ConceptReroTransformation,
    "cidref": ConceptIdrefTransformation,
    "pidref": PlaceIdrefTransformation,
}

IDENTIFIERS = {
    "mef": MefIdentifier,
    "viaf": ViafIdentifier,
    "aggnd": AgentGndIdentifier,
    "aidref": AgentIdrefIdentifier,
    "agrero": AgentReroIdentifier,
    "comef": MefIdentifier,
    "corero": ConceptReroIdentifier,
    "cidref": ConceptIdrefIdentifier,
    "pidref": PlaceIdrefIdentifier,
}

RERO_MEF_APP_BASE_URL = "https://mef.rero.ch"
RERO_MEF_VIAF_BASE_URL = "http://www.viaf.org"
RERO_MEF_AGENTS_RERO_GET_RECORD = "http://data.rero.ch/02-{id}/marcxml"
RERO_MEF_AGENTS_GND_GET_RECORD = (
    "https://services.dnb.de/sru/authorities"
    "?version=1.1&operation=searchRetrieve&query=idn%3D{id}"
    "&recordSchema=MARC21-xml"
)

SEARCH_CLIENT_CONFIG = dict(
    timeout=60,
    max_retries=5,
)

MAX_RESULT_WINDOW = 100000000
# REST API Configuration
# ======================
RECORDS_REST_ENDPOINTS = dict(
    mef=dict(
        pid_type="mef",
        pid_minter="mef_id",
        pid_fetcher="mef_id",
        search_class="rero_mef.agents.mef.api:AgentMefSearch",
        indexer_class="rero_mef.agents.mef.api:AgentMefIndexer",
        record_class="rero_mef.agents.mef.api:AgentMefRecord",
        search_index="mef",
        record_serializers={
            "application/json": (
                "rero_mef.agents.mef.serializers" ":json_agent_mef_response"
            ),
        },
        search_serializers={
            "application/json": (
                "rero_mef.agents.mef.serializers" ":json_agent_mef_search"
            ),
        },
        search_factory_imp="rero_mef.query:and_search_factory",
        list_route="/agents/mef/",
        item_route=(
            "agents//mef/<pid(mef, record_class="
            '"rero_mef.agents.mef.api:AgentMefRecord"):pid_value>'
        ),
        default_media_type="application/json",
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers={},
    ),
    viaf=dict(
        pid_type="viaf",
        pid_minter="viaf_id",
        pid_fetcher="viaf_id",
        search_class="rero_mef.agents.viaf.api:AgentViafSearch",
        indexer_class="rero_mef.agents.viaf.api:AgentViafIndexer",
        record_class="rero_mef.agents.viaf.api:AgentViafRecord",
        search_index="viaf",
        record_serializers={
            "application/json": (
                "rero_mef.agents.viaf.serializers" ":json_agent_viaf_response"
            ),
        },
        search_serializers={
            "application/json": (
                "rero_mef.agents.viaf.serializers" ":json_agent_viaf_search"
            ),
        },
        search_factory_imp="rero_mef.query:and_search_factory",
        list_route="/agents/viaf/",
        item_route=(
            "/agents/viaf/<pid(viaf, record_class="
            '"rero_mef.agents.viaf.api:AgentViafRecord"):pid_value>'
        ),
        default_media_type="application/json",
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers={},
    ),
    aggnd=dict(
        pid_type="aggnd",
        pid_minter="agent_gnd_id",
        pid_fetcher="agent_gnd_id",
        search_class="rero_mef.agents.gnd.api:AgentGndSearch",
        indexer_class="rero_mef.agents.gnd.api:AgentGndIndexer",
        record_class="rero_mef.agents.gnd.api:AgentGndRecord",
        search_index="agents_gnd",
        record_serializers={
            "application/json": ("rero_mef.agents.serializers" ":json_agent_response"),
        },
        search_serializers={
            "application/json": ("rero_mef.agents.serializers" ":json_agent_search"),
        },
        search_factory_imp="rero_mef.query:and_search_factory",
        list_route="/agents/gnd/",
        item_route=(
            "/agents/gnd/<pid(aggnd, record_class="
            '"rero_mef.agents.gnd.api:AgentGndRecord"):pid_value>'
        ),
        default_media_type="application/json",
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers={},
    ),
    aidref=dict(
        pid_type="aidref",
        pid_minter="agent_idref_id",
        pid_fetcher="agent_idref_id",
        search_class="rero_mef.agents.idref.api:AgentIdrefSearch",
        indexer_class="rero_mef.agents.idref.api:AgentIdrefIndexer",
        record_class="rero_mef.agents.idref.api:AgentIdrefRecord",
        search_index="agents_idref",
        record_serializers={
            "application/json": ("rero_mef.agents.serializers" ":json_agent_response"),
        },
        search_serializers={
            "application/json": ("rero_mef.agents.serializers" ":json_agent_search"),
        },
        search_factory_imp="rero_mef.query:and_search_factory",
        list_route="/agents/idref/",
        item_route=(
            "/agents/idref/<pid(aidref, record_class="
            '"rero_mef.agents.idref.api:AgentIdrefRecord"):pid_value>'
        ),
        default_media_type="application/json",
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers={},
    ),
    agrero=dict(
        pid_type="agrero",
        pid_minter="agent_rero_id",
        pid_fetcher="agent_rero_id",
        search_class="rero_mef.agents.rero.api:AgentReroSearch",
        indexer_class="rero_mef.agents.rero.api:AgentReroIndexer",
        record_class="rero_mef.agents.rero.api:AgentReroRecord",
        search_index="agents_rero",
        record_serializers={
            "application/json": ("rero_mef.agents.serializers" ":json_agent_response"),
        },
        search_serializers={
            "application/json": ("rero_mef.agents.serializers" ":json_agent_search"),
        },
        search_factory_imp="rero_mef.query:and_search_factory",
        list_route="/agents/rero/",
        item_route=(
            "/agents/rero/<pid(agrero, record_class="
            '"rero_mef.agents.rero.api:AgentReroRecord"):pid_value>'
        ),
        default_media_type="application/json",
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers={},
    ),
    comef=dict(
        pid_type="comef",
        pid_minter="concept_mef_id",
        pid_fetcher="concept_mef_id",
        search_class="rero_mef.concepts.mef.api:ConceptMefSearch",
        indexer_class="rero_mef.concepts.mef.api:ConceptMefIndexer",
        record_class="rero_mef.concepts.mef.api:ConceptMefRecord",
        search_index="concepts_mef",
        record_serializers={
            "application/json": (
                "rero_mef.concepts.mef.serializers" ":json_concept_mef_response"
            ),
        },
        search_serializers={
            "application/json": (
                "rero_mef.concepts.mef.serializers" ":json_concept_mef_search"
            ),
        },
        search_factory_imp="rero_mef.query:and_search_factory",
        list_route="/concepts/mef/",
        item_route=(
            "/concepts/mef/<pid(comef, record_class="
            '"rero_mef.concepts.mef.api:ConceptMefRecord")'
            ":pid_value>"
        ),
        default_media_type="application/json",
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers={},
    ),
    corero=dict(
        pid_type="corero",
        pid_minter="concept_rero_id",
        pid_fetcher="concept_rero_id",
        search_class="rero_mef.concepts.rero.api:ConceptReroSearch",
        indexer_class="rero_mef.concepts.rero.api:ConceptReroIndexer",
        record_class="rero_mef.concepts.rero.api:ConceptReroRecord",
        search_index="concepts_rero",
        record_serializers={
            "application/json": (
                "rero_mef.concepts.serializers" ":json_concept_response"
            ),
        },
        search_serializers={
            "application/json": (
                "rero_mef.concepts.serializers" ":json_concept_search"
            ),
        },
        search_factory_imp="rero_mef.query:and_search_factory",
        list_route="/concepts/rero/",
        item_route=(
            "/concepts/rero/<pid(corero, record_class="
            '"rero_mef.concepts.rero.api:ConceptReroRecord"):pid_value>'
        ),
        default_media_type="application/json",
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers={},
    ),
    cidref=dict(
        pid_type="cidref",
        pid_minter="concept_idref_id",
        pid_fetcher="concept_idref_id",
        search_class="rero_mef.concepts.idref.api:ConceptIdrefSearch",
        indexer_class="rero_mef.concepts.idref.api:ConceptIdrefIndexer",
        record_class="rero_mef.concepts.idref.api:ConceptIdrefRecord",
        search_index="concepts_idref",
        record_serializers={
            "application/json": (
                "rero_mef.concepts.serializers" ":json_concept_response"
            ),
        },
        search_serializers={
            "application/json": (
                "rero_mef.concepts.serializers" ":json_concept_search"
            ),
        },
        search_factory_imp="rero_mef.query:and_search_factory",
        list_route="/concepts/idref/",
        item_route=(
            "/concepts/idref/<pid(cidref, record_class="
            '"rero_mef.concepts.idref.api:ConceptIdrefRecord"):pid_value>'
        ),
        default_media_type="application/json",
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers={},
    ),
    plmef=dict(
        pid_type="plmef",
        pid_minter="place_mef_id",
        pid_fetcher="place_mef_id",
        search_class="rero_mef.places.mef.api:PlaceMefSearch",
        indexer_class="rero_mef.places.mef.api:PlaceMefIndexer",
        record_class="rero_mef.places.mef.api:PlaceMefRecord",
        search_index="places_mef",
        record_serializers={
            "application/json": (
                "rero_mef.places.mef.serializers" ":json_place_mef_response"
            ),
        },
        search_serializers={
            "application/json": (
                "rero_mef.places.mef.serializers" ":json_place_mef_search"
            ),
        },
        search_factory_imp="rero_mef.query:and_search_factory",
        list_route="/places/mef/",
        item_route=(
            "/places/mef/<pid(plmef, record_class="
            '"rero_mef.places.mef.api:PlaceMefRecord")'
            ":pid_value>"
        ),
        default_media_type="application/json",
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers={},
    ),
    pidref=dict(
        pid_type="pidref",
        pid_minter="place_idref_id",
        pid_fetcher="place_idref_id",
        search_class="rero_mef.places.idref.api:PlaceIdrefSearch",
        indexer_class="rero_mef.places.idref.api:PlaceIdrefIndexer",
        record_class="rero_mef.places.idref.api:PlaceIdrefRecord",
        search_index="places_idref",
        record_serializers={
            "application/json": ("rero_mef.places.serializers" ":json_place_response"),
        },
        search_serializers={
            "application/json": ("rero_mef.places.serializers" ":json_place_search"),
        },
        search_factory_imp="rero_mef.query:and_search_factory",
        list_route="/places/idref/",
        item_route=(
            "/places/idref/<pid(pidref, record_class="
            '"rero_mef.places.idref.api:PlaceIdrefRecord"):pid_value>'
        ),
        default_media_type="application/json",
        max_result_window=MAX_RESULT_WINDOW,
        error_handlers={},
    ),
)

RERO_AGENTS = ["aidref", "aggnd", "agrero"]

RERO_CONCEPTS = ["cidref", "corero"]

RERO_PLACES = ["pidref"]

RERO_ENTITIES = RERO_AGENTS + RERO_CONCEPTS + RERO_PLACES

RECORDS_JSON_SCHEMA = {
    "plmef": "/places_mef/mef-place-v0.0.1.json",
    "pidref": "/places_idref/idref-place-v0.0.1.json",
    "corero": "/concepts_rero/rero-concept-v0.0.1.json",
    "cidref": "/concepts_idref/idref-concept-v0.0.1.json",
    "comef": "/concepts_mef/mef-concept-v0.0.1.json",
    "aggnd": "/agents_gnd/gnd-agent-v0.0.1.json",
    "agrero": "/agents_rero/rero-agent-v0.0.1.json",
    "aidref": "/agents_idref/idref-agent-v0.0.1.json",
    "mef": "/mef/mef-v0.0.1.json",
    "viaf": "/viaf/viaf-v0.0.1.json",
}

RECORDS_REST_FACETS = dict(
    mef=dict(
        aggs=dict(
            type=dict(terms=dict(field="type", size=30)),
            source=dict(terms=dict(field="sources", size=30)),
            deleted=dict(filter=dict(exists=dict(field="deleted"))),
            deleted_entities=dict(filter=dict(exists=dict(field="*.deleted"))),
            identifiedBy_source=dict(
                terms=dict(field="*.identifiedBy.source", size=30)
            ),
        ),
        filters=dict(
            type=terms_filter("type"),
            source=terms_filter("sources"),
            deleted=exists_filter("deleted"),
            deleted_entities=exists_filter("*.deleted"),
            rero_double=terms_filter("rero.pid"),
            identifiedBy_source=terms_filter("*.identifiedBy.source"),
        ),
    ),
    viaf=dict(aggs=AgentViafRecord.aggregations(), filters=AgentViafRecord.filters()),
    agents_gnd=dict(
        aggs=dict(
            type=dict(terms=dict(field="type", size=30)),
            deleted=dict(filter=dict(exists=dict(field="deleted"))),
            identifiedBy_source=dict(terms=dict(field="identifiedBy.source", size=30)),
        ),
        filters=dict(
            type=terms_filter("type"),
            deleted=exists_filter("deleted"),
            identifiedBy_source=terms_filter("identifiedBy.source"),
        ),
    ),
    agents_idref=dict(
        aggs=dict(
            type=dict(terms=dict(field="type", size=30)),
            deleted=dict(filter=dict(exists=dict(field="deleted"))),
            identifiedBy_source=dict(terms=dict(field="identifiedBy.source", size=30)),
        ),
        filters=dict(
            type=terms_filter("type"),
            deleted=exists_filter("deleted"),
            identifiedBy_source=terms_filter("identifiedBy.source"),
        ),
    ),
    agents_rero=dict(
        aggs=dict(
            type=dict(terms=dict(field="type", size=30)),
            deleted=dict(filter=dict(exists=dict(field="deleted"))),
            identifiedBy_source=dict(terms=dict(field="identifiedBy.source", size=30)),
        ),
        filters=dict(
            type=terms_filter("type"),
            deleted=exists_filter("deleted"),
            identifiedBy_source=terms_filter("identifiedBy.source"),
        ),
    ),
    concepts_mef=dict(
        aggs=dict(
            type=dict(terms=dict(field="type", size=30)),
            source=dict(terms=dict(field="sources", size=30)),
            deleted=dict(filter=dict(exists=dict(field="deleted"))),
            deleted_entities=dict(filter=dict(exists=dict(field="*.deleted"))),
            identifiedBy_source=dict(
                terms=dict(field="*.identifiedBy.source", size=30)
            ),
        ),
        filters=dict(
            type=terms_filter("type"),
            source=terms_filter("sources"),
            deleted=exists_filter("deleted"),
            deleted_entities=exists_filter("*.deleted"),
            rero_double=terms_filter("rero.pid"),
            identifiedBy_source=terms_filter("*.identifiedBy.source"),
        ),
    ),
    concepts_rero=dict(
        aggs=dict(
            type=dict(terms=dict(field="type", size=30)),
            classification=dict(terms=dict(field="classification.name", size=30)),
            classificationPortion=dict(
                terms=dict(field="classification.classificationPortion", size=30)
            ),
            deleted=dict(filter=dict(exists=dict(field="deleted"))),
            identifiedBy_source=dict(terms=dict(field="identifiedBy.source", size=30)),
        ),
        filters=dict(
            type=terms_filter("type"),
            classification=terms_filter("classification.name"),
            classificationPortion=terms_filter("classification.classificationPortion"),
            deleted=exists_filter("deleted"),
            identifiedBy_source=terms_filter("identifiedBy.source"),
        ),
    ),
    concepts_idref=dict(
        aggs=dict(
            type=dict(terms=dict(field="type", size=30)),
            classification=dict(terms=dict(field="classification.name", size=30)),
            classificationPortion=dict(
                terms=dict(field="classification.classificationPortion", size=30)
            ),
            deleted=dict(filter=dict(exists=dict(field="deleted"))),
            identifiedBy_source=dict(terms=dict(field="identifiedBy.source", size=30)),
        ),
        filters=dict(
            type=terms_filter("type"),
            classification=terms_filter("classification.name"),
            classificationPortion=terms_filter("classification.classificationPortion"),
            deleted=exists_filter("deleted"),
            identifiedBy_source=terms_filter("identifiedBy.source"),
        ),
    ),
    places_mef=dict(
        aggs=dict(
            type=dict(terms=dict(field="type", size=30)),
            source=dict(terms=dict(field="sources", size=30)),
            deleted=dict(filter=dict(exists=dict(field="deleted"))),
            deleted_entities=dict(filter=dict(exists=dict(field="*.deleted"))),
            identifiedBy_source=dict(
                terms=dict(field="*.identifiedBy.source", size=30)
            ),
        ),
        filters=dict(
            type=terms_filter("type"),
            source=terms_filter("sources"),
            deleted=exists_filter("deleted"),
            deleted_entities=exists_filter("*.deleted"),
            identifiedBy_source=terms_filter("*.identifiedBy.source"),
        ),
    ),
    places_idref=dict(
        aggs=dict(
            type=dict(terms=dict(field="type", size=30)),
            classification=dict(terms=dict(field="classification.name", size=30)),
            classificationPortion=dict(
                terms=dict(field="classification.classificationPortion", size=30)
            ),
            deleted=dict(filter=dict(exists=dict(field="deleted"))),
            identifiedBy_source=dict(terms=dict(field="identifiedBy.source", size=30)),
        ),
        filters=dict(
            type=terms_filter("type"),
            classification=terms_filter("classification.name"),
            classificationPortion=terms_filter("classification.classificationPortion"),
            deleted=exists_filter("deleted"),
            identifiedBy_source=terms_filter("identifiedBy.source"),
        ),
    ),
)
