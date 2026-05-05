# RERO MEF
# Copyright (C) 2026 RERO
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

"""API for manipulating VIAF record."""

import random
import signal
import threading
import time
from copy import deepcopy
from urllib.parse import quote

import click
import requests
from elasticsearch_dsl.query import Q
from flask import current_app
from invenio_search.api import RecordsSearch

from rero_mef.extensions import MD5Extension
from rero_mef.filter import exists_filter
from rero_mef.utils import (
    get_entity_class,
    progressbar,
    requests_retry_session,
)
from rero_mef.version import __version__

from .. import AgentGndRecord, AgentIdrefRecord, AgentMefRecord, AgentReroRecord
from ..api import Action, EntityIndexer, EntityRecord
from .fetchers import viaf_id_fetcher
from .minters import viaf_id_minter
from .models import ViafMetadata
from .providers import ViafProvider

_md5 = MD5Extension()


def _sleep_with_countdown(wait_seconds):
    """Sleep while showing a short progress countdown.

    :param wait_seconds: Number of seconds to wait.
    """
    if wait_seconds <= 0:
        return
    hms = f"{wait_seconds // 3600:02d}:{(wait_seconds % 3600) // 60:02d}:{wait_seconds % 60:02d}"
    with click.progressbar(
        range(wait_seconds),
        label=f"Retry-After={hms}",
        length=wait_seconds,
    ) as progress_items:
        for _ in progress_items:
            time.sleep(1)


def _get_redirect_pid_from_msg(msg):
    """Extract redirect target PID from a VIAF fetch message.

    :param msg: VIAF fetch status message.
    :returns: Redirect target PID or ``None``.
    """
    marker = "| REDIRECT -> "
    if not msg or marker not in msg:
        return None
    redirect_to_pid = msg.split(marker, maxsplit=1)[1].strip()
    return redirect_to_pid or None


class RetryableVIAFError(RuntimeError):
    """Transient VIAF fetch failure that callers should not treat as not-found."""


class AgentViafSearch(RecordsSearch):
    """RecordsSearch."""

    class Meta:
        """Search only on index."""

        index = "viaf"
        doc_types = None
        fields = ("*",)
        facets = {}

        default_filter = None


