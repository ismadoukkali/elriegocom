from src.wix_client import WixAPIClient
from src.oxylabs_client import OxylabsClient
from datetime import datetime
from pprint import pprint
import os
import json
from pydantic import BaseModel, Field
from openai import OpenAI
import uuid

api_key = os.getenv('WIX_API_KEY')
account_id = os.getenv('WIX_ACCOUNT_ID')
site_id = os.getenv('WIX_SITE_ID')

client = WixAPIClient(api_key, account_id, site_id)
oxylabs = OxylabsClient(os.getenv('USER_NAME_OXYLABS'), os.getenv('PASSWORD_OXYLABS'))

products_data = []
client_openai = OpenAI()


# Define the HTML content as a variable

def get_product_display_html(product_title, 
                             brand,
                             product_price,
                             product_image, 
                             product_bulletpoints, 
                             product_description, 
                             product_url):

    product_html = f"""<div style="font-family: Arial, sans-serif; max-width: 800px; padding: 20px; border: 1px solid #e0e0e0; border-radius: 20px; background-color: white; margin: 2rem auto;">
    <!-- Main product container -->
    <div style="
        display: flex;
        flex-direction: column;
        gap: 20px;
    ">
        <!-- Product header section -->
        <div style="
        display: flex;
        gap: 20px;
        @media (max-width: 600px) {{
            flex-direction: column;
            align-items: center;
        }}
        ">
        <!-- Image container -->
        <div style="
            width: 150px;
            aspect-ratio: 1;
            position: relative;
            flex-shrink: 0;
            @media (max-width: 600px) {{
            width: 200px;
            order: -1;
            margin-bottom: 10px;
            }}
        ">
            <img src={product_image}
                alt={product_title}
                style="
                position: absolute;
                width: 100%;
                height: 100%;
                object-fit: contain;
                "
            />
        </div>

        <!-- Product info container -->
        <div style="flex: 1;">
            <h2 style="
            margin: 0 0 15px 0;
            color: #31572c;
            font-size: 20px;
            @media (max-width: 600px) {{
                text-align: center;
                font-size: 18px;
            }}
            ">
            <a href={product_url} target="_blank" rel="noopener noreferrer" style="color: inherit; text-decoration: none;">
                {product_title}
            </a>
            </h2>

            <ul style="
            margin: 0 0 20px 0;
            padding-left: 20px;
            color: #333;
            @media (max-width: 600px) {{
                padding-left: 16px;
                padding-right: 16px;
                margin-bottom: 15px;
            }}
            ">
            <li style="margin-bottom: 8px;">{product_bulletpoints[0]}</li>
            <li style="margin-bottom: 8px;">{product_bulletpoints[1]}</li>
            <li style="margin-bottom: 8px;">{product_bulletpoints[2]}</li>
            </ul>

            <!-- Price and CTA section -->
            <div style="
            display: flex;
            align-items: center;
            gap: 15px;
            @media (max-width: 600px) {{
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }}
            ">
            <span style="
                font-size: 24px;
                font-weight: bold;
                color: #333;
                @media (max-width: 600px) {{
                font-size: 22px;
                }}
            ">{product_price}</span>
            <a href="{product_url}" target="_blank" rel="noopener noreferrer" style="
                background: #FFD814;
                color: black;
                text-decoration: none;
                padding: 8px 15px;
                border-radius: 8px;
                font-size: 14px;
                white-space: nowrap;
                @media (max-width: 600px) {{
                width: 100%;
                text-align: center;
                }}
            ">Ver Opiniones <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Amazon_icon.svg/1200px-Amazon_icon.svg.png" 
                alt="Amazon icon" 
                style="width: 15px; height: 15px; object-fit: center;"> </a>
            </div>
        </div>
        </div>

        <!-- Description -->
        <p style="
        color: #333;
        line-height: 1.5;
        margin: 0;
        @media (max-width: 600px) {{
            font-size: 14px;
        }}
        ">
        {product_description}
        </p>

        <!-- Bottom CTA -->
        <div style="text-align: center; margin-top: 20px;">
        <a href={product_url} target="_blank" rel="noopener noreferrer" style="
            background: #31572c;
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            display: inline-block;
            width: auto;
            @media (max-width: 600px) {{
            width: 100%;
            box-sizing: border-box;
            }}
        ">{brand} - Ver opiniones
        </a>
        </div>
    </div>
    </div>"""

    return product_html

