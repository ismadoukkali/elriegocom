from openai import OpenAI
from pydantic import BaseModel, Field
from enum import Enum
from typing import Type
import time
from typing import Literal
from dotenv import load_dotenv
from src.wix_client import WixAPIClient
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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


def completions_with_structured_output(prompt: str, structure: object ) -> str:

  completion = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "eres un assistente experto en clasificar productos de riego en distintas categorías"},
        {"role": "user", "content": prompt},
    ],
    response_format=structure,
  )

  event = completion.choices[0].message.parsed

  return event

class ProductFamilyCategorization(BaseModel):
    name_of_product: str = Field(..., description="The full name of the product")
    main_categorization_family: Literal[
        "Riego Enterrado", 
        "Riego de Superficie", 
        "Riego por Goteo", 
        "Riego Vacacional"
    ] = Field(..., description=f"""The primary family of products in which this company might fit, based on its name, description and features.""")
    
class ProductSubFamilyCategorization(BaseModel):
    name_of_product: str = Field(..., description="The full name of the product")
    main_categorization_family: str = Field(..., description=f"""The family of products in which this company might fit, based on its name, description and features. It can only fit in one category from the ones provided.""")

class ProductClassifier:
    def __init__(self, hierarchy):
        self.hierarchy = hierarchy
    
    def categorise_family(self, product_content):
        families = completions_with_structured_output(
            prompt=f"Based on the following product naming and description, can you categorise it within the following categories? {list(self.hierarchy.keys())} Here the product content:\n\n{product_content}", 
            structure=ProductFamilyCategorization
        )
        
        return {"family": families.main_categorization_family}
    
    def categorise_sub_family(self, family, product_content):
        subfamilies = list(self.hierarchy[family].keys())
        families = completions_with_structured_output(
            prompt=f"Based on the following product naming and description, can you categorise it within the following categories? {subfamilies} Here the product content:\n\n{product_content}",
            structure=ProductSubFamilyCategorization
        )
        
        return {"subfamily": families.main_categorization_family}
    
    def categorise_subsub_family(self, family, sub_family, product_content):
        if self.hierarchy[family][sub_family]:
            subsubfamilies = list(self.hierarchy[family][sub_family].keys())
            families = completions_with_structured_output(
                prompt=f"""Based on the following product naming and description and the fact that this product was already categorised under family: {family} and subfamily: {sub_family} 
                          Can you categorise it within any of the following categories? {subsubfamilies} 
                          Here the product content:\n\n{product_content}""",
                structure=ProductSubFamilyCategorization
            )
            
            return {"subsubfamily": families.main_categorization_family}
        else:
            return None
    
    def main(self, product_content):
        family = self.categorise_family(product_content)
        sub_family = self.categorise_sub_family(family["family"], product_content)
        subsub_family = self.categorise_subsub_family(family["family"], sub_family["subfamily"], product_content)
        
        return {
            "family": family["family"],
            "subfamily": sub_family["subfamily"],
            "subsubfamily": subsub_family.get("subsubfamily", None) if subsub_family is not None else None
        }
    

# api_key = os.getenv('WIX_API_KEY')
# account_id = os.getenv('WIX_ACCOUNT_ID')
# site_id = os.getenv('WIX_SITE_ID')

# client_wix = WixAPIClient(api_key, account_id, site_id)
# wix_data = WixAPIClient.query_product_with_filters(client_wix, collection_id="FamiliasSub-FamiliasyCategorias")
# hierarchy = transform_wix_categories(wix_data)
# classifier = ProductClassifier(hierarchy)
# result = classifier.main("""ALTADEX Pistola - REGADERA con Varilla DE Agua con 8 Formas DE RIEGO, Con regulador de caudal
# Longitud total: 60 cm
# El sistema de cabezal de pulverización de ángulo ajustable permite una mayor flexibilidad y un trabajo más fácil
# La varilla de agua se puede colgar para un almacenamiento compacto
# Material: ABS, PP, TPR, AL
# Fuente de alimentación: Battery Powered""")

# print(result)

