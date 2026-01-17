
# 📊 Litio Dashboard (Streamlit Edition)

Esta es una aplicación de análisis logístico inteligente diseñada para la gestión de despachos de litio. Aunque utiliza **React** en el frontend, su interfaz ha sido adaptada para emular la experiencia de usuario de **Streamlit (Python)**.

## ✨ Características

- **Carga de Archivos**: Procesa bases de datos en formato Excel (.xlsx, .xlsm).
- **IA Generativa**: Integración con Google Gemini API para análisis de insights operativos.
- **Visualización Dinámica**: Gráficos interactivos usando Recharts.
- **Exportación**: Generación de informes profesionales en PDF.
- **UI/UX**: Estética limpia inspirada en Streamlit.

## 🚀 Instalación y Configuración

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/tu-usuario/litio-dashboard.git
   ```

2. **Configurar la API Key**:
   Para que el análisis de IA funcione, necesitas una clave de API de Google Gemini.
   - Crea un archivo `.env` en la raíz del proyecto.
   - Añade tu clave: `API_KEY=tu_clave_aqui`

3. **Despliegue**:
   Puedes desplegarlo fácilmente en **Vercel** o **Netlify**. Asegúrate de configurar la variable de entorno `API_KEY` en el panel de control de la plataforma de despliegue.

## 🛡️ Seguridad

Este proyecto utiliza variables de entorno para manejar la `API_KEY`. Nunca compartas tu archivo `.env` ni lo subas a repositorios públicos.

---
*Hecho con ❤️ para la optimización logística.*