def get_product_ventajas_html(ventajas_title,
                              ventajas_title_and_description,
                              product_url):

    product_html = f"""
    <div style="max-width: 1200px; margin: 2rem auto; padding: 1.5rem; font-family: Arial, sans-serif; background-color: white; border: 1px solid #e0e0e0; border-radius: 20px;">
    <h2 style="color: #31572c; font-size: 1.5rem; margin-bottom: 2rem; font-weight: bold;">{ventajas_title}</h2>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
        <div style="display: flex; flex-direction: column; gap: 0.5rem; background-color: #f9f9f9; padding: 1rem; border-radius: 20px;">
            <h3 style="display: flex; align-items: center; gap: 0.5rem; font-weight: bold; color: #333; font-size: 1.1rem;">
                <span style="color: #0066CC; margin-right: 8px;">•</span>
                {ventajas_title_and_description[0][0]}
            </h3>
            <p style="color: #444; line-height: 1.4; margin: 0;">{ventajas_title_and_description[0][1]}</p>
        </div>

        <div style="display: flex; flex-direction: column; gap: 0.5rem; background-color: #f9f9f9; padding: 1rem; border-radius: 20px;">
            <h3 style="display: flex; align-items: center; gap: 0.5rem; font-weight: bold; color: #333; font-size: 1.1rem;">
                <span style="color: #0066CC; margin-right: 8px;">•</span>
                {ventajas_title_and_description[1][0]}
            </h3>
            <p style="color: #444; line-height: 1.4; margin: 0;">{ventajas_title_and_description[1][1]}</p>
        </div>

        <div style="display: flex; flex-direction: column; gap: 0.5rem; background-color: #f9f9f9; padding: 1rem; border-radius: 20px;">
            <h3 style="display: flex; align-items: center; gap: 0.5rem; font-weight: bold; color: #333; font-size: 1.1rem;">
                <span style="color: #0066CC; margin-right: 8px;">•</span>
                {ventajas_title_and_description[2][0]}
            </h3>
            <p style="color: #444; line-height: 1.4; margin: 0;">{ventajas_title_and_description[2][1]}</p>
        </div>

        <div style="display: flex; flex-direction: column; gap: 0.5rem; background-color: #f9f9f9; padding: 1rem; border-radius: 20px;">
            <h3 style="display: flex; align-items: center; gap: 0.5rem; font-weight: bold; color: #333; font-size: 1.1rem;">
                <span style="color: #0066CC; margin-right: 8px;">•</span>
                {ventajas_title_and_description[3][0]}
            </h3>
            <p style="color: #444; line-height: 1.4; margin: 0;">{ventajas_title_and_description[3][1]}</p>
        </div>

        <div style="display: flex; flex-direction: column; gap: 0.5rem; background-color: #f9f9f9; padding: 1rem; border-radius: 20px;">
            <h3 style="display: flex; align-items: center; gap: 0.5rem; font-weight: bold; color: #333; font-size: 1.1rem;">
                <span style="color: #0066CC; margin-right: 8px;">•</span>
                {ventajas_title_and_description[4][0]}
            </h3>
            <p style="color: #444; line-height: 1.4; margin: 0;">{ventajas_title_and_description[4][1]}</p>
        </div>

        <div style="display: flex; flex-direction: column; gap: 0.5rem; background-color: #f9f9f9; padding: 1rem; border-radius: 20px;">
            <h3 style="display: flex; align-items: center; gap: 0.5rem; font-weight: bold; color: #333; font-size: 1.1rem;">
                <span style="color: #0066CC; margin-right: 8px;">•</span>
                {ventajas_title_and_description[5][0]}
            </h3>
            <p style="color: #444; line-height: 1.4; margin: 0;">{ventajas_title_and_description[5][1]}</p>
        </div>
    </div>
<div style="
    display: flex;
    justify-content: center;
    width: 100%;
    margin-top: 2rem;
">
    <a href={product_url}
       target="_blank"
       style="
        background-color: #FFD700;
        border: none;
        padding: 12px 24px;
        border-radius: 20px;
        font-size: 1.1rem;
        font-weight: bold;
        color: #333;
        cursor: pointer;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        text-decoration: none;
    " 
    onmouseover="this.style.transform='scale(1.05)'" 
    onmouseout="this.style.transform='scale(1)'">
        Ver Ventajas
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Amazon_icon.svg/1200px-Amazon_icon.svg.png" 
             alt="Amazon icon" 
             style="width: 20px; height: 20px; object-fit: contain;">
    </a>
</div>
</div>"""
    return product_html

#### Retrieve product info from Oxylabs ####

