import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime
import pytz

load_dotenv()

class WixAPIClient:
    def __init__(self, api_key, account_id, site_id=None):
        self.base_url = 'https://www.wixapis.com'
        self.api_key = api_key
        self.account_id = account_id
        self.site_id = site_id
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': self.api_key,
            'wix-account-id': self.account_id
        }
        if site_id:
            self.headers['wix-site-id'] = site_id
    
    def get_collections(self, collection_id=None):
        """Get collections from Wix Data API"""
        endpoint = f'{self.base_url}/wix-data/v2/collections'
        if collection_id:
            endpoint += f'/{collection_id}'
        
        response = requests.get(endpoint, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.text}")
        return response.json()
    
    def insert_gardening_product(self, product_data, collection_id):
        """Insert a new gardening product into the collection.
        
        Args:
            product_data (dict): Dictionary containing the product information with these fields:
                - productName (str): Full name of the product
                - price (str): Price of the product
                - rating (float): Product rating
                - isAutomated (bool): Whether the product is automated
                - productUrl (str): Amazon product URL
                - image (str): Product image URL
                - descriptionOfProduct (str): Rich text description
                - opinionDeExperto (str): Expert opinion in rich text format
                - date (str): Date in ISO format (YYYY-MM-DD)
                - categora (str): Product category
                - marca (str): Product brand
                - discount (str, optional): Discount information
                - previousPrice (str, optional): Previous price if discounted
                
        Returns:
            dict: The created item data from the API response
        """
        endpoint = f'{self.base_url}/wix-data/v2/items'
        
        # Prepare the request body
        request_body = {
            "dataCollectionId": collection_id,
            "dataItem": {
                "data": product_data
            }
        }
        
        response = requests.post(endpoint, headers=self.headers, json=request_body)
        
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.text}")
        
        return response.json()
    
    def query_product_with_filters(self, collection_id, filter_params=None, sort_params=None, paging=None, return_total_count=True):
        """Query gardening products from the collection with optional filtering, sorting, and paging.
        
        Args:
            filter_params (dict, optional): Dictionary of field-value pairs to filter by.
                Example: {"marca": "Rainbird", "isAutomated": True}
            sort_params (list, optional): List of fields to sort by with direction.
                Example: [{"field": "price", "order": "DESC"}]
            paging (dict, optional): Paging parameters.
                Example: {"limit": 10, "offset": 0}
            return_total_count (bool, optional): Whether to return the total count in results.
                Default is True.
        
        Returns:
            dict: Query results containing dataItems and paging metadata
        """
        endpoint = f'{self.base_url}/wix-data/v2/items/query'
        
        # Prepare the query object
        query = {}
        
        if filter_params:
            query["filter"] = filter_params
            
        if sort_params:
            query["sort"] = sort_params
            
        if paging:
            query["paging"] = paging
        
        # Prepare the request body
        request_body = {
            "dataCollectionId": collection_id,
            "query": query,
            "returnTotalCount": return_total_count
        }
        
        response = requests.post(endpoint, headers=self.headers, json=request_body)
        
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.text}")
        
        return response.json()
    
    def query_product_by_asin(self, collection_id, asin, return_total_count=True):
        """Query a specific product from the collection using its ASIN.
        
        Args:
            collection_id (str): The ID of the collection to query
            asin (str): The ASIN of the product to find
            return_total_count (bool, optional): Whether to return the total count in results.
                Default is True.
        
        Returns:
            dict: Query results containing dataItems and paging metadata
        """
        endpoint = f'{self.base_url}/wix-data/v2/items/query'
        
        # Prepare the query object with ASIN filter
        query = {
            "filter": {
                "asin": {
                    "$eq": asin
                }
            }
        }
        
        # Prepare the request body
        request_body = {
            "dataCollectionId": collection_id,
            "query": query,
            "returnTotalCount": return_total_count
        }
        
        response = requests.post(endpoint, headers=self.headers, json=request_body)
        
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.text}")
    
        return response.json()
    
    def get_products_needing_price_update(self, days_threshold=1):
        """Query products that haven't had their prices updated in the specified number of days.
        
        Args:
            days_threshold (int, optional): Number of days to check against. Default is 1 day.
        
        Returns:
            dict: Query results containing products that need price updates
        """
        from datetime import datetime, timedelta
        
        # Calculate the cutoff timestamp
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        cutoff_str = cutoff_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        endpoint = f'{self.base_url}/wix-data/v2/items/query'
        
        # Prepare the query to find items where timestamp is older than cutoff
        # or where timestamp doesn't exist
        request_body = {
            "dataCollectionId": "GardeningAmazonProducts",
            "query": {
                "filter": {
                    "$or": [
                        {
                            "timestampOfPriceUpdate": {
                                "$lt": {"$date": cutoff_str}
                            }
                        },
                        {
                            "timestampOfPriceUpdate": None
                        }
                    ]
                },
                "paging": {
                    "limit": 1000  # Adjust this based on your needs
                }
            },
            "returnTotalCount": True
        }
        
        response = requests.post(endpoint, headers=self.headers, json=request_body)
        
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.text}")
        
        return response.json()

    def update_product(self, product_id, old_product_data, new_price, new_price_float, new_previous_price=None, new_discount=None):
        """Update the price, previous price, and discount of a product in the collection while preserving all other data.
        
        Args:
            product_id (str): The ID of the product to update
            old_product_data (dict): The existing product data to preserve
            new_price (str): The new price of the product
            new_previous_price (str, optional): The new previous price of the product
            new_discount (str, optional): The new discount information
        
        Returns:
            dict: The updated item data from the API response
        """
        endpoint = f'{self.base_url}/wix-data/v2/items/{product_id}'
        
        local_tz = pytz.timezone('Europe/Madrid')  # or 'Europe/Paris', depending on your location
        today = datetime.now(local_tz)
        # Format timestamp according to specified format
        utc_time = today.astimezone(pytz.UTC)
        iso_datetime = utc_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        # Option 2: Store with timezone information
        iso_datetime = today.isoformat()
        
        # Start with a copy of the old data to preserve all fields
        update_data = old_product_data.copy()
        
        # Update the specific fields
        update_data.update({
            "price": new_price,
            "price1": new_price_float,
            "timestampOfPriceUpdate": {
                "$date": iso_datetime
            }
        })
        
        # Update optional fields only if they are provided
        if new_previous_price is not None:
            update_data["previousPrice"] = new_previous_price
        
        if new_discount is not None:
            update_data["discount"] = new_discount
        
        # Prepare the request body according to the API documentation
        request_body = {
            "dataCollectionId": "GardeningAmazonProducts",
            "dataItem": {
                "data": update_data
            }
        }
        
        response = requests.put(endpoint, headers=self.headers, json=request_body)
        
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.text}")
        
        return response.json()
    
    def draft_blog_post(self, post_data, member_id=None):
        """Create a draft blog post using the Wix Blog API.
        
        Args:
            post_data (dict): Dictionary containing the blog post information with these fields:
                - title (str, required): Draft post title (max 200 chars)
                - excerpt (str, optional): Post excerpt (max 500 chars)
                - featured (bool, optional): Whether the post is featured
                - categoryIds (list, optional): List of category IDs (max 10)
                - hashtags (list, optional): List of hashtags (max 100)
                - commentingEnabled (bool, optional): Whether commenting is enabled
                - heroImage (dict, optional): Hero image data
                - tagIds (list, optional): List of tag IDs (max 30)
                - relatedPostIds (list, optional): List of related post IDs (max 3)
                - language (str, optional): Language code in IETF BCP 47 format
                - richContent (dict, required): Rich content in Ricos Document format
            member_id (str, required): The member ID of the post owner
                
        Returns:
            dict: The created draft post data from the API response
        
        Raises:
            ValueError: If required fields are missing or invalid
            Exception: If the API request fails
        """
        endpoint = f'{self.base_url}/blog/v3/draft-posts'
        
        # Validate required fields
        if not member_id:
            raise ValueError("member_id is required")
        if 'title' not in post_data:
            raise ValueError("Post title is required")
        if len(post_data['title']) > 200:
            raise ValueError("Post title exceeds maximum length of 200 characters")
        if 'richContent' not in post_data:
            raise ValueError("Rich content is required")

        # Create a clean copy of the post data
        clean_post_data = {
            "title": post_data['title'],
            "richContent": post_data['richContent'],
            "memberId": member_id  # Add the member_id to the request
        }
        
        # Add optional fields if they exist
        optional_fields = [
            'excerpt', 'featured', 'categoryIds', 'hashtags',
            'commentingEnabled', 'heroImage', 'tagIds',
            'relatedPostIds', 'language'
        ]
        
        for field in optional_fields:
            if field in post_data:
                clean_post_data[field] = post_data[field]
        
        # Validate field constraints
        if 'excerpt' in clean_post_data and len(clean_post_data['excerpt']) > 500:
            raise ValueError("Excerpt exceeds maximum length of 500 characters")
        if 'categoryIds' in clean_post_data and len(clean_post_data['categoryIds']) > 10:
            raise ValueError("Maximum of 10 category IDs allowed")
        if 'hashtags' in clean_post_data and len(clean_post_data['hashtags']) > 100:
            raise ValueError("Maximum of 100 hashtags allowed")
        if 'tagIds' in clean_post_data and len(clean_post_data['tagIds']) > 30:
            raise ValueError("Maximum of 30 tag IDs allowed")
        if 'relatedPostIds' in clean_post_data and len(clean_post_data['relatedPostIds']) > 3:
            raise ValueError("Maximum of 3 related post IDs allowed")
        
        # Prepare the request body
        request_body = {
            "draftPost": clean_post_data,
            "fieldsets": ["URL", "RICH_CONTENT"]
        }
        
        # Add required headers for blog API
        headers = self.headers.copy()
        
        try:
            response = requests.post(endpoint, headers=headers, json=request_body)
            response.raise_for_status()  # Raise exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                error_data = e.response.json()
                error_message = error_data.get('message', 'Unknown error occurred')
                raise ValueError(f"API request failed: {error_message}")
            raise Exception(f"API request failed: {str(e)}")
    
    def get_members(self, limit=50, offset=0, fieldsets=None):
        """List site members using the Wix Members API.
        
        Args:
            limit (int, optional): Number of items to load. Defaults to 50.
            offset (int, optional): Number of items to skip. Defaults to 0.
            fieldsets (list, optional): List of fieldsets to return. Options are ['PUBLIC', 'FULL'].
                Defaults to ['PUBLIC'].
                
        Returns:
            dict: Response containing members list and metadata
            
        Example:
            client = WixAPIClient(api_key="key", account_id="id")
            members = client.get_members(limit=10)
            for member in members['members']:
                print(f"Member ID: {member['id']}, Nickname: {member['profile']['nickname']}")
        """
        endpoint = f'{self.base_url}/members/v1/members'
        
        # Build query parameters
        params = {
            'paging.limit': limit,
            'paging.offset': offset
        }
        
        if fieldsets:
            params['fieldsets'] = fieldsets
        
        # Add required headers
        headers = self.headers.copy()
        
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                error_data = e.response.json()
                error_message = error_data.get('message', 'Unknown error occurred')
                raise ValueError(f"API request failed: {error_message}")
            raise Exception(f"API request failed: {str(e)}")



