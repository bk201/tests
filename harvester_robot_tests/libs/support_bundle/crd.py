"""
SupportBundle CRD Implementation - SupportBundle CRs in harvester-system.
"""
import time

from kubernetes.client.rest import ApiException

from constant import (
    HARVESTER_API_GROUP, HARVESTER_API_VERSION, HARVESTER_NAMESPACE,
    SUPPORTBUNDLE_PLURAL, SUPPORTBUNDLE_STATE_ERROR,
)
from crd import create_cr, get_cr, delete_cr, wait_for_cr_deleted
from support_bundle.base import Base
from utility.utility import logging, get_retry_count_and_interval


class CRD(Base):
    """SupportBundle implementation backed by Harvester CRDs."""

    def __init__(self):
        self.common_parameters = {
            "group": HARVESTER_API_GROUP,
            "version": HARVESTER_API_VERSION,
            "namespace": HARVESTER_NAMESPACE,
            "plural": SUPPORTBUNDLE_PLURAL,
        }
        _, self.retry_interval = get_retry_count_and_interval()

    def create(self, name, description):
        body = {
            "apiVersion": f"{HARVESTER_API_GROUP}/{HARVESTER_API_VERSION}",
            "kind": "SupportBundle",
            "metadata": {"name": name, "namespace": HARVESTER_NAMESPACE},
            "spec": {"description": description},
        }
        bundle = create_cr(**self.common_parameters, body=body)
        logging(f"Created support bundle {name}")
        return bundle

    def wait_for_state(self, name, state, timeout):
        endtime = time.time() + int(timeout)
        current = None
        while time.time() < endtime:
            try:
                bundle = get_cr(**self.common_parameters, name=name)
                current = bundle.get("status", {}).get("state", "")
                if current == state:
                    logging(f"Support bundle {name} is {state}")
                    return bundle
                if current == SUPPORTBUNDLE_STATE_ERROR:
                    conditions = bundle.get("status", {}).get("conditions", [])
                    raise AssertionError(f"Support bundle {name} failed: {conditions}")
                logging(f"Support bundle {name} is '{current}', waiting for {state}")
            except ApiException as e:
                logging(f"Error getting support bundle {name}: {e}", "WARNING")
            time.sleep(self.retry_interval)
        raise AssertionError(
            f"Support bundle {name} didn't become {state} within {timeout}s (last: '{current}')")

    def delete_if_exists(self, name):
        try:
            delete_cr(**self.common_parameters, name=name)
        except ApiException as e:
            if e.status == 404:
                return
            raise
        wait_for_cr_deleted(**self.common_parameters, name=name)
        logging(f"Deleted support bundle {name}")
