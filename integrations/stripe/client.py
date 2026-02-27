import stripe

class StripeClient:
    def __init__(self, api_key):
        self.api_key = api_key
        stripe.api_key = self.api_key

    def create_charge(self, amount, currency, source):
        # Logic to create a charge
        pass

    def list_charges(self):
        # Logic to list charges
        pass
