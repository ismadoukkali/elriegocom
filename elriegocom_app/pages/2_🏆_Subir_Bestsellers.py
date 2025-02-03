# pages/2_🏆_Subir_Bestsellers.py
import streamlit as st
from utils import check_authentication
from src.upload_products import ElRiegoCOMClient
import logging
from datetime import datetime
from utils import add_logo_and_navigation

# Add logo to sidebar
add_logo_and_navigation()
st.set_page_config(page_title="Subir Best Sellers", page_icon="🏆", layout="wide")

def render():
    if not check_authentication():
        st.warning("Por favor, inicia sesión para acceder a esta página.")
        return

    st.title("Subir Productos Best Seller")
    
    st.markdown("""
    👨‍💻 Esta página te permite subir productos best seller al sistema de El Riego Com. 
    Introduce el ID de la categoría y configura el número de productos a importar.
    """)

    # Form for input
    with st.form("upload_bestsellers"):
        category_id = st.text_input("ID de Categoría")
        num_products = st.slider("Número de productos a importar", 1, 50, 10)
        max_workers = st.slider("Máximo de trabajadores concurrentes", 1, 5, 3)
        submit_button = st.form_submit_button("Subir Best Sellers")

    # Create placeholders for dynamic content
    progress_bar = st.empty()
    metrics_container = st.container()
    log_area = st.empty()

    if submit_button:
        progress_text = "Procesando productos..."
        my_bar = progress_bar.progress(0, text=progress_text)
        
        # Initialize counters in columns
        with metrics_container:
            col1, col2, col3 = st.columns(3)
            processed_count = col1.empty()
            success_count = col2.empty()
            failure_count = col3.empty()
            
            processed_count.metric("Procesados", "0")
            success_count.metric("Exitosos", "0")
            failure_count.metric("Fallidos", "0")

        logs = []
        total_processed = 0
        total_success = 0
        total_failed = 0

        def update_progress(result):
            nonlocal total_processed, total_success, total_failed, logs
            
            # Update counters
            total_processed += 1
            if result["success"]:
                total_success += 1
            else:
                total_failed += 1

            # Update progress bar
            progress = total_processed / num_products
            my_bar.progress(progress, text=progress_text)
            
            # Update metrics
            processed_count.metric("Procesados", f"{total_processed}/{num_products}")
            success_count.metric("Exitosos", str(total_success))
            failure_count.metric("Fallidos", str(total_failed))

            # Update logs
            timestamp = datetime.now().strftime('%H:%M:%S')
            log_entry = f"{timestamp} - ASIN: {result['asin']} - {'✅' if result['success'] else '❌'} {result['message']}"
            logs.append(log_entry)
            log_area.text_area("Logs", "\n".join(logs), height=100)

        try:
            results = ElRiegoCOMClient.push_all_bestsellers_to_cms_sync(
                category_id=category_id,
                max_workers=max_workers,
                number_of_products=num_products,
                progress_callback=update_progress
            )

            # Process completed
            st.success("¡Proceso completado!")

        except Exception as e:
            st.error(f"Error durante el proceso: {str(e)}")
        
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.rerun()

if __name__ == "__main__":
    render()