"""
Support Bundle Keywords - creates SupportBundle() instance and delegates - NO direct API calls!
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))  # noqa: E402

from utility.utility import logging  # noqa: E402
from support_bundle import SupportBundle  # noqa: E402
from constant import DEFAULT_TIMEOUT, SUPPORTBUNDLE_STATE_READY  # noqa: E402


class support_bundle_keywords:
    """Layer 3: SupportBundle keyword wrapper."""

    def __init__(self):
        self.support_bundle = SupportBundle()

    def create_support_bundle(self, name, description):
        logging(f"Creating support bundle {name}")
        return self.support_bundle.create(name, description)

    def wait_for_support_bundle_ready(self, name, timeout=DEFAULT_TIMEOUT):
        logging(f"Waiting for support bundle {name} to be ready")
        return self.support_bundle.wait_for_state(name, SUPPORTBUNDLE_STATE_READY, timeout)

    def delete_support_bundle_if_exists(self, name):
        logging(f"Deleting support bundle {name} if it exists")
        self.support_bundle.delete_if_exists(name)