################################################################################


# Example usage
def getting_a_collection():
    api_key = os.getenv('WIX_API_KEY')
    account_id = os.getenv('WIX_ACCOUNT_ID')
    site_id = os.getenv('WIX_SITE_ID')
    
    client = WixAPIClient(api_key, account_id, site_id)
    
    try:
        # Get collections
        collections = client.get_collections(collection_id="GardeningAmazonProducts")
        print("Collections:", json.dumps(collections, indent=2))
                  
    except Exception as e:
        print(f"Error: {str(e)}")

def test_insert_product():
    api_key = os.getenv('WIX_API_KEY')
    account_id = os.getenv('WIX_ACCOUNT_ID')
    site_id = os.getenv('WIX_SITE_ID')
    
    client = WixAPIClient(api_key, account_id, site_id)
    
    # Test product data
    test_product = {
        "productName": "Biotop Altadex Ahuyentador Sol...",
        "price": "36.49€",
        "rating": 1.0,
        "isAutomated": True,
        "productUrl": "https://www.amazon.es/Biotop-Altadex-Ahuyentad-Animales-Salvajes/dp/B0977SRJ18",
        "image": "https://m.media-amazon.com/images/I/51tBAW7o-QS._AC_UF1000,1000_QL80_.jpg",
        "descriptionOfProduct": "Advanced sprinkler system with smart controls",
        "opinionDeExperto": "Este sistema de riego es altamente recomendable por su facilidad de uso y eficiencia.",
        "date": "2024-12-04",
        "categora": "Control de Animales",
        "marca": "Altadex",
        "discount": "10%",
        "previousPrice": "169.99"
    }
    
    try:
        result = client.insert_gardening_product(test_product, "GardeningAmazonProducts")
        print("Successfully inserted product:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error inserting product: {str(e)}")

