from src.wix_client import WixAPIClient
from src.oxylabs_client import OxylabsClient
from src.utils_markdown import MarkdownToHTML
from src.categorizer import ProductClassifier
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
from pydantic import BaseModel, Field
from enum import Enum
from typing import Type
import time
from typing import Literal
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/bestsellers_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
api_key = os.getenv('WIX_API_KEY')
account_id = os.getenv('WIX_ACCOUNT_ID')
site_id = os.getenv('WIX_SITE_ID')
client = WixAPIClient(api_key, account_id, site_id)
oxylabs = OxylabsClient(os.getenv('USER_NAME_OXYLABS'), os.getenv('PASSWORD_OXYLABS'))
openai_client = OpenAI()

def transform_wix_categories(wix_data):
    # Initialize the hierarchy dictionary
    hierarchy = {}
    
    # Process each item in the data
    for item in wix_data['dataItems']:
        data = item['data']
        
        # Get the family (main category)
        family = data['familia'][0] if 'familia' in data and data['familia'] else None
        
        # Get the subfamily (stored in subSubFamilia in Wix)
        subfamily = data['subSubFamilia'][0] if 'subSubFamilia' in data and data['subSubFamilia'] else None
        
        # Get the subsubfamily (stored in subFamilia in Wix)
        subsubfamily = data['subFamilia'][0] if 'subFamilia' in data and data['subFamilia'] else None
        
        if family and subfamily:
            # Initialize family if it doesn't exist
            if family not in hierarchy:
                hierarchy[family] = {}
                
            # Initialize subfamily if it doesn't exist
            if subfamily not in hierarchy[family]:
                hierarchy[family][subfamily] = {}
                
            # If there's a subsubfamily, add it to the structure
            if subsubfamily:
                if not hierarchy[family][subfamily]:
                    hierarchy[family][subfamily] = {}
                if subfamily not in hierarchy[family][subfamily]:
                    hierarchy[family][subfamily][subsubfamily] = [f"{subfamily} {subsubfamily}"]
    
    return hierarchy

def push_product(product, collection_id):
    """ Example of a push of a product:
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
        "previousPrice": "169.99",
        "asin": "testing"
    }"""
    
    try:
        result = client.insert_gardening_product(product, collection_id) 
        print("Successfully inserted product:")
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"Error inserting product: {str(e)}")
    

# Query product by asin
def query_specific_product_by_asin(asin, collection_id):
    try:
        product = client.query_product_by_asin(
            collection_id=collection_id,
            asin=asin
        )
        response = json.dumps(product, indent=2)
        print(f"\nProduct with ASIN {asin}:")
        print(json.dumps(product, indent=2))
        return response

        
    except Exception as e:
        print(f"Error querying product: {str(e)}")

def parse_product_data(product_data):
    try:
        if isinstance(product_data, str):
            product_data = json.loads(product_data)
            
        content = product_data['results'][0]['content']
        main_data = parse_main_data(content)
        additional_data = parse_description_and_reviews(content)
        return main_data, additional_data
    except Exception as e:
        print(f"Error parsing product data: {str(e)}")
       

def parse_main_data(content):
    local_tz = pytz.timezone('Europe/Madrid')  # or 'Europe/Paris', depending on your location
    today = datetime.now(local_tz)

    # Two options:

    # Option 1: Store in UTC (recommended)
    utc_time = today.astimezone(pytz.UTC)
    iso_datetime = utc_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    # Option 2: Store with timezone information
    iso_datetime = today.isoformat()

    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    
    discount = ""
    previous_price = ""
    current_price = float(content.get('price', 0))
    
    if 'discount_percentage' in content and content['discount_percentage']:
        discount = f"-{content['discount_percentage']}%"
        if 'price_strikethrough' in content and content['price_strikethrough']:
            previous_price = f"{content['price_strikethrough']:.2f}€"
    
    return {
        "asin": content.get('asin', ''),
        "productUrl": f"https://www.amazon.es/dp/{content.get('asin', '')}?tag=elriego-21&linkCode=ogi&th=1&psc=1",
        "marca": content.get('brand', ''),
        "discount": discount,
        "previousPrice": previous_price,
        "price": f"{current_price:.2f}€",
        "price1": current_price,
        "rating": float(content.get('rating', 0)),
        "rating1": float(content.get('reviews_count', 0)),
        "isAutomated": True,
        "image": content.get('images', [''])[0],
        "previewName": content.get('title', '')[:39] + ('...' if len(content.get('title', '')) > 39 else ''),
        "descriptionOfProduct": "",
        "date": date_str,
        "odeinfoproducto": "",
        "odepros": "",
        "oderecomendacion": "",
        "odecontras": "",
        "categoria": "",
        "subFamilia": "",
        "subSubFamilia": "",
        "seofamilia": "",
        "seosubfamilia": "",
        "seosubsubfamilia": "",
        "timestampOfPriceUpdate": {
            "$date": iso_datetime
        },
        "productName": content.get('title', '')
    }

