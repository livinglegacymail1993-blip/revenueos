"""Stripe ingestion logic. Canonical location for ingest behavior."""

from .client import StripeClient


class StripeIngest:
    def __init__(self, client: StripeClient):
        self.client = client

    def ingest_charges(self):
        # Logic to ingest charges from Stripe
        pass
