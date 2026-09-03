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
        try:
            json_response = response.json()
        except ValueError as e:
            raise RuntimeError(
                f"Smartproxy returned non-JSON (HTTP {response.status_code}): {(response.text or '')[:300]}"
            ) from e

        if response.status_code >= 400 or 'results' not in json_response:
            raise RuntimeError(
                f"Smartproxy scrape failed (HTTP {response.status_code}): "
                f"{json_response.get('message') or json_response.get('error') or json_response}"
            )

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
        import re

        price_elements = {
            'product_price': [],
            'price_symbols': [],
            'discounts': [],
            'price_strikethrough': []
        }

        def normalize_euro_price(text):
            if not text:
                return None
            text = text.replace('\xa0', '').replace(' ', '').strip()
            # Keep values like 26,70€ / 26.70€
            match = re.search(r'(\d+[.,]\d{2})\s*€', text)
            if match:
                amount = match.group(1).replace('.', ',')
                return f"{amount}€"
            # Recover glued values like 2670€ -> 26,70€ when clearly cents
            match = re.search(r'(\d+)€', text)
            if match and len(match.group(1)) >= 3:
                digits = match.group(1)
                amount = f"{digits[:-2]},{digits[-2:]}"
                return f"{amount}€"
            return None
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            current_price_text = None

            # Prefer main buybox / core price offscreen text
            for css in [
                '#corePrice_feature_div span.a-price span.a-offscreen',
                '#corePriceDisplay_desktop_feature_div span.a-price span.a-offscreen',
                '.a-price.priceToPay span.a-offscreen',
                'span.a-price.aok-align-center span.a-offscreen',
                'span.a-price span.a-offscreen',
            ]:
                el = soup.select_one(css)
                current_price_text = normalize_euro_price(el.get_text(strip=True) if el else None)
                if current_price_text:
                    break

            # Fallback: build from whole/fraction in the main price block
            if not current_price_text:
                current_price = (
                    soup.select_one('#corePrice_feature_div .a-price')
                    or soup.select_one('.a-price.priceToPay')
                    or soup.find(class_="a-price aok-align-center reinventPricePriceToPayMargin priceToPay")
                    or soup.find(class_="a-price aok-align-center")
                )
                if current_price:
                    whole = current_price.find(class_="a-price-whole")
                    fraction = current_price.find(class_="a-price-fraction")
                    symbol = current_price.find(class_="a-price-symbol")
                    if whole and fraction:
                        whole_text = re.sub(r'[^\d]', '', whole.get_text(strip=True))
                        fraction_text = re.sub(r'[^\d]', '', fraction.get_text(strip=True))
                        symbol_text = (symbol.get_text(strip=True) if symbol else '€') or '€'
                        if whole_text and fraction_text:
                            current_price_text = normalize_euro_price(
                                f"{whole_text},{fraction_text}{symbol_text}"
                            )
                
            if current_price_text:
                price_elements['product_price'] = [current_price_text]

            # Get price symbols
            symbols = soup.find_all(class_="a-price-symbol")
            price_elements['price_symbols'] = list(set(symbol.get_text(strip=True) for symbol in symbols if symbol.get_text(strip=True)))
            
            # Get savings percentage
            savings = soup.find(class_="a-size-large a-color-price savingPriceOverride aok-align-center reinventPriceSavingsPercentageMargin savingsPercentage")
            if not savings:
                savings = soup.select_one('.savingsPercentage, span.savingPriceOverride')
            savings_text = None
            if savings:
                savings_text = savings.get_text(strip=True)
                # Remove non-breaking space and ensure proper format
                savings_text = savings_text.replace('\xa0', '')
                if savings_text and not savings_text.endswith('%'):
                    savings_text += '%'
                if savings_text:
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
    