def parse_description_and_reviews(content):
    description = [content.get('bullet_points', ''), content.get('description', '')]
    description = ' '.join(filter(None, description))
    
    reviews = content.get('reviews', [])
    sorted_reviews = sorted(reviews, 
                          key=lambda x: x.get('helpful_count', 0) if x.get('helpful_count') is not None else -1, 
                          reverse=True)
    top_reviews = sorted_reviews[:3]
    
    formatted_reviews = []
    for review in top_reviews:
        formatted_reviews.append({
            'rating': review.get('rating', 0),
            'title': review.get('title', ''),
            'content': review.get('content', '').replace('Leer más', '').strip(),
            'author': review.get('author', ''),
            'helpful_count': review.get('helpful_count', 0),
            'date': review.get('timestamp', '')
        })
    
    return {
        'description': description,
        'top_reviews': formatted_reviews
    }

# Retrieve from Oxylabs
def retrieve_product_data(asin):
    # Scrape product data from Oxylabs
    product_data = oxylabs.oxylabs_retrieve_product_data(asin)

    # Parse product data from Oxylabs
    print(f"Parsed data for product with ASIN: {asin}")
    main_data, additional_data = parse_product_data(product_data)
    parsed_data = {
        'main_data': main_data,
        'additional_data': additional_data
    }
    pprint(main_data)
    return parsed_data


# Old Opinión de experto using OpenAI
def generate_response_gpt(prompt, model):
    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": str(prompt)}
        ],
        max_tokens=2000
    )
    
    # Extract the response content
    selection = response.choices[0].message.content
    
    # Extract token usage
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    total_tokens = response.usage.total_tokens
    
    # Display token usage
    # print(f"Input tokens (prompt): {prompt_tokens}")
    # print(f"Output tokens (completion): {completion_tokens}")
    # print(f"Total tokens used: {total_tokens}")
    
    return selection

class ProductFamilyCategorization(BaseModel):
    info_about_product: str = Field(..., description="Información del producto en markdown. No pongas 'Informacion de producto' en el titulo, solo las 3 frases.")
    pros: str = Field(..., description=f"Pros del producto en bulletpoints y markdown. No pongas 'pros' en el titulo, solo los 4 bulletpoints")
    contras: str = Field(..., description=f"""Contras del product en bulletpoints and markdown. No pongas 'contras' en el titulo, solo los 4 bulletpoints.""")
    conclusion: str = Field(..., description=f"""Conclusiones y recomendacion final sobre el producto en markdown. No pongas 'Conclusion' en el titulo, solo las 3 frases.""")

def completions_with_structured_output(prompt: str, structure: object ) -> str:

    completion = openai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Eres un asistente experto en analizar productos de riego en distintas categorías"},
            {"role": "user", "content": prompt},
        ],
        response_format=structure,
    )

    event = completion.choices[0].message.parsed

    return event
  