# Retrieve from Oxylabs
def parse_main_data(content):
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    # Format datetime in ISO format with Z suffix for UTC
    iso_datetime = today.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
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
        "categora": "",
        "discount": discount,
        "previousPrice": previous_price,
        "price": f"{current_price:.2f}€",
        "rating": float(content.get('rating', 0)),
        "rating1": float(content.get('reviews_count', 0)),
        "isAutomated": True,
        "image": content.get('images', [''])[0],
        "previewName": content.get('title', '')[:39] + ('...' if len(content.get('title', '')) > 39 else ''),
        "descriptionOfProduct": "",
        "date": date_str,
        "opinionDeExperto": "",
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


class ProductDisplay(BaseModel):
    product_full_name: str = Field(description="Full name of the product")
    abbreviated_name: str = Field(description="Abbreviated name of the product understandable by anyone.")
    description: str = Field(description="Description of the product highlighting its features.")
    price: str = Field(description="Price of the product")
    bulletpoints: list[str] = Field(description="List of three string bullet points describing the product.")
    ventajas: list[list[str]] = Field(description="List of lists of two string tuples describing the product's advantages. The first tuple is a simple title of the benefit, the second is a full description of the benefit. Make sure to output 6 benefits / tuples everytime.")

def generate_response_gpt(prompt, model):
    completion = client_openai.beta.chat.completions.parse(
    model=model,
    messages=[
        {"role": "system", "content": "You are an expert in analysing and understanding gardening products. You will be given a product's data and you will need to generate an engaging blog section for it. The sections MUST be in Spanish."},
        {"role": "user", "content": str(prompt)}
    ],
    response_format=ProductDisplay,
    )

    product_parsed_data = completion.choices[0].message.parsed

    return product_parsed_data


def generate_text_for_blog(asin):
    product_data = retrieve_product_data(asin)
    product_url = product_data['main_data']['productUrl']
    product_image = product_data['main_data']['image']
    product_price = product_data['main_data']['price']

    prompt = f""" 
    Find here the product data: 
    product_title: {product_data['main_data']['productName']}
    Brand: {product_data['main_data']['marca']}
    Product Description: 
    {product_data['additional_data']['description']} 
    """

    product_blog_section = generate_response_gpt(prompt, "gpt-4o")

    full_response = {
        "title": product_data['main_data']['productName'],
        "product_url": product_url,
        "image": product_image,
        "price": product_price,
        "brand": product_data['main_data']['marca'],
        "blog_section": {
            "product_full_name": product_blog_section.product_full_name,
            "abbreviated_name": product_blog_section.abbreviated_name,
            "description": product_blog_section.description,
            "price": product_blog_section.price,
            "bulletpoints": product_blog_section.bulletpoints,
            "ventajas": product_blog_section.ventajas
        }
    }

    products_data.append(full_response)

    return full_response




def generate_blog_section_for_product(asin):
    product_sections = generate_text_for_blog(asin)
    product_title = product_sections['title']
    product_url = product_sections['product_url']
    product_image = product_sections['image']
    product_price = product_sections['price']
    brand = product_sections['brand']
    product_bulletpoints = product_sections['blog_section']['bulletpoints']
    product_description = product_sections['blog_section']['description']

    main_prodcut_html = get_product_display_html(product_title,
                                                 brand,
                                                 product_price,
                                                 product_image,
                                                 product_bulletpoints,
                                                 product_description,
                                                 product_url)
    
    ventajas_title = "Ventajas del " + product_sections['blog_section']['abbreviated_name']
    ventajas_title_and_description = product_sections['blog_section']['ventajas']
    
    ventajas_html = get_product_ventajas_html(ventajas_title,
                                              ventajas_title_and_description,
                                              product_url)
    
    return main_prodcut_html, ventajas_html


def return_blog_sections(html_section):
    """Helper function to format HTML sections with proper structure"""
    return {
        "type": "HTML",
        "htmlData": {
            "containerData": {
                "width": {
                    "custom": "940"
                },
                "alignment": "CENTER",
                "height": {
                    "custom": "auto"  # Changed to auto for better responsiveness
                }
            },
            "html": html_section,
            "source": "HTML"
        }
    }

class BlogReview(BaseModel):
    blog_title: str = Field(description="SEO friendly title of the full blog post. (ex. 'Los 5 mejores programadores de riego calidad-precio para este 2025') or  ('Las 3 Mejores Sopladoras de Hojas a Gasolina Calidad-Precio 2025')")
    blog_introduction: str = Field(description="Introdution to the blog post. No more than 3-4 sentences. The introduction should be SEO friendly and informative.")
    blog_conclusion: str = Field(description="Conclusion to the blog post. No more than 3-4 sentences. The introduction should be SEO friendly and informative.")
    
