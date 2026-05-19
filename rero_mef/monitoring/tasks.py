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

"""Celery task: periodic OpenSearch cluster-health snapshot."""

import logging
from datetime import UTC, datetime

from celery import shared_task
from invenio_search import current_search_client

logger = logging.getLogger(__name__)


def _last_snapshot(client, node_id):
    """Return the most recent os-monitor doc for this node, or None."""
    try:
        result = client.search(
            index="os-monitor-*",
            body={
                "size": 1,
                "sort": [{"@timestamp": "desc"}],
                "query": {"term": {"node.id": node_id}},
                "_source": [
                    "@timestamp",
                    "node.indices.search_query_total",
                    "node.indices.index_total",
                    "node.indices.index_failed_total",
                ],
            },
        )
        hits = result["hits"]["hits"]
        return hits[0]["_source"] if hits else None
    except Exception as e:
        logger.exception("_last_snapshot failed for node %s: %s", node_id, e)
        return None


def _rate(current, prev_src, field, elapsed):
    """Compute per-second rate between two cumulative counter values."""
    prev = (
        prev_src.get("node", {}).get("indices", {}).get(field, current)
        if prev_src
        else current
    )
    return round(max(0.0, (current - prev) / max(elapsed, 1)), 4)


@shared_task(ignore_result=True)
def index_os_stats():
    """Index one OpenSearch cluster-stats snapshot into os-monitor-YYYY.MM.dd.

    Collects cluster health and per-node JVM, OS, index and filesystem
    statistics. Search and index throughput are stored as per-second rates
    (computed against the previous snapshot) so the dashboard charts show
    meaningful activity rather than ever-growing cumulative counters.
    """
    client = current_search_client
    health = client.cluster.health()
    nodes = client.nodes.stats(metric="jvm,os,indices,fs,breaker")

    now = datetime.now(UTC)
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    index_name = f"os-monitor-{now.strftime('%Y.%m.%d')}"
    status_code = {"green": 0, "yellow": 1, "red": 2}.get(health["status"], -1)

    for node_id, ns in nodes["nodes"].items():
        prev = _last_snapshot(client, node_id)
        if prev:
            prev_ts = datetime.fromisoformat(prev["@timestamp"].replace("Z", "+00:00"))
            elapsed = (now - prev_ts).total_seconds()
        else:
            elapsed = 60

        fs = ns.get("fs", {}).get("total", {})
        total_bytes = fs.get("total_in_bytes", 1)
        free_bytes = fs.get("free_in_bytes", 0)

        curr_search = ns["indices"]["search"]["query_total"]
        curr_index = ns["indices"]["indexing"]["index_total"]
        curr_failed = ns["indices"]["indexing"]["index_failed"]

        doc = {
            "@timestamp": timestamp,
            "cluster": {
                "status": health["status"],
                "status_code": status_code,
                "active_shards": health["active_shards"],
                "active_primary_shards": health["active_primary_shards"],
                "unassigned_shards": health["unassigned_shards"],
                "relocating_shards": health["relocating_shards"],
                "initializing_shards": health["initializing_shards"],
                "number_of_nodes": health["number_of_nodes"],
            },
            "node": {
                "id": node_id,
                "name": ns["name"],
                "jvm": {
                    "heap_used_percent": ns["jvm"]["mem"]["heap_used_percent"],
                    "heap_used_bytes": ns["jvm"]["mem"]["heap_used_in_bytes"],
                    "heap_max_bytes": ns["jvm"]["mem"]["heap_max_in_bytes"],
                    "gc_old_count": ns["jvm"]["gc"]["collectors"]["old"][
                        "collection_count"
                    ],
                    "gc_old_time_ms": ns["jvm"]["gc"]["collectors"]["old"][
                        "collection_time_in_millis"
                    ],
                },
                "os": {
                    "cpu_percent": ns["os"]["cpu"]["percent"],
                    "mem_used_percent": ns["os"]["mem"]["used_percent"],
                },
                "fs": {
                    "total_bytes": total_bytes,
                    "free_bytes": free_bytes,
                    "disk_used_percent": round(
                        100.0 * (1.0 - free_bytes / max(total_bytes, 1)), 2
                    ),
                },
                "indices": {
                    "docs_count": ns["indices"]["docs"]["count"],
                    "docs_deleted": ns["indices"]["docs"]["deleted"],
                    "store_bytes": ns["indices"]["store"]["size_in_bytes"],
                    "search_query_total": curr_search,
                    "search_query_time_ms": ns["indices"]["search"][
                        "query_time_in_millis"
                    ],
                    "search_fetch_total": ns["indices"]["search"]["fetch_total"],
                    "search_queries_per_sec": _rate(
                        curr_search, prev, "search_query_total", elapsed
                    ),
                    "index_total": curr_index,
                    "index_time_ms": ns["indices"]["indexing"]["index_time_in_millis"],
                    "index_ops_per_sec": _rate(
                        curr_index, prev, "index_total", elapsed
                    ),
                    "index_failed_total": curr_failed,
                    "index_failures_per_sec": _rate(
                        curr_failed, prev, "index_failed_total", elapsed
                    ),
                },
            },
        }
        client.index(index=index_name, body=doc)
