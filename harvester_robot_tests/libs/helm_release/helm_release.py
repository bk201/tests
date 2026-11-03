"""
HelmRelease component wrapper.
Layer 4: delegates to CRD or REST implementation based on HARVESTER_OPERATION_STRATEGY.
"""
import os

from constant import HarvesterOperationStrategy
from helm_release.base import Base
from helm_release.crd import CRD
from helm_release.rest import Rest


class HelmRelease(Base):
    """Selects the CRD or REST implementation at construction time."""

    def __init__(self):
        strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
        if strategy_str == HarvesterOperationStrategy.REST.value:
            self._impl = Rest()
        else:
            self._impl = CRD()

    def get_values(self, namespace, release):
        return self._impl.get_values(namespace, release)
