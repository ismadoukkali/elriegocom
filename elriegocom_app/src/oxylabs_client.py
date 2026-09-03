import requests


class OxylabsClient:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def _post_query(self, payload):
        if not self.username or not self.password:
            raise Exception(
                "Oxylabs credentials missing. Set USER_NAME_OXYLABS and PASSWORD_OXYLABS in .env"
            )

        response = requests.post(
            'https://realtime.oxylabs.io/v1/queries',
            auth=(self.username, self.password),
            json=payload,
            timeout=120,
        )

        if response.status_code == 401:
            raise Exception(
                "Oxylabs authentication failed (401). Check USER_NAME_OXYLABS and PASSWORD_OXYLABS."
            )

        if not response.text:
            raise Exception(
                f"Oxylabs returned an empty response (HTTP {response.status_code})."
            )

        if response.status_code >= 400:
            raise Exception(
                f"Oxylabs request failed (HTTP {response.status_code}): {response.text[:500]}"
            )

        return response.json()
    
    def oxylabs_retrieve_bestsellers(self, category_id):
        payload = {
            'source': 'amazon_bestsellers',
            'render': 'html',
            'parse': True,
            'query': category_id,
            'domain': 'es',
            'user_agent_type': 'desktop',
            'start_page': '1',
        }

        print(f'Retrieving Bestsellers from Amazon with ID: {category_id}...')
        return self._post_query(payload)

    def oxylabs_retrieve_product_data(self, asin):
        print(f'Retrieving Product Data from Amazon with ASIN: {asin}...')
        payload = {
            'source': 'amazon_product',
            'domain': 'es',
            'user_agent_type': 'desktop',
            'parse': True,
            'render': 'html',
            'query': asin,
        }

        return self._post_query(payload)
