import streamlit as st
from google.cloud import logging
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime, timedelta
import pytz
import os
from utils import check_authentication, StreamlitHandler
from utils import add_logo_and_navigation

# Add logo to sidebar
add_logo_and_navigation()
st.set_page_config(page_title="Actualización de Precios", page_icon="🔄", layout="wide")

@st.cache_resource
def get_logging_client():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(current_dir)
    credentials_path = os.path.join(app_dir, 'credentials.json')
    
    if not os.path.exists(credentials_path):
        st.error(f"Credentials file not found at: {credentials_path}")
        st.stop()
        
    credentials = service_account.Credentials.from_service_account_file(credentials_path)
    return logging.Client(credentials=credentials)

def parse_log_entry(entry):
    """Parse a StructEntry into a dictionary format."""
    payload = entry.payload

    # For summary entries (to keep track of totals)
    if 'error_count' in payload:
        return {
            'timestamp': entry.timestamp,
            'type': 'summary',
            'severity': payload.get('severity', ''),
            'message': payload.get('message', ''),
            'updated_count': payload.get('updated_count', 0),
            'skipped_count': payload.get('skipped_count', 0),
            'error_count': payload.get('error_count', 0)
        }
    
    # Check if message starts with one of our desired prefixes
    message = payload.get('message', '')
    valid_prefixes = (
        "Successfully updated price for",
        "Skipped update for",
        "Invalid or empty Amazon data for ASIN"
    )
    
    if not any(message.startswith(prefix) for prefix in valid_prefixes):
        return None
    
    # For product update entries
    return {
        'timestamp': entry.timestamp,
        'type': 'product',
        'severity': payload.get('severity', ''),
        'asin': payload.get('asin', ''),
        'message': message,
        'product_url': payload.get('product_url', ''),
        'old_price': payload.get('old_price', ''),
        'new_price': payload.get('new_price', ''),
        'current_price': payload.get('current_price', '')
    }

def get_logs(hours=24):
    client = get_logging_client()
    
    filter_str = f'''
    logName="projects/elriegocom/logs/price_updates"
    timestamp >= "{(datetime.now(pytz.UTC) - timedelta(hours=hours)).isoformat()}"
    '''
    
    entries = list(client.list_entries(
        filter_=filter_str,
        order_by=logging.DESCENDING,
        page_size=1000
    ))

    product_logs = []
    latest_summary = None

    for entry in entries:
        parsed_entry = parse_log_entry(entry)
        if parsed_entry is None:
            continue
            
        if parsed_entry['type'] == 'summary':
            if latest_summary is None:
                latest_summary = parsed_entry
        elif parsed_entry['type'] == 'product' and parsed_entry['asin']:
            product_logs.append(parsed_entry)

    return pd.DataFrame(product_logs), latest_summary

def main():
    if not check_authentication():
        st.warning("Por favor, inicia sesión para acceder a esta página.")
        return
    
    st.title("📊 Monitorización de Actualización de Precios")
    
    # Time period selector
    time_period = st.selectbox(
        "Periodo de tiempo",
        options=[1, 6, 12, 24, 48, 72],
        format_func=lambda x: f"Últimas {x} horas",
        index=3
    )
    
    # Get logs and summary
    df, summary = get_logs(hours=time_period)
    
    # Display summary metrics if available
    if summary:
        st.write(f"#### Estadísticas de la última actualización: {summary['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        # Add a divider for visual separation
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Productos Actualizados", summary['updated_count'])
        with col2:
            st.metric("⏭️ Productos Sin Cambios", summary['skipped_count'])
        with col3:
            st.metric("❌ Errores", summary['error_count'])
    
    st.write("#### Estadísticas de la vista actual")
    # Create columns for metrics
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    # Add a divider for visual separation
    if not df.empty:
        # Add filters
        col1, col2 = st.columns(2)
        with col1:
            severity_filter = st.multiselect(
                "Filtrar por severidad",
                options=sorted(df['severity'].unique()),
                default=['ERROR', 'INFO']
            )
        with col2:
            asin_filter = st.multiselect(
                "Filtrar por ASIN",
                options=sorted(df['asin'].unique()),
                default=[]
            )
        
        # Apply filters
        filtered_df = df[df['severity'].isin(severity_filter)]
        if asin_filter:
            filtered_df = filtered_df[filtered_df['asin'].isin(asin_filter)]
        
       # Create style conditions for each row
        def style_rows(row):
            if row['severity'] == 'ERROR':
                return ['background-color: #ffcccc'] * len(row)
            elif 'updated' in str(row['message']).lower():
                return ['background-color: #ccffcc'] * len(row)
            else:
                return [''] * len(row)

        # Display the dataframe
        st.dataframe(
            filtered_df.style.apply(style_rows, axis=1),
            column_config={
                "timestamp": st.column_config.DatetimeColumn(
                    "Fecha/Hora",
                    format="DD/MM/YY HH:mm:ss"
                ),
                "severity": st.column_config.TextColumn("Severidad"),
                "asin": st.column_config.TextColumn("ASIN"),
                "message": st.column_config.TextColumn("Mensaje"),
                "product_url": st.column_config.LinkColumn("URL del Producto"),
                "old_price": st.column_config.TextColumn("Precio Anterior"),
                "new_price": st.column_config.TextColumn("Precio Nuevo"),
                "current_price": st.column_config.TextColumn("Precio Actual")
            },
            hide_index=True,
            use_container_width=True
        )
                
        with stat_col1:
            st.metric(
                label="📋 Total Registros",
                value=len(filtered_df),
                help="Número total de registros mostrados con los filtros actuales"
            )
        
        with stat_col2:
            error_count = len(filtered_df[filtered_df['severity'] == 'ERROR'])
            st.metric(
                label="❌ Errores",
                value=error_count,
                delta=f"{error_count/len(filtered_df)*100:.1f}%" if len(filtered_df) > 0 else "0%",
                delta_color="inverse",
                help="Número de errores encontrados"
            )
        
        with stat_col3:
            success_count = len(filtered_df[filtered_df['message'].str.contains('Successfully updated', case=False, na=False)])
            st.metric(
                label="✅ Actualizaciones Exitosas",
                value=success_count,
                delta=f"{success_count/len(filtered_df)*100:.1f}%" if len(filtered_df) > 0 else "0%",
                help="Número de actualizaciones realizadas con éxito"
            )
        
        
    else:
        st.info("No se encontraron registros para el periodo seleccionado.")

    if st.sidebar.button("Cerrar Sesión"):
            st.session_state.authenticated = False
            st.rerun()
if __name__ == "__main__":
    main()
