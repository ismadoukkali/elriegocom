import requests
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from pprint import pprint

load_dotenv()
def save_html_to_file(html_content, filename="output.html"):
    try:
        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Open file in write mode with UTF-8 encoding
        with open(filename, 'w', encoding='utf-8') as file:
            # Write the prettified HTML to the file
            file.write(str(soup))
            
        print(f"HTML content successfully saved to {filename}")
        
    except Exception as e:
        print(f"An error occurred while saving the file: {str(e)}")


class SmartProxyClient:
    def __init__(self, api_key):
        self.api_key = api_key  
    
    def get_product(self, asin):
        url = "https://scraper-api.smartproxy.com/v2/scrape"

        payload = {
            "url": f"https://www.amazon.es/dp/{asin}",
        }

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Basic " + self.api_key
        }

        response = requests.post(url, json=payload, headers=headers)
        json_response = response.json()
        html_content = json_response['results'][0]['content']
        return html_content
    
    def calculate_original_price(self, current_price, savings_percentage):
        """
        Calculate the original price using current price and savings percentage.
        
        Args:
            current_price (str): Current price (e.g., '32,99€')
            savings_percentage (str): Savings percentage (e.g., '-42%')
            
        Returns:
            str: Calculated original price with same format as input
        """
        try:
            # Extract numeric values
            price_num = float(current_price.replace('€', '').replace(',', '.'))
            savings_num = abs(float(savings_percentage.replace('%', '').replace('-', '')))
            
            # Calculate original price: current_price = original_price * (1 - savings_percentage/100)
            # Therefore: original_price = current_price / (1 - savings_percentage/100)
            original_price = price_num / (1 - savings_num/100)
            
            # Format back to string with same format as input
            # Round to 2 decimal places and format with comma
            formatted_price = f"{original_price:.2f}".replace('.', ',') + '€'
            
            return formatted_price
        except Exception as e:
            print(f"Error calculating original price: {str(e)}")
            return None
    
    def parse_response(self, html_content):
        """
        Extract and format price-related elements from Amazon HTML content.
        
        Args:
            html_content (str): HTML content from Amazon product page
            
        Returns:
            dict: Dictionary containing formatted price elements
        """
        price_elements = {
            'product_price': [],
            'price_symbols': [],
            'discounts': [],
            'price_strikethrough': []
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Get current price (product_price) - checking both formats
            current_price = None
            # First format
            current_price = soup.find(class_="a-price aok-align-center")
            
            # Second format (with reinventPricePriceToPayMargin)
            if not current_price or not current_price.get_text(strip=True):
                current_price = soup.find(class_="a-price aok-align-center reinventPricePriceToPayMargin priceToPay")
            
            current_price_text = None
            if current_price:
                # Try to construct price from components if available
                whole = current_price.find(class_="a-price-whole")
                fraction = current_price.find(class_="a-price-fraction")
                symbol = current_price.find(class_="a-price-symbol")
                
                if whole and fraction and symbol:
                    whole_text = whole.get_text(strip=True).replace(',', '')
                    fraction_text = fraction.get_text(strip=True)
                    symbol_text = symbol.get_text(strip=True)
                    current_price_text = f"{whole_text},{fraction_text}{symbol_text}"
                else:
                    # Fallback to getting full text if components aren't available
                    price_text = current_price.get_text(strip=True)
                    # Remove duplicate price if it appears twice
                    if len(price_text) > 0:
                        half_length = len(price_text) // 2
                        current_price_text = price_text[:half_length] if price_text[:half_length] == price_text[half_length:] else price_text
                
                if current_price_text:
                    price_elements['product_price'] = [current_price_text]

            # Get price symbols
            symbols = soup.find_all(class_="a-price-symbol")
            price_elements['price_symbols'] = list(set(symbol.get_text(strip=True) for symbol in symbols if symbol.get_text(strip=True)))
            
            # Get savings percentage
            savings = soup.find(class_="a-size-large a-color-price savingPriceOverride aok-align-center reinventPriceSavingsPercentageMargin savingsPercentage")
            savings_text = None
            if savings:
                savings_text = savings.get_text(strip=True)
                # Remove non-breaking space and ensure proper format
                savings_text = savings_text.replace('\xa0', '')
                if not savings_text.endswith('%'):
                    savings_text += '%'
                price_elements['discounts'] = [savings_text]
                
                # Calculate strikethrough price when there's a discount
                if current_price_text:
                    calculated_price = self.calculate_original_price(current_price_text, savings_text)
                    if calculated_price:
                        price_elements['price_strikethrough'] = [calculated_price]
            
            # Remove empty lists from the dictionary
            price_elements = {k: v for k, v in price_elements.items() if v}
            
            return price_elements
        
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return None
        
    def get_product_price(self, asin):
        html = self.get_product(asin)
        response = self.parse_response(html)
        return response

# if __name__ == "__main__":
#     smart_proxy = SmartProxyClient(api_key=os.getenv('AUTH_TOKEN_SMARTPROXY'))
#     response = smart_proxy.get_product_price("B07PDS3HB4")
#     pprint(response)
    




