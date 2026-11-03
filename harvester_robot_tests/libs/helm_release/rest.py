"""
Helm release REST implementation stub.
Layer 4: Harvester's REST API doesn't expose Helm release values.
"""
from helm_release.base import Base


class Rest(Base):
    """REST strategy stub — all methods raise NotImplementedError."""

    def get_values(self, namespace, release):
        raise NotImplementedError("REST strategy not supported for Helm release values")
