# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tasks used by  RERO-MEF."""

from celery import shared_task
from flask import current_app

from ...marctojson.do_idref_concepts import Transformation
from ...utils import (
    MyOAIItemIterator,
    SickleWithRetries,
    oai_get_record,
    oai_process_records_from_dates,
    oai_save_records_from_dates,
)
from .api import ConceptIdrefRecord


@shared_task
def process_records_from_dates(
    from_date=None,
    until_date=None,
    ignore_deleted=False,
    dbcommit=True,
    reindex=True,
    test_md5=True,
    verbose=False,
    debug=False,
    viaf_online=False,
    **kwargs,
):
    """Harvest multiple records from an OAI repo.

    :param from_date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    :param ignore_deleted: Ignore deleted records.
    :param dbcommit: Commit changes to DB.
    :param reindex: Reindex in ES.
    :param test_md5: Test MD5 for changes.
    :param verbose: Verbose print.
    :param debug: Debug print.
    :param viaf_online: Get also VIAF.
    """
    # data on IDREF Servers starts on 2000-10-01
    return oai_process_records_from_dates(
        name="concepts.idref",
        sickle=SickleWithRetries,
        max_retries=current_app.config.get("RERO_OAI_RETRIES", 0),
        oai_item_iterator=MyOAIItemIterator,
        transformation=Transformation,
        record_class=ConceptIdrefRecord,
        days_span=30,
        from_date=from_date,
        until_date=until_date,
        ignore_deleted=ignore_deleted,
        dbcommit=dbcommit,
        reindex=reindex,
        test_md5=test_md5,
        verbose=verbose,
        debug=debug,
        viaf_online=viaf_online,
        kwargs=kwargs,
    )


@shared_task
def save_records_from_dates(file_name, from_date=None, until_date=None, verbose=False):
    """Harvest and save multiple records from an OAI repo.

    :param file_name: Output file path for the harvested MARC records.
    :param from_date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    """
    # data on IDREF Servers starts on 2000-10-01
    return oai_save_records_from_dates(
        name="concepts.idref",
        file_name=file_name,
        sickle=SickleWithRetries,
        max_retries=current_app.config.get("RERO_OAI_RETRIES", 0),
        oai_item_iterator=MyOAIItemIterator,
        days_span=30,
        from_date=from_date,
        until_date=until_date,
        verbose=verbose,
    )


@shared_task
def idref_get_record(id_, debug=False):
    """Get a record from IDREF OAI repo."""
    return oai_get_record(
        id_=id_,
        name="concepts.idref",
        transformation=Transformation,
        identifier="oai:IdRefOAIServer.fr:",
        debug=debug,
    )
