import streamlit as st
from utils import login, check_authentication, add_logo_and_navigation
st.set_page_config(
    page_title="El Riego - Sistema de Gestión",
    page_icon="🌱",
    layout="wide"
)

add_logo_and_navigation()

def main():
    if not check_authentication():
        col_1, col_2, col_3 = st.columns([2, 5, 2])
        with col_2:
          st.markdown("#### 🌱 Iniciar sesión — Panel de gestión elriego.com")
          st.caption(
              "Panel interno para importar productos de Amazon a Wix, generar blogs "
              "comparativos y revisar el historial de actualizaciones de precios. "
              "Soporte: idoukkali@apolomarketing.net"
          )
          with st.form("login_form"):
              email = st.text_input("Email")
              password = st.text_input("Contraseña", type="password")
              submit = st.form_submit_button("Iniciar Sesión")
              
              if submit:
                  if login(email, password):
                      st.success("¡Inicio de sesión exitoso!")
                      st.rerun()
                  else:
                      st.error("Credenciales inválidas")
    else:
        st.markdown("""
## 👋 Panel de gestión — elriego.com

Herramienta interna de [elriego.com](https://apolomarketing.wixstudio.com/elriegocom) para publicar productos afiliados de Amazon (ES) en Wix, generar contenido con IA y consultar el resultado de las actualizaciones de precios.

Usa la **barra lateral** para moverte entre secciones.

### Qué hace cada sección

- 📦 **Subir Producto**  
  Introduce un **ASIN** de Amazon.es. El sistema comprueba si ya existe en Wix; si no, lo scrapea, genera descripción / opinión de experto / categoría con IA y lo crea en la colección de productos.

- 🏆 **Subir Bestsellers**  
  Introduce el **ID de categoría** de Amazon bestsellers (dominio ES). Importa los N productos más vendidos de esa categoría (mismo flujo que un producto individual, marcados como best seller).

- 📝 **Subir Blog**  
  Introduce entre **2 y 5 ASINs**. Genera un artículo comparativo con IA y lo guarda como borrador de blog en Wix.

- 🔄 **Actualización de Precios**  
  **Solo monitoriza** los logs de Google Cloud (`price_updates`). No lanza la actualización desde aquí. Los precios se recalculan con un job programado (Cloud Function + Smartproxy/Decodo) que escribe en Wix; esta página muestra qué se actualizó, se omitió o falló.

### Cómo funciona el flujo (resumen)

1. **Importación de producto / bestsellers**  
   [Oxylabs](https://oxylabs.io/) obtiene datos estructurados de Amazon.es → [OpenAI](https://openai.com/) genera textos y categorización → la [API de Wix](https://dev.wix.com/) crea o referencia el producto en el CMS ([estudio Wix del sitio](https://apolomarketing.wixstudio.com/elriegocom)).

2. **Blog comparativo**  
   Se scrapean los ASINs, OpenAI redacta la comparativa y Wix Blog recibe el borrador.

3. **Precios**  
   Un proceso aparte (historicamente Google Cloud Function + Scheduler en el proyecto `elriegocom`) consulta precios en Amazon vía [Decodo](https://decodo.com/) (antes Smartproxy), compara con Wix y actualiza si hay cambio. Los resultados se registran en Cloud Logging; este panel los lee para revisión.

### Servicios que usa el sistema

| Servicio | Rol en elriego |
| --- | --- |
| [Oxylabs](https://oxylabs.io/) | Scraping de fichas y bestsellers de Amazon al subir productos/blogs |
| [Decodo](https://decodo.com/) (ex Smartproxy) | Scraping de precios para el job de actualización |
| [OpenAI](https://openai.com/) | Descripciones, opinión de experto, categorías y blogs |
| [Wix](https://www.wix.com/) / [Wix Studio](https://apolomarketing.wixstudio.com/elriegocom) | CMS de la tienda, productos y blogs |
| [Google Cloud](https://console.cloud.google.com/home/dashboard?project=elriegocom) | Función/scheduler de precios y logs (`elriegocom` / `price_updates`) |

### Notas operativas

- Hace falta iniciar sesión con la cuenta admin configurada en el entorno (`ADMIN_EMAIL` / `ADMIN_PASSWORD`).
- Las credenciales de Oxylabs, Decodo/Smartproxy, OpenAI y Wix viven en variables de entorno (no en este panel).
- La página de precios necesita `credentials.json` (cuenta de servicio de GCP) para leer logs.
- Tras subir un producto, el enlace al detalle suele verse en la propia página de subida (ruta en el sitio Wix Studio).

¿Dudas o incidencias? Contacta con **idoukkali@apolomarketing.net**.
        """)
        
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.authenticated = False
            st.rerun()

if __name__ == "__main__":
    main()