class AgentViafRecord(EntityRecord):
    """VIAF agent class."""

    minter = viaf_id_minter
    fetcher = viaf_id_fetcher
    provider = ViafProvider
    name = "viaf"
    model_cls = ViafMetadata
    search = AgentViafSearch
    # https://viaf.org/
    sources = {
        "SUDOC": {
            "name": "idref",
            "info": "Sudoc [ABES], France",
            "record_class": AgentIdrefRecord,
        },
        "DNB": {
            "name": "gnd",
            "info": "German National Library",
            "record_class": AgentGndRecord,
        },
        "RERO": {
            "name": "rero",
            "info": "RERO - Library Network of Western Switzerland",
            "record_class": AgentReroRecord,
        },
        "SZ": {"name": "sz", "info": "Swiss National Library"},
        "BNE": {"name": "bne", "info": "National Library of Spain"},
        "BNF": {"name": "bnf", "info": "National Library of France"},
        "ICCU": {
            "name": "iccu",
            "info": "Central Institute for the Union Catalogue of the "
            "Italian libraries",
        },
        "ISNI": {"name": "isni", "info": "ISNI"},
        "WKP": {"name": "wiki", "info": "Wikidata"},
        # 'LC': 'loc',  # Library of Congress
        # 'SELIBR': 'selibr',  # National Library of Sweden
        # 'NLA': 'nla',  # National Library of Australia
        # 'PTBNP': 'ptbnp',  # National Library of Portugal
        # 'BLBNB': 'BLBNB',  # National Library of Brazil
        # 'NKC': 'nkc',  # National Library of the Czech Republic
        # 'J9U': 'j9u',  # National Library of Israel
        # 'EGAXA': 'egaxa',  # Library of Alexandria, Egypt
        # 'BAV': 'bav',  # Vatican Library
        # 'CAOONL': 'caoonl',  # Library and Archives Canada/PFAN
        # 'JPG': 'jpg',  # Union List of Artist Names [Getty Research Institute]
        # 'NUKAT': 'nukat',  # NUKAT Center of Warsaw University Library
        # 'NSZL': 'NSZL',  # National Széchényi Library, Hungary
        # 'VLACC': 'vlacc',  # Flemish Public Libraries National Library of Russia
        # 'NTA': 'nta',  # National Library of Netherlands
        # 'BIBSYS': 'bibsys',  # BIBSYS
        # 'GRATEVE': 'grateve',  # National Library of Greece
        # 'ARBABN': 'arbabn',  # National Library of Argentina
        # 'W2Z': 'w2z',  # National Library of Norway
        # 'DBC': 'dbc',  # DBC (Danish Bibliographic Center)
        # 'NDL': 'ndl',  # National Diet Library, Japan
        # 'NII': 'nii',  # NII (Japan)
        # 'NLB': 'nlb',  # National Library Board, Singapore
        # 'LNB': 'lnb',  # National Library of Latvia
        # 'PLWABN': 'plwabn',  # National Library of Poland
        # 'BNC': 'BNC',  # National Library of Catalonia
        # 'LNL': 'lnl',  # Lebanese National Library
        # 'PERSEUS': 'perseus',  # Perseus Digital Library
        # 'SRP': 'srp',  # Syriac Reference Portal
        # 'N6I': 'n6i',  # National Library of Ireland
        # 'NSK': 'nsk',  # National and University Library in Zagreb
        # 'CYT': 'cyt',  # National Central Library, Taiwan
        # 'B2Q': 'b2q',  # National Library and Archives of Québec
        # 'KRLNK': 'krlnk',  # National Library of Korea
        # 'BNL': 'BNL',  # National Library of Luxembourg
        # 'BNCHL': 'bnchl',  # National Library of Chile
        # 'MRBNR': 'mrbnr',  # National Library of Morocco
        # 'XA': 'xa',  # xA Extended Authorities
        # 'XR': 'xr',  # xR Extended Relationships
        # 'FAST': 'fast',  # FAST Subjects
        # 'ERRR': 'errr',  # National Library of Estonia
        # 'UIY': 'uiy',  # National and University Library of Iceland (NULI)
        # 'NYNYRILM': 'nynyrilm',  # Repertoire International de Litterature Musicale, Inc. (RILM)
        # 'DE663': 'de663',  # International Inventory of Musical Sources (RISM)
        # 'SIMACOB': 'simacob',  # NUK/COBISS.SI, Slovenia
        # 'LIH': 'lih',  # National Library of Lithuania
        # 'SKMASNL': 'skmasnl',  # Slovak National Library
        # 'UAE': 'uae',  # United Arab Emirates University
    }

    def __init__(self, data, model=None, **kwargs):
        """Initialize instance with dictionary data and SQLAlchemy model.

        :param data: Dict with record metadata.
        :param model: :class:`~invenio_records.models.RecordMetadata` instance.
        """
        super().__init__(data or {}, model=model, **kwargs)
        self.sources_used = {}
        for data in self.sources.values():
            if record_class := data.get("record_class"):
                self.sources_used[data["name"]] = record_class

    @classmethod
    def filters(cls):
        """Filters for sources."""
        return {
            source["name"]: exists_filter(f"{source['name']}_pid")
            for source in cls.sources.values()
        }

    @classmethod
    def aggregations(cls):
        """Aggregations for sources."""
        return {
            source["name"]: {"filter": {"exists": {"field": f"{source['name']}_pid"}}}
            for source in cls.sources.values()
        }

    def create_mef_and_agents(
        self,
        dbcommit=False,
        reindex=False,
        online=None,
        verbose=False,
        online_verbose=False,
        update_viaf=False,
    ):
        """Create MEF and agents records.

        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :param online: Search online for new VIAF record.
        :param verbose: Verbose.
        :param online_verbose: Online verbose.
        :param update_viaf: When True, search VIAF online for each agent
            displaced from this cluster and create/update the new cluster.
        :returns: Actions.
        """

        def update_online(agent_class, pid, online):
            """Update agents online.

            :param agent_class: Agent class to use.
            :param pid: Agent pid to use.
            :param online: Try to get following agent types online.
            :return: Agent record and performed action.
            """
            action = Action.NOT_ONLINE
            agent_record = None
            if agent_class.provider.pid_type in online:
                data, msg = agent_class.get_online_record(id_=pid)
                if online_verbose:
                    click.echo(f"\n{msg}")
                if data and not data.get("NO TRANSFORMATION"):
                    agent_record, action = agent_class.create_or_update(
                        data=data, dbcommit=dbcommit, reindex=reindex
                    )
            else:
                agent_record = agent_class.get_record_by_pid(pid)
            return agent_record, action

        def set_actions(actions, pid, source_name, action, mef_actions=None):
            """Set actions.

            :param actions: Actions dictionary to change
            :param pid: Pid to add.
            :param source_name: Source name to add
            :param action: Action to add.
            :param mef_actions: MEF actions to add (optional).
            :return: actions
            """
            actions.setdefault(pid, {"source": source_name, "action": action})
            if mef_actions:
                actions[pid]["MEF"] = mef_actions
            return actions

        actions = {}
        online = online or []
        viaf_agents_data = self.get_entities_pids()
        viaf_agents_pids = [data["pid"] for data in viaf_agents_data]
        # Delete old agent entries from MEF records
        old_agents = {}
        for mef_record in AgentMefRecord.get_mef(self.pid, self.name):
            changed = False
            for agent in mef_record.get_entities_records():
                if agent.pid not in viaf_agents_pids:
                    mef_record.pop(agent.name)
                    old_agents[agent.pid] = agent
                    actions = set_actions(
                        actions=actions,
                        pid=agent.pid,
                        source_name=agent.name,
                        action=Action.DISCARD,
                        mef_actions={mef_record.pid: Action.DELETE},
                    )
                    changed = True
            if changed:
                mef_record.update(data=mef_record, dbcommit=dbcommit, reindex=reindex)
        # Flush VIAF index so ES reflects this cluster's updated agent list
        # before get_viaf() queries run inside create_or_update_mef.
        if reindex:
            self.flush_indexes()
        # Recreate MEF records
        for data in viaf_agents_data:
            agent_record, action = update_online(
                agent_class=data["record_class"], pid=data["pid"], online=online
            )
            if agent_record:
                _, mef_actions = agent_record.create_or_update_mef(
                    dbcommit=dbcommit, reindex=reindex, viaf_record=self
                )
                actions = set_actions(
                    actions=actions,
                    pid=agent_record.pid,
                    source_name=agent_record.name,
                    action=action,
                    mef_actions=mef_actions,
                )
            else:
                mef_records = AgentMefRecord.get_mef(data["pid"], data["record_class"])
                mef_actions = {}
                for mef_record in mef_records:
                    mef_record.update(
                        data=mef_record, dbcommit=dbcommit, reindex=reindex
                    )
                    mef_actions[mef_record.pid] = Action.DISCARD
                actions = set_actions(
                    actions=actions,
                    pid=data["pid"],
                    source_name=data["source"],
                    action=Action.NOT_FOUND,
                    mef_actions=mef_actions,
                )
        # Create Mef records for old agents
        if reindex:
            AgentMefRecord.flush_indexes()
        for entity_pid, agent in old_agents.items():
            viaf_updated = False
            if update_viaf and getattr(agent, "viaf_source_code", None):
                try:
                    viaf_data, msg = AgentViafRecord.get_online_record(
                        viaf_source_code=agent.viaf_source_code, pid=entity_pid
                    )
                    if verbose:
                        click.echo(msg)
                    if viaf_data and not viaf_data.get("NO TRANSFORMATION"):
                        new_viaf_record, viaf_action = AgentViafRecord.create_or_update(
                            data=viaf_data, dbcommit=dbcommit, reindex=reindex
                        )
                        if new_viaf_record:
                            new_viaf_record.create_mef_and_agents(
                                dbcommit=dbcommit, reindex=reindex
                            )
                        actions.setdefault(entity_pid, {})
                        actions[entity_pid]["viaf_update"] = viaf_action
                        viaf_updated = viaf_action in (
                            Action.CREATE,
                            Action.UPDATE,
                            Action.REPLACE,
                        )
                except RetryableVIAFError as err:
                    if verbose:
                        click.echo(
                            f"  VIAF lookup failed for {agent.name}:{entity_pid}: {err}"
                        )
            if not viaf_updated:
                mef_record, mef_actions = agent.create_or_update_mef(
                    dbcommit=dbcommit, reindex=reindex
                )
                actions.setdefault(entity_pid, {})
                actions[entity_pid].setdefault("MEF", {})
                for pid, action in mef_actions.items():
                    actions[entity_pid]["MEF"][pid] = action
        return actions

    def reindex(self, forceindex=False):
        """Reindex record."""
        result = super().reindex(forceindex=forceindex)
        self.flush_indexes()
        return result

    @classmethod
    def get_online_record(cls, viaf_source_code, pid, rec_format=None):
        """Get VIAF record.

        Get's the VIAF record from: http://www.viaf.org/viaf/sourceID/{source_code}|{pid}

        :param viaf_source_code: agent source code
        :param pid: pid for agent source code
        :param rec_format: raw = get the not transformed VIAF record link = get the VIAF link record
        :returns: VIAF record as json
        """
        viaf_url = current_app.config.get("RERO_MEF_VIAF_BASE_URL")
        url = f"{viaf_url}/viaf"
        connect_timeout = current_app.config.get("RERO_MEF_VIAF_CONNECT_TIMEOUT")
        read_timeout = current_app.config.get("RERO_MEF_VIAF_READ_TIMEOUT")
        retries = current_app.config.get("RERO_MEF_VIAF_RETRIES")
        total_timeout = current_app.config.get("RERO_MEF_VIAF_TOTAL_TIMEOUT")
        request_delay = current_app.config.get("RERO_MEF_VIAF_REQUEST_DELAY")
        request_jitter = current_app.config.get("RERO_MEF_VIAF_REQUEST_JITTER", 0)
        retry_after_default = current_app.config.get(
            "RERO_MEF_VIAF_RETRY_AFTER_DEFAULT"
        )
        retry_after_max = current_app.config.get("RERO_MEF_VIAF_RETRY_AFTER_MAX")
        user_agent = current_app.config.get(
            "RERO_MEF_VIAF_USER_AGENT",
            f"rero-mef/{__version__} (+https://github.com/rero/rero-mef)",
        )

        headers = {
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": user_agent,
        }

        if viaf_source_code.upper() == "VIAF":
            url = f"{url}/{pid}"
        else:
            source_id = quote(str(viaf_source_code), safe="")
            source_pid = quote(str(pid), safe="")
            url = f"{url}/sourceID/{source_id}%7C{source_pid}"

        if request_delay:
            time.sleep(float(request_delay) + random.uniform(0, float(request_jitter)))

        # 429 is handled explicitly below so we can cap Retry-After sleeps.
        retry_statuses = (500, 502, 503, 504)

        def _perform_request():
            if (
                total_timeout
                and hasattr(signal, "SIGALRM")
                and threading.current_thread() is threading.main_thread()
            ):

                def _on_timeout(_signum, _frame):
                    raise TimeoutError(f"request exceeded {total_timeout}s")

                previous_handler = signal.getsignal(signal.SIGALRM)
                signal.signal(signal.SIGALRM, _on_timeout)
                signal.setitimer(signal.ITIMER_REAL, float(total_timeout))
                try:
                    return requests_retry_session(
                        retries=retries,
                        backoff_factor=1,
                        status_forcelist=retry_statuses,
                    ).get(
                        url,
                        headers=headers,
                        timeout=(connect_timeout, read_timeout),
                    )
                finally:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    signal.signal(signal.SIGALRM, previous_handler)

            return requests_retry_session(
                retries=retries,
                backoff_factor=1,
                status_forcelist=retry_statuses,
            ).get(
                url,
                headers=headers,
                timeout=(connect_timeout, read_timeout),
            )

        max_attempts = 2
        response = None
        for attempt in range(1, max_attempts + 1):
            try:
                # requests' connect/read timeouts are not always sufficient to bound
                # total wall-clock time under some network/proxy conditions.
                response = _perform_request()
            except (TimeoutError, requests.RequestException) as e:
                msg = f"VIAF get: {pid:<15} {url} | REQUEST ERROR: {e}"
                if attempt >= max_attempts:
                    raise RetryableVIAFError(msg) from e
                continue

            if response.status_code != 429:
                break

            retry_after = response.headers.get("Retry-After")
            try:
                requested_sleep = (
                    int(retry_after) if retry_after else retry_after_default
                )
            except TypeError, ValueError:
                requested_sleep = retry_after_default
            capped_sleep = min(requested_sleep, retry_after_max)
            wait_msg = (
                f"VIAF get: {pid:<15} {url} | RATE LIMITED (429) "
                f"Retry-After={requested_sleep}s"
                + (
                    f" (capped to {capped_sleep}s)"
                    if capped_sleep < requested_sleep
                    else ""
                )
            )
            if attempt >= max_attempts:
                raise RetryableVIAFError(wait_msg)
            click.echo(wait_msg)
            _sleep_with_countdown(capped_sleep)
            continue

        result = {}
        msg = f"VIAF get: {pid:<15} {url} | HTTP {response.status_code}"
        if response.status_code == requests.codes.ok:
            msg = f"VIAF get: {pid:<15} {url} | OK"
            try:
                data_json = response.json()

                # Handle new API format with ns1:VIAFCluster wrapper
                if "ns1:VIAFCluster" in data_json:
                    data_json = data_json["ns1:VIAFCluster"]

                if rec_format == "raw":
                    return data_json, msg

                # Extract VIAF ID (handle both old and new format, ensure string type)
                viaf_id = data_json.get("viafID") or data_json.get("ns1:viafID")
                result["pid"] = str(viaf_id) if viaf_id else None

                # Extract sources (handle both old and new format with ns1: prefix)
                sources_data = (
                    data_json.get("sources") or data_json.get("ns1:sources") or {}
                )
                if isinstance(sources_data, dict):
                    sources = sources_data.get("source") or sources_data.get(
                        "ns1:source"
                    )
                else:
                    sources = None

                if sources:
                    if isinstance(sources, dict):
                        sources = [sources]
                    for source in sources:
                        # get pid (handle both old and new format, ensure string type)
                        text = source.get("content") or source.get("#text", "|")
                        text = str(text).split("|")
                        if bib_source := cls.sources.get(text[0], {}).get("name"):
                            result[f"{bib_source}_pid"] = text[1]
                            # get URL (handle both old and new format)
                            nsid = source.get("nsid") or source.get("@nsid")
                            if nsid and str(nsid).startswith("http"):
                                result[bib_source] = nsid

                    # get Wikipedia URLs (handle both old and new format)
                    x_links_data = (
                        data_json.get("xLinks") or data_json.get("ns1:xLinks") or {}
                    )
                    x_links = (
                        x_links_data.get("xLink", [])
                        if isinstance(x_links_data, dict)
                        else []
                    )
                    if not isinstance(x_links, list):
                        x_links = [x_links]
                    for x_link in x_links:
                        if isinstance(x_link, dict) and result.get("wiki_pid"):
                            # Handle both old and new format
                            text = x_link.get("content") or x_link.get("#text")
                            if text and "wikipedia" in text:
                                result.setdefault("wiki", []).append(
                                    text.replace('"', "%22")
                                )
                    if wiki_urls := result.get("wiki"):
                        result["wiki"] = sorted(wiki_urls)
            except Exception as e:
                current_app.logger.exception(
                    f"Error parsing VIAF response for {pid}: {e}"
                )
                return {}, f"VIAF get: {pid:<15} {url} | PARSE ERROR: {e}"

        # make sure we got a VIAF with the same pid for source
        if viaf_source_code.upper() == "VIAF":
            if result.get("pid") == pid:
                return result, msg
            # Redirect detected: VIAF cluster was merged into another
            if result.get("pid"):
                result["redirect_from"] = pid
                return None, (
                    f"VIAF get: {pid:<15} {url} | REDIRECT -> {result['pid']}"
                )
        elif (
            result.get(f"{cls.sources.get(viaf_source_code, {}).get('name')}_pid")
            == pid
        ):
            return result, msg
        return {}, f"VIAF get: {pid:<15} {url} | NO RECORD"

    def update_online(self, dbcommit=False, reindex=False):
        """Update online.

        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex record.
        :returns: record and actions message.
        """
        try:
            online_data, msg = self.get_online_record(
                viaf_source_code="VIAF", pid=self.pid
            )
        except RetryableVIAFError as err:
            current_app.logger.warning(f"VIAF update failed for {self.pid}: {err}")
            return None, Action.ERROR
        if redirect_to_pid := _get_redirect_pid_from_msg(msg):
            new_record, action, _redirect_info = self.handle_redirect(
                redirect_to_pid=redirect_to_pid,
                dbcommit=dbcommit,
                reindex=reindex,
            )
            return new_record, action
        if online_data:
            online_data["$schema"] = self["$schema"]
            _md5.add_md5(online_data)
            if online_data["md5"] == self.get("md5"):
                return self, Action.UPTODATE
            return (
                self.replace(data=online_data, dbcommit=dbcommit, reindex=reindex),
                Action.REPLACE,
            )
        return None, Action.DISCARD

    def handle_redirect(
        self, redirect_to_pid, dbcommit=False, reindex=False, delete_if_not_found=False
    ):
        """Handle VIAF cluster merge (redirect).

        When a VIAF cluster is merged into another, the old VIAF ID
        redirects to the new one. This method:
        1. Fetches and creates/updates the target VIAF record
        2. Deletes the old VIAF record (which cleans up MEF via delete())
        3. Logs the redirect for audit

        :param redirect_to_pid: The new VIAF PID (redirect target).
        :param dbcommit: Commit changes to DB.
        :param reindex: Reindex records.
        :param delete_if_not_found: Delete old record even if target not found or error occurs.
        :returns: Tuple (new_record, action, redirect_info_dict).
        """
        old_pid = self.pid
        redirect_info = {
            "from": old_pid,
            "to": redirect_to_pid,
        }
        current_app.logger.info(f"VIAF redirect: {old_pid} -> {redirect_to_pid}")
        # Fetch the target VIAF record
        try:
            target_data, msg = self.get_online_record(
                viaf_source_code="VIAF", pid=redirect_to_pid
            )
        except RetryableVIAFError as err:
            current_app.logger.warning(
                f"VIAF redirect target fetch failed transiently: "
                f"{old_pid} -> {redirect_to_pid} | {err}"
            )
            return None, Action.ERROR, redirect_info
        if redirected_to_pid := _get_redirect_pid_from_msg(msg):
            current_app.logger.warning(
                f"VIAF redirect target chained: "
                f"{old_pid} -> {redirect_to_pid} -> {redirected_to_pid} | {msg}"
            )
            if delete_if_not_found:
                current_app.logger.info(
                    f"Deleting old VIAF record {old_pid} due to chained redirect"
                )
                self.delete(force=True, dbcommit=dbcommit, delindex=reindex)
            return None, Action.ERROR, redirect_info
        if not target_data:
            current_app.logger.warning(
                f"VIAF redirect target not found: "
                f"{old_pid} -> {redirect_to_pid} | {msg}"
            )
            if delete_if_not_found:
                current_app.logger.info(
                    f"Deleting old VIAF record {old_pid} as target not found"
                )
                self.delete(force=True, dbcommit=dbcommit, delindex=reindex)
            return None, Action.ERROR, redirect_info
        target_data = _md5.add_md5(target_data)

        try:
            new_record, _ = self.create_or_update(
                data=target_data,
                dbcommit=dbcommit,
                reindex=reindex,
                test_md5=True,
            )
        except Exception as e:
            current_app.logger.exception(
                f"Failed to create/update target VIAF {redirect_to_pid}: {e}"
            )
            if delete_if_not_found:
                current_app.logger.info(
                    f"Deleting old VIAF record {old_pid} due to target creation error"
                )
                self.delete(force=True, dbcommit=dbcommit, delindex=reindex)
            return None, Action.ERROR, redirect_info

        if new_record:
            new_record.create_mef_and_agents(dbcommit=dbcommit, reindex=reindex)
        # Delete old VIAF record (handles MEF cleanup) only after successful create/update
        self.delete(force=True, dbcommit=dbcommit, delindex=reindex)

        return new_record, Action.REDIRECT, redirect_info

    @classmethod
    def get_viaf(cls, agent):
        """Get VIAF record by agent.

        :param agent: Agency do get corresponding VIAF record.
        """
        if isinstance(agent, AgentMefRecord):
            return [cls.get_record_by_pid(agent.get("viaf_pid"))]
        if isinstance(agent, AgentViafRecord):
            return [cls.get_record_by_pid(agent.get("pid"))]
        pid = agent.get("pid")
        viaf_pid_name = agent.viaf_pid_name
        query = (
            AgentViafSearch()
            .filter({"term": {viaf_pid_name: pid}})
            .params(preserve_order=True)
            .sort({"_updated": {"order": "desc"}})
        )
        viaf_records = [
            cls.get_record_by_pid(hit.pid) for hit in query.source("pid").scan()
        ]
        if len(viaf_records) > 1:
            current_app.logger.error(
                f"MULTIPLE VIAF FOUND FOR: {agent.name} {agent.pid} | "
                f"viaf: {', '.join([viaf.pid for viaf in viaf_records])}"
            )
        return viaf_records

    @classmethod
    def create_or_update(
        cls,
        data,
        id_=None,
        delete_pid=True,
        dbcommit=False,
        reindex=False,
        test_md5=False,
    ):
        """Create or update VIAF record."""
        record, action = super().create_or_update(
            data=data,
            id_=id_,
            delete_pid=delete_pid,
            dbcommit=dbcommit,
            reindex=reindex,
            test_md5=test_md5,
        )
        return record, action

    def delete(self, force=True, dbcommit=False, delindex=False):
        """Delete record and persistent identifier.

        :param force: Force-delete the record (always True for VIAF records).
        :param dbcommit: Commit changes to DB.
        :param delindex: Remove record from index.
        :returns: Tuple (result, Action.DELETE, mef_actions).
        """
        agents_records = self.get_entities_records()
        mef_records = AgentMefRecord.get_mef(entity_pid=self.pid, entity_name=self.name)
        # delete VIAF record
        result = super().delete(force=True, dbcommit=dbcommit, delindex=delindex)

        # Clean MEF records
        mef_actions = {}
        old_agent_records = {}
        for mef_record in mef_records:
            mef_actions[mef_record.pid] = {}
            mef_agents_records = mef_record.get_entities_records()
            if len(mef_agents_records):
                mef_actions[mef_record.pid][mef_agents_records[0].name] = {
                    mef_agents_records[0].pid: Action.UPDATE
                }
            # Guard: if create_mef_and_agents for a redirect target already migrated
            # this MEF record to a new VIAF cluster, the DB record's viaf_pid no longer
            # matches self.pid (ES may still show the old value when reindex=False).
            # Cleaning up an already-migrated record would strip the new viaf_pid.
            current_viaf_pid = mef_record.get("viaf_pid")
            if current_viaf_pid != self.pid:
                mef_actions[mef_record.pid]["viaf"] = {current_viaf_pid: Action.DISCARD}
                continue
            for mef_agent_record in mef_agents_records[1:]:
                if mef_agent_record in agents_records:
                    mef_record.pop(mef_agent_record.name)
                    mef_actions[mef_record.pid][mef_agent_record.name] = {
                        mef_agent_record.pid: Action.DELETE
                    }
                    old_agent_records[mef_agent_record.pid] = mef_agent_record
            mef_record.pop("viaf_pid", None)
            mef_actions[mef_record.pid]["viaf"] = {current_viaf_pid: Action.DELETE}
            mef_record.update(data=mef_record, dbcommit=True, reindex=True)
            AgentMefRecord.flush_indexes()
        # recreate MEF records for agents
        for agent_record in old_agent_records.values():
            mef, _ = agent_record.create_or_update_mef(dbcommit=True, reindex=True)
            mef_actions[mef.pid] = {
                agent_record.name: {agent_record.pid: Action.CREATE}
            }
        AgentMefRecord.flush_indexes()
        return result, Action.DELETE, mef_actions

    def get_entities_pids(self):
        """Get agent pids."""
        agents = []
        for source, record_class in self.sources_used.items():
            if source_pid := self.get(f"{source}_pid"):
                agents.append(
                    {"source": source, "record_class": record_class, "pid": source_pid}
                )
        return agents

    def get_entities_records(self, verbose=False):
        """Get agent records."""
        agent_records = []
        for agent in self.get_entities_pids():
            record_class = agent["record_class"]
            if agent_record := record_class.get_record_by_pid(agent["pid"]):
                agent_records.append(agent_record)
            elif verbose:
                current_app.logger.warning(
                    f"Record not found VIAF: {self.pid} "
                    f"{agent['record_class'].name}: {agent['pid']}"
                )
        return agent_records

    @classmethod
    def get_missing_entity_pids(cls, agent, verbose=False):
        """Get all missing pids defined in VIAF.

        :param agent: Agent to search for missing pids.
        :param verbose: Verbose.
        :returns: Agent pids without VIAF, VIAF pids without agent
        """
        if record_class := get_entity_class(agent):
            if verbose:
                click.echo(f"Get pids from {agent} ...")
            progress = progressbar(
                items=record_class.get_all_pids(),
                length=record_class.count(),
                verbose=verbose,
            )
            pids_db = set(progress)

            entity_pid_name = f"{record_class.name}_pid"
            if verbose:
                click.echo(f"Get pids from VIAF with {entity_pid_name} ...")
            query = AgentViafSearch().filter(
                "bool", should=[Q("exists", field=entity_pid_name)]
            )
            progress = progressbar(
                items=query.source(["pid", entity_pid_name]).scan(),
                length=query.count(),
                verbose=verbose,
            )
            pids_viaf = []
            for hit in progress:
                viaf_pid = hit.pid
                entity_pid = hit.to_dict().get(entity_pid_name)
                if entity_pid in pids_db:
                    pids_db.discard(entity_pid)
                else:
                    pids_viaf.append(viaf_pid)
            return list(pids_db), pids_viaf
        click.secho(f"ERROR Record class not found for: {agent}", fg="red")
        return [], []

    @classmethod
    def get_pids_with_multiple_viaf(cls, verbose=False):
        """Get agent pids with multiple MEF records.

        :param verbose: Verbose.
        :returns: pids.
        """
        multiple_pids = {
            f"{source}_pid": {} for source in AgentViafRecord(data={}).sources_used
        }
        cleaned_pids = deepcopy(multiple_pids)
        progress = progressbar(
            items=AgentViafSearch()
            .params(preserve_order=True)
            .sort({"pid": {"order": "asc"}})
            .scan(),
            length=AgentViafSearch().count(),
            verbose=verbose,
        )
        for hit in progress:
            viaf_pid = hit.pid
            data = hit.to_dict()
            for source in multiple_pids:
                if pid := data.get(source):
                    multiple_pids[source].setdefault(pid, [])
                    multiple_pids[source][pid].append(viaf_pid)
        for source, pids in multiple_pids.items():
            for pid, viaf_pids in pids.items():
                if len(viaf_pids) > 1:
                    cleaned_pids[source][pid] = viaf_pids
        return cleaned_pids


class AgentViafIndexer(EntityIndexer):
    """Agent VIAF indexer."""

    record_cls = AgentViafRecord

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(
            record_id_iterator, index=AgentViafSearch.Meta.index, doc_type="viaf"
        )
