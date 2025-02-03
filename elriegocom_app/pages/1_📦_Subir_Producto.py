import streamlit as st
from utils import check_authentication, StreamlitHandler
from src.upload_products import ElRiegoCOMClient
import logging
from datetime import datetime
from utils import add_logo_and_navigation

# Add logo to sidebar
add_logo_and_navigation()
st.set_page_config(page_title="Subir Producto", page_icon="📦", layout="wide")

def render():
    if not check_authentication():
        st.warning("Por favor, inicia sesión para acceder a esta página.")
        return

    st.title("Subir Producto Individual")
    
    st.markdown("""
    👨‍💻 Esta página te permite subir un producto individual al sistema de El Riego Com. 
    Por favor, introduce el ASIN del producto que deseas subir y márcalo como best seller si corresponde.
    """)
    
    with st.form("upload_product"):
        asin = st.text_input("Introduce el ASIN de Amazon")
        is_best_seller = st.checkbox("Marcar como Best Seller")
        submit_button = st.form_submit_button("Subir Producto")

    log_placeholder = st.empty()
    
    if submit_button:
        try:
            logger = logging.getLogger()
            logger.setLevel(logging.INFO)
            
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            streamlit_handler = StreamlitHandler(log_placeholder)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            streamlit_handler.setFormatter(formatter)
            logger.addHandler(streamlit_handler)
            
            file_handler = logging.FileHandler(
                f'logs/registro_producto_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            with st.spinner("Subiendo producto..."):
                result = ElRiegoCOMClient.push_product_to_cms(
                    asin=asin,
                    is_best_seller=is_best_seller
                )
                
                if result["success"]:
                    st.success(f"¡Producto subido exitosamente! ID: {result['product_id']}")
                    product_link = result["response_from_push"]["dataItem"]["data"].get(
                        "link-gardening-amazon-products-productName"
                    )
                    if product_link:
                        full_url = f"https://apolomarketing.wixstudio.com/elriegocom{product_link}"
                        st.markdown(f"[Ver Producto en Wix →]({full_url})")
                else:
                    st.error(f"Error al subir el producto: {result['message']}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
        
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.rerun()

if __name__ == "__main__":
    render()
    
