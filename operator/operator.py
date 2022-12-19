#!/usr/bin/env python3

import logging
import os

import kopf
import kubernetes_asyncio

from infinite_relative_backoff import InfiniteRelativeBackoff

operator_domain = os.environ.get('OPERATOR_DOMAIN', 'babylon.gpte.redhat.com')
operator_version = os.environ.get('OPERATOR_VERSION', 'v1')

@kopf.on.startup()
async def on_startup(logger, settings, **_):
    # Store last handled configuration in status
    settings.persistence.diffbase_storage = kopf.StatusDiffBaseStorage(field='status.diffBase')

    # Never give up from network errors
    settings.networking.error_backoffs = InfiniteRelativeBackoff()

    # Use operator domain as finalizer
    settings.persistence.finalizer = operator_domain

    # Store progress in status.
    settings.persistence.progress_storage = kopf.StatusProgressStorage(field='status.kopf.progress')

    # Only create events for warnings and errors
    settings.posting.level = logging.WARNING

    # Disable scanning for CustomResourceDefinitions updates
    settings.scanning.disabled = True

@kopf.timer(operator_domain, operator_version, 'catalogitems', interval=5)
async def catalog_item_timer(annotations, labels, name, namespace, spec, logger, **_):
    logger.info(f"CatalogItem {name} in {namespace}")
