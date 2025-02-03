import streamlit as st
from utils import check_authentication, StreamlitHandler
from src.upload_blogs import BlogSection
import logging
from datetime import datetime
from utils import add_logo_and_navigation

# Add logo to sidebar
add_logo_and_navigation()
st.set_page_config(page_title="Subir Blog", page_icon="📝", layout="wide")

def render():
    if not check_authentication():
        st.warning("Por favor, inicia sesión para acceder a esta página.")
        return

    st.title("Generar Blog de Comparación")
    
    st.markdown("""
    📝 Esta página te permite generar blogs de comparación automáticamente.
    Introduce los ASINs de los productos que deseas comparar (mínimo 2, máximo 5).
    """)
    
    with st.form("create_blog"):
        asins = st.text_area(
            "ASINs de productos (uno por línea)",
            help="Introduce entre 2 y 5 ASINs, uno por línea"
        )
        submit_button = st.form_submit_button("Generar Blog")

    log_placeholder = st.empty()
    
    if submit_button:
        # Process ASINs
        asin_list = [asin.strip() for asin in asins.split('\n') if asin.strip()]
        
        if len(asin_list) < 2 or len(asin_list) > 5:
            st.error("Por favor, introduce entre 2 y 5 ASINs.")
            return
        
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
                f'logs/registro_blog_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            with st.spinner("Generando blog..."):
                logger.info("Iniciando generación del blog...")
                logger.info(f"ASINs a procesar: {', '.join(asin_list)}")
                
                # Create progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Process each product
                for i, asin in enumerate(asin_list):
                    status_text.text(f"Procesando producto {i+1}/{len(asin_list)}: {asin}")
                    logger.info(f"Procesando ASIN: {asin}")
                    progress_bar.progress((i + 1) / len(asin_list))
                
                # Generate and push blog
                logger.info("Generando secciones del blog...")
                BlogSection.create_comparison_blog(asin_list)
                
                st.success("¡Blog generado y publicado exitosamente!")
                logger.info("Blog completado y publicado")
                
        except Exception as e:
            st.error(f"Error al generar el blog: {str(e)}")
            logger.error(f"Error en la generación del blog: {str(e)}")
        
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.rerun()

if __name__ == "__main__":
    render()