def generate_response_gpt_2(prompt, model):
    completion = client_openai.beta.chat.completions.parse(
    model=model,
    messages=[
        {"role": "system", "content": "You are an expert in analysing and understanding gardening products. You will be given a set of product's data and you will need to generate a comprehensive introduction and conclusion to a blog post reviewing the products. The blog post should be SEO friendly and informative. The blog post MUST be written in Spanish."},
        {"role": "user", "content": str(prompt)}
    ],
    response_format=BlogReview,
    )

    product_parsed_data = completion.choices[0].message.parsed

    return product_parsed_data

def create_intro_and_conclusion(products_data):

    full_text = ""

    for product in products_data:
        full_text += f"""\nHere information about a product:
        Name: {product["blog_section"]["product_full_name"]}
        Description: {product["blog_section"]["description"]}
        Price: {product["blog_section"]["price"]}\n
        """
    
    blog_review =generate_response_gpt_2(full_text, "gpt-4o")

    full_response = {
        "blog_title": blog_review.blog_title,
        "blog_introduction": blog_review.blog_introduction,
        "blog_conclusion": blog_review.blog_conclusion
    }

    return full_response


def glue_and_push_html_sections(blog_title,
                                blog_intro,
                                blog_conclusion,
                                html_sections):
    # Ensure proper date format for timestamps
    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    # Format the intro paragraph
    intro = {
        "type": "PARAGRAPH",
        "id": f"intro_{uuid.uuid4().hex[:8]}",  # Add unique ID
        "nodes": [
            {
                "type": "TEXT",
                "id": f"text_{uuid.uuid4().hex[:8]}",  # Add unique ID
                "textData": {
                    "text": blog_intro,
                    "decorations": []
                }
            }
        ]
    }
    
    # Format the conclusion paragraph
    conclusion = {
        "type": "PARAGRAPH",
        "id": f"conclusion_{uuid.uuid4().hex[:8]}",  # Add unique ID
        "nodes": [
            {
                "type": "TEXT",
                "id": f"text_{uuid.uuid4().hex[:8]}",  # Add unique ID
                "textData": {
                    "text": blog_conclusion,
                    "decorations": []
                }
            }
        ]
    }

    # Create the post data structure
    post_data = {
        "title": blog_title,
        "richContent": {
            "nodes": [],
            "metadata": {
                "version": 1,
                "createdTimestamp": current_time,
                "updatedTimestamp": current_time
            }
        },
        "language": "es",  # Changed to Spanish since content is in Spanish
        "status": "DRAFT",
        "commentingEnabled": True
    }

    # Build the nodes array
    all_nodes = [intro]  # Start with intro
    
    # Add HTML sections with proper IDs
    for i, html_section in enumerate(html_sections):
        section_with_id = html_section.copy()
        section_with_id["id"] = f"html_{uuid.uuid4().hex[:8]}"  # Add unique ID
        all_nodes.append(section_with_id)
    
    all_nodes.append(conclusion)  # End with conclusion
    
    # Set all nodes
    post_data["richContent"]["nodes"] = all_nodes

    try:
        # Get the member ID
        members_response = client.get_members(fieldsets=['FULL'])
        
        if not members_response.get('members'):
            raise ValueError("No members found in the account")
            
        member_id = members_response['members'][0]['id']
        
        # Create the blog post draft
        result = client.draft_blog_post(post_data, member_id=member_id)
        print("Draft post created successfully:", result)
            
    except Exception as e:
        print(f"Error creating blog post: {str(e)}")
        raise


class BlogSection:
    def create_comparison_blog(products):
        html_sections = []
        for product in products:
            main_product_html, ventajas_html = generate_blog_section_for_product(product)
            main_product_html = return_blog_sections(main_product_html)
            ventajas_html = return_blog_sections(ventajas_html)
            html_sections.append(main_product_html)
            html_sections.append(ventajas_html)
        
        intro_conclu = create_intro_and_conclusion(products_data)
        blog_title = intro_conclu["blog_title"]
        blog_intro = intro_conclu["blog_introduction"]
        blog_conclusion = intro_conclu["blog_conclusion"]
    
        glue_and_push_html_sections(blog_title,
                                blog_intro,
                                blog_conclusion,
                                html_sections)
    

# if __name__ == "__main__":

#     products = ["B093SNMP7T", "B06XJ5DNDD", "B0001E3TA8"]
#     BlogSection.create_comparison_blog(products)
    