def generate_opinion_de_experto_old(product_data):
    product_title = product_data['main_data']['productName']
    product_description = product_data['additional_data']['description']
    product_reviews = product_data['additional_data']['top_reviews']
    prompt = f""" 

Eres un experto profesional en productos de riego con más de 10 años de experiencia evaluando y recomendando productos.

INPUT REQUERIDO:
- Nombre del producto: {str(product_title)}
- Principales reseñas/comentarios de usuarios: {str(product_reviews)}
- Descripcion del producto: {str(product_description)}

Genera una "Opinión de Experto" para una página de afiliados que:
1. Demuestre autoridad y experiencia en el campo.
2. Evalúe objetivamente los pros y contras del producto.
3. Nombra el producto con un nombre abreviado y coloquial, para que todo el mundo lo entienda.
3. Respalde las afirmaciones con evidencia de reseñas reales, no menciones ninguno de las afirmaciones directamente, posiciónalo como lo que la gente dice en general.
4. Mantenga un tono cercano y critico sobretodo tienes que inspirar confianza al lector. Puedes introducir algo de gracia tambien. Escribelo en Español de España.
5. Incluya una recomendación final clara.
6. Cada seccion tiene que tener el spacing adequado para que se vea bien, asegurarte de ello. Usa triple espaciado para absolutamente todos los cambio de parrafos.

La opinión debe estructurarse en distintos parrafos con bulletpoints:
- Información del producto
- Pros
- Contras

Evita:
- Lenguaje excesivamente promocional
- Incluir un titulo como "Opinión de experto"
- Presentarte como profesional, ve directo al grano y no hagas referencias a otros expertos
- Afirmaciones sin respaldo
- Críticas destructivas

Da tu opinion de experto en formato Markdown. Pon todos los titulos en 'bold' y pon los titulos de secciones en 'italics'. Añade también en bold en las secciones más importantes y usa bulletpoints para describir tus puntos. 

Aquí un ejemplo de como deberias realizar el output:

''Este temporizador de rociadores es una herramienta valiosa para jardineros, propietarios de hogares y entusiastas de la jardinería que buscan un control preciso y eficiente de sus sistemas de riego.

**Información del producto**
...

**Pros**

* Permite configurar la hora de inicio, duración y frecuencia del riego, ajustándose de forma precisa a las necesidades específicas de cada planta.
* La duración del riego es altamente flexible, con opciones desde 1 minuto hasta casi 4 horas......''

**Contras**
...
"""

    opinion_de_experto_markdown = generate_response_gpt(prompt, "gpt-4o")
    opinion_de_experto = MarkdownToHTML.custom_markdown_to_html(opinion_de_experto_markdown)
    return opinion_de_experto

def generate_opinion_de_experto(product_data):
    product_title = product_data['main_data']['productName']
    product_description = product_data['additional_data']['description']
    product_reviews = product_data['additional_data']['top_reviews']
    prompt = f""" 

Eres un experto profesional en productos de riego con más de 10 años de experiencia evaluando y recomendando productos.

INPUT REQUERIDO:
- Nombre del producto: {str(product_title)}
- Principales reseñas/comentarios de usuarios: {str(product_reviews)}
- Descripcion del producto: {str(product_description)}

Genera una "Opinión de Experto" para una página de afiliados que:
1. Demuestre autoridad y experiencia en el campo.
2. Evalúe objetivamente los pros y contras del producto.
3. Nombra el producto con un nombre abreviado y coloquial, para que todo el mundo lo entienda.
3. Respalde las afirmaciones con evidencia de reseñas reales, no menciones ninguno de las afirmaciones directamente, posiciónalo como lo que la gente dice en general.
4. Mantenga un tono cercano y critico sobretodo tienes que inspirar confianza al lector. Puedes introducir algo de gracia tambien. Escribelo en Español de España.
5. Incluya una recomendación final clara.
6. Cada seccion tiene que tener el spacing adequado para que se vea bien, asegurarte de ello. Usa triple espaciado para absolutamente todos los cambio de parrafos.

La opinión debe estructurarse en distintos parrafos con bulletpoints:
- Información del producto
- Pros
- Contras

Evita:
- Lenguaje excesivamente promocional
- Incluir un titulo como "Opinión de experto"
- Presentarte como profesional, ve directo al grano y no hagas referencias a otros expertos
- Afirmaciones sin respaldo
- Críticas destructivas

Da tu opinion de experto en formato Markdown. Pon todos los titulos en 'bold' y pon los titulos de secciones en 'italics'. Añade también en bold en las secciones más importantes y usa bulletpoints para describir tus puntos. 

Aquí un ejemplo de como deberias realizar el output:

''Este temporizador de rociadores es una herramienta valiosa para jardineros, propietarios de hogares y entusiastas de la jardinería que buscan un control preciso y eficiente de sus sistemas de riego.

**Información del producto**
...

**Pros**

* Permite configurar la hora de inicio, duración y frecuencia del riego, ajustándose de forma precisa a las necesidades específicas de cada planta.
* La duración del riego es altamente flexible, con opciones desde 1 minuto hasta casi 4 horas......''

**Contras**
...
"""

    opinion_de_experto_markdown = completions_with_structured_output(prompt=prompt, structure=ProductFamilyCategorization)
    opinion_de_experto = {
        "info_about_product": MarkdownToHTML.custom_markdown_to_html(opinion_de_experto_markdown.info_about_product),
        "pros": MarkdownToHTML.custom_markdown_to_html(opinion_de_experto_markdown.pros),
        "contras": MarkdownToHTML.custom_markdown_to_html(opinion_de_experto_markdown.contras),
        "conclusion": MarkdownToHTML.custom_markdown_to_html(opinion_de_experto_markdown.conclusion)
    }
    
    return opinion_de_experto

