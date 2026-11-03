"""
SupportBundle component wrapper.
Layer 4: delegates to CRD or REST implementation based on HARVESTER_OPERATION_STRATEGY.
"""
import os

from constant import HarvesterOperationStrategy
from support_bundle.base import Base
from support_bundle.crd import CRD
from support_bundle.rest import Rest


class SupportBundle(Base):
    """Selects the CRD or REST implementation at construction time."""

    def __init__(self):
        strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
        if strategy_str == HarvesterOperationStrategy.REST.value:
            self._impl = Rest()
        else:
            self._impl = CRD()

    def create(self, name, description):
        return self._impl.create(name, description)

    def wait_for_state(self, name, state, timeout):
        return self._impl.wait_for_state(name, state, timeout)

    def delete_if_exists(self, name):
        return self._impl.delete_if_exists(name)
