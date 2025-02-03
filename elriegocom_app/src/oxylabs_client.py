import os
import requests
from pprint import pprint


class OxylabsClient:
    def __init__(self, username, password):
        self.username = username
        self.password = password
    
    def oxylabs_retrieve_bestsellers(self, category_id):

        payload = {
        'source': 'amazon_bestsellers',
        'render': 'html',
        'parse': True,
        'query': category_id,
        'domain': 'es',
        'user_agent_type': 'desktop',
        'start_page': '1'
    }

        print(f'Retrieving Bestsellers from Amazon with ID: {category_id}...')
        # Get response.
        response = requests.request(
            'POST',
            'https://realtime.oxylabs.io/v1/queries',
            auth=(self.username, self.password),
            json=payload,
        )

        # Instead of response with job status and results url, this will return the
        # JSON response with results.
        return response.json()

    def oxylabs_retrieve_product_data(self, asin):
        print(f'Retrieving Product Data from Amazon with ASIN: {asin}...')
        payload = {
    'source': 'amazon_product',
    'domain': 'es',
    'user_agent_type': 'desktop',
    'parse': True,
    'render': 'html',
    'query': asin
    }

        # Get response.
        response = requests.request(
            'POST',
            'https://realtime.oxylabs.io/v1/queries',
            auth=(self.username, self.password), #Your credentials go here
            json=payload,
        )

        # Instead of response with job status and results url, this will return the
        # JSON response with results.
        return response.json()
