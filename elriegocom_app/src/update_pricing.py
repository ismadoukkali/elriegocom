from src.wix_client import WixAPIClient
from src.smartproxy_client import SmartProxyClient
from utils_markdown import MarkdownToHTML
import os
import json
import requests
from pprint import pprint
from datetime import datetime
from openai import OpenAI
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import logging
import sys
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial


# Initialize logging
def setup_logging():
    """Configure logging with both file and console handlers."""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Create a timestamp for the log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'logs/price_updates_{timestamp}.log'
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

# Initialize global logger
logger = setup_logging()

api_key = os.getenv('WIX_API_KEY')
account_id = os.getenv('WIX_ACCOUNT_ID')
site_id = os.getenv('WIX_SITE_ID')
smart_proxy = SmartProxyClient(api_key=os.getenv('AUTH_TOKEN_SMARTPROXY'))
wix_client = WixAPIClient(api_key, account_id, site_id)

def normalize_price(price_str):
    """
    Normalizes price string to a float value by removing currency symbols and converting commas to dots.
    
    Args:
        price_str (str): Price string (e.g., "11,68€" or "14.99€")
    
    Returns:
        float: Normalized price value
        
    Raises:
        ValueError: If price string cannot be converted to float
    """
    try:
        # Remove currency symbols and whitespace
        cleaned = price_str.replace('€', '').replace('$', '').strip()
        # Convert comma to dot for decimal point
        cleaned = cleaned.replace(',', '.')
        return float(cleaned)
    except ValueError as e:
        logger.error(f"Failed to normalize price string '{price_str}': {str(e)}")
        raise ValueError(f"Invalid price format: {price_str}") from e

def format_price(price_float):
    """
    Formats a float price value to the standard format with euro symbol.
    
    Args:
        price_float (float): Price value
    
    Returns:
        str: Formatted price string (e.g., "11.68€")
        
    Raises:
        ValueError: If price_float is not a valid number
    """
    try:
        return f"{float(price_float):.2f}€"
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to format price value '{price_float}': {str(e)}")
        raise ValueError(f"Invalid price value: {price_float}") from e