# Example test code
def test_query_products(collection_id):
    api_key = os.getenv('WIX_API_KEY')
    account_id = os.getenv('WIX_ACCOUNT_ID')
    site_id = os.getenv('WIX_SITE_ID')
    
    client = WixAPIClient(api_key, account_id, site_id)
    
    try:
        # Example 1: Get all products (paginated)
        all_products = client.query_product_with_filters(
            collection_id=collection_id,
            paging={"limit": 10, "offset": 0}
        )
        print("\nAll products (first 10):")
        print(json.dumps(all_products, indent=2))
        
        # # Example 2: Filter by brand and sort by price
        # filtered_products = client.query_product_with_filters(
        #     collection_id=collection_id,
        #     filter_params={"marca": "Rainbird"},
        #     sort_params=[{"field": "price", "order": "DESC"}],
        #     paging={"limit": 5}
        # )
        # print("\nRainbird products sorted by price (descending):")
        # print(json.dumps(filtered_products, indent=2))
        
        # # Example 3: Get automated products with rating > 4
        # automated_products = client.query_product_with_filters(
        #     collection_id=collection_id,
        #     filter_params={
        #         "isAutomated": True,
        #         "rating": {"$gt": 4}
        #     }
        # )
        # print("\nAutomated products with high ratings:")
        # print(json.dumps(automated_products, indent=2))
        
    except Exception as e:
        print(f"Error querying products: {str(e)}")

