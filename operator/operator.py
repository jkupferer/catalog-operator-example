#!/usr/bin/env python3

import logging
import os

from datetime import datetime

import kopf
import kubernetes_asyncio

from infinite_relative_backoff import InfiniteRelativeBackoff

operator_domain = os.environ.get('OPERATOR_DOMAIN', 'babylon.gpte.redhat.com')
operator_version = os.environ.get('OPERATOR_VERSION', 'v1')

kubernetes_asyncio.config.load_incluster_config()
custom_objects_api = kubernetes_asyncio.client.CustomObjectsApi()

@kopf.on.startup()
async def on_startup(logger, settings, **_):
    global custom_objects_api

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

    if name == 'tests.test-empty-config.prod' and namespace == 'babylon-catalog-test':
        logger.info("Update timestamp")
        await babylon.custom_objects_api.patch_namespaced_custom_object_status(
            group = operator_domain,
            name = name,
            namespace = namespace,
            plural = 'catalogitems',
            version = operator_version,
            body = {
                "annotations": {
                    "timestamp": datetime.utcnow().strftime('%FT%TZ'),
                }
            },
            _content_type = 'application/merge-patch+json',
        )
        self.update_from_definition(definition)