class ElRiegoCOMClient:
    @staticmethod
    def validate_product_data(product):
        """
        Validates that the product data contains all required fields.
        
        Args:
            product (dict): Product information from Wix
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ['id', 'data']
        required_data_fields = ['asin', 'price']
        
        if not all(field in product for field in required_fields):
            missing = [f for f in required_fields if f not in product]
            raise ValueError(f"Missing required fields in product: {missing}")
            
        if not all(field in product['data'] for field in required_data_fields):
            missing = [f for f in required_data_fields if f not in product['data']]
            raise ValueError(f"Missing required fields in product data: {missing}")

    @staticmethod
    def check_and_update_product_price(product, smart_proxy, wix_client):
        """
        Checks if a product's price has changed on Amazon and updates it in Wix if necessary.
        
        Args:
            product (dict): Product information from Wix
            smart_proxy (SmartProxyClient): Initialized smart proxy client
            wix_client (WixAPIClient): Initialized Wix API client
        
        Returns:
            dict: Result of the operation with status and details
        """
        try:
            # Validate product data
            ElRiegoCOMClient.validate_product_data(product)
            
            # Extract product information
            product_id = product['id']
            asin = product['data']['asin']
            
            logger.info(f"Processing product ASIN: {asin}")
            
            try:
                current_price = normalize_price(product['data']['price'])
            except ValueError as e:
                logger.error(f"Invalid current price format for ASIN {asin}: {str(e)}")
                raise
            
            # Get latest price from Amazon
            try:
                amazon_data = smart_proxy.get_product_price(asin)
            except Exception as e:
                logger.error(f"Failed to fetch Amazon price for ASIN {asin}: {str(e)}")
                raise RuntimeError(f"Amazon price fetch failed: {str(e)}") from e
            
            if not amazon_data or 'product_price' not in amazon_data or not amazon_data['product_price']:
                logger.error(f"Invalid or empty Amazon data for ASIN {asin}")
                return {
                    'status': 'error',
                    'message': f'Failed to fetch Amazon price for ASIN {asin}',
                    'asin': asin
                }
            
            # Get the new price from Amazon
            try:
                new_price = normalize_price(amazon_data['product_price'][0])
            except ValueError as e:
                logger.error(f"Invalid Amazon price format for ASIN {asin}: {str(e)}")
                raise
            
            # If prices are the same, no update needed
            if abs(current_price - new_price) < 0.01:
                logger.info(f"No price update needed for ASIN {asin}")
                try:
                    updated_product = wix_client.update_product(
                    product_id=product_id,
                    old_product_data=product['data'],
                    new_price=format_price(current_price),
                    new_price_float=current_price,
                    new_previous_price=None,
                    new_discount=None
                )
                except Exception as e:
                    logger.error(f"Failed to update Wix product for ASIN {asin}: {str(e)}")
                    raise RuntimeError(f"Wix update failed: {str(e)}") from e
                
                logger.info(f"Successfully updated pricing check date for ASIN {asin}")
                return {
                    'status': 'skipped',
                    'message': f'No price update needed for ASIN {asin}',
                    'asin': asin,
                    'current_price': format_price(current_price),
                    'new_price': format_price(new_price)
                }
            
            # Format the new price
            formatted_new_price = format_price(new_price)
            logger.info(f"Price change detected for ASIN {asin}: {format_price(current_price)} -> {formatted_new_price}")
            
            # Handle cases where there's no strikethrough price or discount
            new_previous_price = ''
            new_discount = ''
            
            # Only set these values if they exist in the Amazon data
            if ('price_strikethrough' in amazon_data and 
                amazon_data['price_strikethrough'] and 
                len(amazon_data['price_strikethrough']) > 0):
                new_previous_price = amazon_data['price_strikethrough'][0]
                
            if ('discounts' in amazon_data and 
                amazon_data['discounts'] and 
                len(amazon_data['discounts']) > 0):
                new_discount = amazon_data['discounts'][0]
            
            # Update the product in Wix
            try:
                updated_product = wix_client.update_product(
                    product_id=product_id,
                    old_product_data=product['data'],
                    new_price=formatted_new_price,
                    new_price_float=current_price,
                    new_previous_price=new_previous_price,
                    new_discount=new_discount
                )
            except Exception as e:
                logger.error(f"Failed to update Wix product for ASIN {asin}: {str(e)}")
                raise RuntimeError(f"Wix update failed: {str(e)}") from e
            
            logger.info(f"Successfully updated product ASIN {asin}")
            return {
                'status': 'updated',
                'message': f'Successfully updated price for ASIN {asin}',
                'asin': asin,
                'old_price': format_price(current_price),
                'new_price': formatted_new_price,
                'new_previous_price': new_previous_price,
                'new_discount': new_discount,
                'updated_product': updated_product
            }
            
        except Exception as e:
            asin = product.get('data', {}).get('asin', 'unknown')
            logger.error(f"Error processing ASIN {asin}: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Error processing ASIN {asin}: {str(e)}',
                'asin': asin,
                'error': str(e)
            }

    @staticmethod
    def update_all_products(products, smart_proxy, wix_client, max_workers=10):
        """
        Updates prices for all products that need checking using parallel processing.
        
        Args:
            products (list): List of products to check
            smart_proxy (SmartProxyClient): Initialized smart proxy client
            wix_client (WixAPIClient): Initialized Wix API client
            max_workers (int): Maximum number of concurrent threads to use
        
        Returns:
            dict: Summary of the update operation
        """
        if not products:
            logger.warning("No products provided for update")
            return {'updated': [], 'skipped': [], 'errors': []}
        
        logger.info(f"Starting parallel price updates for {len(products)} products with {max_workers} workers")
        results = {
            'updated': [],
            'skipped': [],
            'errors': []
        }
        
        # Create a partial function with the fixed arguments
        process_product = partial(
            ElRiegoCOMClient.check_and_update_product_price,
            smart_proxy=smart_proxy,
            wix_client=wix_client
        )
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks and get futures
            future_to_product = {
                executor.submit(process_product, product): product
                for product in products
            }
            
            # Process completed tasks with progress bar
            for future in tqdm(
                as_completed(future_to_product),
                total=len(products),
                desc="Updating products"
            ):
                try:
                    result = future.result()
                    if result['status'] == 'updated':
                        results['updated'].append(result)
                    elif result['status'] == 'skipped':
                        results['skipped'].append(result)
                    else:
                        results['errors'].append(result)
                except Exception as e:
                    product = future_to_product[future]
                    asin = product.get('data', {}).get('asin', 'unknown')
                    error_result = {
                        'status': 'error',
                        'message': f'Thread execution failed for ASIN {asin}: {str(e)}',
                        'asin': asin,
                        'error': str(e)
                    }
                    results['errors'].append(error_result)
                    logger.error(f"Thread execution failed for ASIN {asin}: {str(e)}", exc_info=True)
        
        # Log summary
        logger.info(f"Parallel update complete. Updated: {len(results['updated'])}, "
                f"Skipped: {len(results['skipped'])}, "
                f"Errors: {len(results['errors'])}")
        
        return results
    
# if __name__ == "__main__":

#     try:
#         products_to_update = wix_client.get_products_needing_price_update()['dataItems']
#         results = ElRiegoCOMClient.update_all_products(products_to_update, smart_proxy, wix_client)
        
#         # Print summary
#         print(f"\nUpdate Summary:")
#         print(f"Updated: {len(results['updated'])} products")
#         print(f"Skipped: {len(results['skipped'])} products")
#         print(f"Errors: {len(results['errors'])} products")
        
#         # If there were errors, print them
#         if results['errors']:
#             print("\nErrors encountered:")
#             for error in results['errors']:
#                 print(f"ASIN {error['asin']}: {error['message']}")
            
#     except Exception as e:
#         logger.error(f"Fatal error in price update process: {str(e)}", exc_info=True)
#         raise