# Description using OpenAI
def generate_description(product_data):
    product_title = product_data['main_data']['productName']
    product_description = product_data['additional_data']['description']
    prompt = f"""
    Formatea la siguiente información de proudcto en 3 simples bulletpoints en formato markdown. Sin headings ni nada, solo los bulletpoints.
    
    Aquí la información de producto:
    - Nombre del producto: {str(product_title)}
    - Descripcion del producto: {str(product_description)}
    """

    description_markdown = generate_response_gpt(prompt, "gpt-4o")
    description = MarkdownToHTML.custom_markdown_to_html(description_markdown)
    return description

def categorize_product_old(product_data):
    product_title = product_data['main_data']['productName']
    product_description = product_data['additional_data']['description']
    prompt = f"""
    Clasifica el siguiente producto en una de estas categorias:
    - Pistolas de Riego
    - Programadores de grifo
    - Electroválvulas
    - Difusores
    - Turbinas
    - Varios

    Solo responde con el nombre de la categoría.

    Aquí la información de producto:
    - Nombre del producto: {str(product_title)}
    - Descripcion del producto: {str(product_description)}
    """
    category = generate_response_gpt(prompt, "gpt-4o-mini")
    return str(category)

def categorize_product(product_data):
    product_title = product_data['main_data']['productName']
    product_description = product_data['additional_data']['description']
    client_wix = WixAPIClient(api_key, account_id, site_id)
    wix_data = WixAPIClient.query_product_with_filters(client_wix, collection_id="FamiliasSub-FamiliasyCategorias")
    hierarchy = transform_wix_categories(wix_data)
    classifier = ProductClassifier(hierarchy)
    categorizations = classifier.main(f"Title of product: {product_title}, Description of product: {product_description}")
    return categorizations

# Put into reference of highlighted products
def put_product_in_reference(product_title, 
                             product_id, 
                             categorizations, 
                             best_seller_boolean):
    json_to_push = {
        "title": product_title,
        "reference": product_id,
        "familia": categorizations["family"],
        "subFamilia": categorizations["subfamily"],
        "subSubFamilia": categorizations["subsubfamily"],
        "bestSeller": best_seller_boolean,
    }
    response_from_psuh = push_product(json_to_push, "Productosrelacionados-elriegocom")
    return response_from_psuh

# Return array of best sellers by category
def get_bestsellers_by_category(category_id):
    response = oxylabs.oxylabs_retrieve_bestsellers(category_id)

    try:
        # Navigate to the results array containing the products
        products = response["results"][0]["content"]["results"]
        
        # Extract ASINs using list comprehension
        asins = [product["asin"] for product in products]
        
        return asins
        
    except (KeyError, IndexError) as e:
        print(f"Error processing data: {e}")
        return []