def test_price_update_check():
    api_key = os.getenv('WIX_API_KEY')
    account_id = os.getenv('WIX_ACCOUNT_ID')
    site_id = os.getenv('WIX_SITE_ID')
    
    client = WixAPIClient(api_key, account_id, site_id)
    
    try:
        # Get products needing update after 1 day
        products_to_update = client.get_products_needing_price_update(days_threshold=1)
        print("\nProducts needing price update:")
        print(f"Total products to check: {products_to_update.get('pagingMetadata', {}).get('count', 0)}")
        
        # Print each product's info
        for item in products_to_update.get('dataItems', []):
            product_data = item['data']
            print(f"\nProduct ID: {item.get('id')}")
            print(f"Product: {product_data.get('productName')}")
            print(f"Current Price: {product_data.get('price')}")
            print(f"Previous Price: {product_data.get('previousPrice')}")
            print(f"Discount: {product_data.get('discount')}")
            print(f"Last Update: {product_data.get('timestampOfPriceUpdate', 'Never updated')}")
        
    except Exception as e:
        print(f"Error checking for products to update: {str(e)}")

# if __name__ == "__main__":
#     #test_query_products("Blog/Posts")
#     #test_price_update_check()

#     api_key = os.getenv('WIX_API_KEY')
#     account_id = os.getenv('WIX_ACCOUNT_ID')
#     site_id = os.getenv('WIX_SITE_ID')
    
#     client = WixAPIClient(api_key, account_id, site_id)
#     try:
#         # Get collections
#         collections = client.get_collections(collection_id="FamiliasSub-FamiliasyCategorias")
#         # Save to file
#         with open('blog_data.json', 'w', encoding='utf-8') as f:
#             json.dump(collections, f, indent=2)
    
#         print("Collections data has been saved to 'collections_data.json'")

#     except Exception as e:
#         print(f"Error: {str(e)}")

#     test_query_products(collection_id="FamiliasSub-FamiliasyCategorias")