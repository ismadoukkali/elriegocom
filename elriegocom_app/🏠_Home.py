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
          st.markdown("#### 🌱 Iniciar Sesión en Panel de Control de elriego.com")
          st.caption("Bienvenido a la página de inicio de la aplicación de gestión de productos de elriego.com. Esta página te permite iniciar sesión y acceder a las diferentes secciones de la aplicación. Si tienes cualquier duda o necesitas ayuda, no dudes en contactarnos vía correo electrónico (idoukkali@apolomarketing.net)")
          with st.form("login_form"):
              email = st.text_input("Email")
              password = st.text_input("Contraseña", type="password")
              submit = st.form_submit_button("Iniciar Sesión")
              
              if submit:
                  if login(email, password):
                      st.success("¡Inicio de sesión exitoso!")
                      st.rerun()  # Changed from experimental_rerun() to rerun()
                  else:
                      st.error("Credenciales inválidas")
    else:
        st.markdown("""
        ## 👋 Bienvenido al sistema de gestión de Elriego.com

Este sistema integrado automatiza la gestión y actualización de contenido para la tienda online El Riego, permitiendo una operación eficiente y escalable.

### Navegación

Utiliza la barra lateral para acceder a las diferentes funcionalidades:

- 📦 **Subir Producto**: Sube productos individuales desde Amazon a Wix, manteniendo sincronizados precios y disponibilidad
- 🏆 **Subir Bestsellers**: Importa automáticamente los productos más vendidos por categoría desde Amazon
- 📝 **Subir Blog**: Genera contenido de calidad con comparativas de productos utilizando IA
- 🔄 **Actualización de Precios**: Monitoriza y gestiona las actualizaciones automáticas de precios

### Tecnologías Integradas

El sistema utiliza varias tecnologías punteras que trabajan en conjunto:

#### Servicios de Web Scraping
- **[Oxylabs](https://oxylabs.io/)**
  - Utilizado para extraer datos detallados de productos
  - Gestiona la rotación de IPs y bypass de captchas
  - Proporciona datos estructurados de productos Amazon

- **[Smartproxy](https://smartproxy.com/)**
  - Monitorización continua de precios
  - Sistema de proxies residenciales para evitar bloqueos
  - Actualización en tiempo real de cambios de precios

#### Infraestructura Cloud
- **[Google Cloud](https://cloud.google.com/?hl=es)**
  - Cloud Functions para automatización de tareas
  - Cloud Scheduler para programación de actualizaciones
  - Cloud Logging para monitorización y debugging
  - Almacenamiento seguro de datos y credenciales

#### Gestión de Tienda
- **[Wix](https://manage.wix.com/studio/sites)**
  - Plataforma principal de la tienda online
  - API para gestión automatizada de productos
  - Actualización automática de precios y stock
  - Gestión de contenido y blogs

#### Inteligencia Artificial
- **[OpenAI](https://openai.com/)**
  - Generación de descripciones de productos
  - Creación de contenido para blog
  - Análisis de productos para comparativas
  - Optimización SEO de contenido

### Flujo de Trabajo

1. **Extracción de Datos**
   - Oxylabs extrae información detallada de productos de Amazon
   - Smartproxy monitoriza continuamente los precios

2. **Procesamiento**
   - Google Cloud Functions procesa y valida los datos
   - OpenAI genera contenido optimizado

3. **Actualización**
   - Wix API actualiza la tienda automáticamente
   - El sistema mantiene sincronizados precios y stock

4. **Monitorización**
   - Sistema de logging para seguimiento de operaciones
   - Alertas automáticas ante cambios significativos
   - Panel de control para visualización de métricas

### Seguridad y Confiabilidad
- Autenticación segura en todos los servicios
- Encriptación de datos sensibles
- Backups automáticos
- Monitorización continua de errores

### Métricas y Rendimiento
- Seguimiento de actualizaciones de precios
- Monitorización de éxito en scraping
- Control de generación de contenido
- Estadísticas de sincronización

Para soporte técnico o consultas, contacta con el equipo de desarrollo.
        """)
        
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.authenticated = False
            st.rerun()  # Changed from experimental_rerun() to rerun()

if __name__ == "__main__":
    main()