class ElRiegoCOMClient:
    @staticmethod
    def get_bestsellers_by_category(category_id):
        response = oxylabs.oxylabs_retrieve_bestsellers(category_id)

        try:
            # Navigate to the results array containing the products
            products = response["results"][0]["content"]["results"]
            
            # Extract ASINs using list comprehension
            asins = [product["asin"] for product in products]
            
            return asins
            
        except (KeyError, IndexError) as e:
            print(f"Error processing data: {e}")
            return []
        

    @staticmethod
    def push_product_to_cms(asin, is_best_seller=False):
        try:
            logger.info(f"Starting process for ASIN: {asin}")
            
            # Check if product exists
            query_by_asin = client.query_product_by_asin("GardeningAmazonProducts", asin)

            if query_by_asin.get('dataItems', []):
                logger.info(f"Product with ASIN {asin} already exists in CMS.")
                return {"success": True, "message": "Product already exists", "asin": asin}
            
            logger.info(f"Product with ASIN {asin} does not exist, proceeding with import.")
            
            # Retrieve product data
            product_data = retrieve_product_data(asin)
            if not product_data:
                raise Exception(f"Failed to retrieve product data for ASIN {asin}")

            # OpenAI generations
            opinion_de_experto = generate_opinion_de_experto(product_data)
            description = generate_description(product_data)
            category = categorize_product(product_data)

            # Full push to CMS - All products
            product_data['main_data'].update({
                "descriptionOfProduct": description,
                "isbestseller": is_best_seller,
                "odeinfoproducto": opinion_de_experto["info_about_product"],
                "odepros": opinion_de_experto["pros"],
                "oderecomendacion": opinion_de_experto["conclusion"],
                "odecontras": opinion_de_experto["contras"],
                "categoria": [category["family"]],
                "subFamilia": [category["subfamily"]],
                "subSubFamilia": [category["subsubfamily"]],
                "seofamilia": category["family"],
                "seosubfamilia": category["subfamily"],
                "seosubsubfamilia": category["subsubfamily"],
            })

            response_from_push = push_product(product_data['main_data'], "GardeningAmazonProducts")
            product_pushed_id = response_from_push["dataItem"]["id"]
            logger.info(f"Product pushed successfully with ID: {product_pushed_id}")

            # Full push to CMS - Highlighted products
            response_from_reference = put_product_in_reference(
                product_data['main_data']['productName'], 
                product_pushed_id, 
                category, 
                is_best_seller
            )
            product_referenced_id = response_from_reference["dataItem"]["id"]
            logger.info(f"Product added to reference with ID: {product_referenced_id}")

            return {
                "success": True,
                "message": "Product successfully imported",
                "asin": asin,
                "product_id": product_pushed_id,
                "reference_id": product_referenced_id,
                "response_from_push": response_from_push,
                "response_from_reference": response_from_reference
            }

        except Exception as e:
            logger.error(f"Error processing ASIN {asin}: {str(e)}")
            return {
                "success": False,
                "message": str(e),
                "asin": asin
            }

    @staticmethod
    async def push_all_bestsellers_to_cms(category_id, max_workers=5, number_of_products=10, progress_callback=None):
        """
        Pushes bestseller products to CMS with concurrent processing and progress tracking.
        """
        try:
            bestsellers = get_bestsellers_by_category(category_id)
            bestsellers = bestsellers[:number_of_products]
            
            if not bestsellers:
                raise Exception(f"No bestsellers found for category {category_id}")
                
            
            # Results tracking
            results = {
                "success": [],
                "failure": [],
                "total": len(bestsellers)
            }

            # Create a partial function with the is_best_seller flag set
            push_func = partial(ElRiegoCOMClient.push_product_to_cms, is_best_seller=True)
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                loop = asyncio.get_running_loop()
                futures = []
                
                for asin in bestsellers:
                    task = loop.run_in_executor(executor, push_func, asin)
                    futures.append(task)
                
                # Process results as they complete
                for completed_task in asyncio.as_completed(futures):
                    try:
                        result = await completed_task
                        
                        # Store result
                        if result["success"]:
                            results["success"].append(result)
                        else:
                            results["failure"].append(result)
                        
                        # Call progress callback if provided
                        if progress_callback:
                            progress_callback(result)
                            
                    except Exception as e:
                        if progress_callback:
                            progress_callback({
                                "success": False,
                                "asin": "unknown",
                                "message": f"Error: {str(e)}"
                            })
            
            return results

        except Exception as e:
            logger.error(f"Critical error in push_all_bestsellers_to_cms: {str(e)}")
            raise
        
    @staticmethod
    def push_all_bestsellers_to_cms_sync(category_id, max_workers=5, number_of_products=10, progress_callback=None):
        """
        Synchronous wrapper for the async function.
        """
        try:
            results = asyncio.run(ElRiegoCOMClient.push_all_bestsellers_to_cms(
                category_id=category_id,
                max_workers=max_workers,
                number_of_products=number_of_products,
                progress_callback=progress_callback
            ))
            
            return results

        except Exception as e:
            print(f"Error in sync wrapper: {str(e)}")
            raise

# # Main script
if __name__ == "__main__":
    # Push all best sellers to CMS
    # try:
    #     ElRiegoCOMClient.push_all_bestsellers_to_cms_sync(
    #         category_id="5940500031",
    #         number_of_products=50
    #     )
    # except Exception as e:
    #     logger.error(f"Main script error: {str(e)}")

    # Push single product to CMS
    try:
        ElRiegoCOMClient.push_product_to_cms(
            asin="B09HH753HW",
            is_best_seller=False
        )
    except Exception as e:
        logger.error(f"Main script error: {str(e)}")
        
