"""
SupportBundle REST implementation stub.
Layer 4: REST strategy is not yet supported for SupportBundle operations.
"""
from support_bundle.base import Base


class Rest(Base):
    """REST strategy stub — all methods raise NotImplementedError."""

    def create(self, name, description):
        raise NotImplementedError("REST strategy not yet supported for SupportBundle")

    def wait_for_state(self, name, state, timeout):
        raise NotImplementedError("REST strategy not yet supported for SupportBundle")

    def delete_if_exists(self, name):
        raise NotImplementedError("REST strategy not yet supported for SupportBundle")
