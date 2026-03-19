import streamlit as st
import google.generativeai as genai
import urllib.parse
from PIL import Image
import os

# --- CONFIGURACIÓN DE PÁGINA (MOBILE-FIRST) ---
st.set_page_config(
    page_title="Asistente de Triaje - Electrónica Julio",
    page_icon="🔧",
    layout="centered", # 'centered' es mejor para móviles que 'wide'
    initial_sidebar_state="collapsed",
)

# --- CARGA DEL LOGO Y MANEJO DE ERRORES ---
LOGO_PATH = "logo_electronica_julio.png" # Nombre exacto del archivo de imagen
logo_image = None
try:
    if os.path.exists(LOGO_PATH):
        logo_image = Image.open(LOGO_PATH)
    else:
        st.warning(f"¡Atención! No se encuentra el archivo '{LOGO_PATH}'. El asistente funcionará, pero sin el logo en la cabecera. Asegúrate de que el archivo esté en la misma carpeta que app.py.")
except Exception as e:
    st.error(f"Error al cargar el logo: {e}")

# --- INYECCIÓN DE CSS PERSONALIZADO (UI/UX - MODO OSCURO) ---
custom_css = f"""
<style>
    /* Fondo general gris carbón */
    .stApp {{
        background-color: #1E1E1E;
        color: #FFFFFF;
    }}

    /* Cabecera fija para el logo y título */
    .fixed-header {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #1E1E1E;
        z-index: 1000;
        padding: 20px 0;
        border-bottom: 2px solid #FFD700; /* Borde amarillo eléctrico */
        text-align: center;
    }}
    .logo-header {{
        max-width: 150px;
        display: block;
        margin-left: auto;
        margin-right: auto;
    }}

    /* Contenedor de chat principal para el ajuste de padding */
    [data-testid="stChatMessageContainer"] {{
        padding-top: 170px; /* Ajuste para que el chat no quede debajo de la cabecera fija */
        padding-bottom: 100px; /* Ajuste para el input fijo de chat */
    }}

    /* Estilo de las Burbujas del Chat */
    [data-testid="stChatMessage"] {{
        border-radius: 20px;
        padding: 15px;
        margin-bottom: 10px;
        font-family: sans-serif;
    }}

    /* Burbuja del Bot (Gris Medio) */
    [data-testid="chatAvatarIcon-assistant"] {{
        background-color: #333333;
    }}
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {{
        background-color: #333333;
        color: #FFFFFF !important;
        border-left: 4px solid #FFD700; /* Acento amarillo */
    }}
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) p {{
        color: #FFFFFF !important;
    }}

    /* Burbuja del Usuario (Amarillo Eléctrico) */
    [data-testid="chatAvatarIcon-user"] {{
        background-color: #FFD700;
        color: #000000;
    }}
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
        background-color: #FFD700;
        color: #000000 !important;
    }}
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p {{
        color: #000000 !important;
        font-weight: 500;
    }}

    /* Ocultar elementos innecesarios de Streamlit para móviles */
    #MainMenu, footer, header {{visibility: hidden;}}
    .stDeployButton {{display:none;}}

    /* Estilo para el Botón de WhatsApp */
    .whatsapp-btn {{
        display: block;
        width: 100%;
        background-color: #FFD700; /* Amarillo Eléctrico */
        color: #000000 !important;
        text-align: center;
        padding: 20px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 1.2rem;
        text-decoration: none;
        margin-top: 20px;
        margin-bottom: 20px;
        border: 3px solid #FFD700;
        transition: background-color 0.3s ease, color 0.3s ease;
        font-family: sans-serif;
    }}
    .whatsapp-btn:hover {{
        background-color: transparent;
        color: #FFD700 !important;
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# --- RENDERIZADO DE CABECERA (CON LOGO) ---
# Se inyecta la cabecera fija
st.markdown('<div class="fixed-header">', unsafe_allow_html=True)
if logo_image:
    st.image(logo_image, width=150) # El ancho se ajusta para móviles
else:
    # Fallback si no hay logo
    st.markdown('<h1 style="color: #FFD700; margin-top: 0; font-size: 1.8rem;">ELECTRÓNICA JULIO</h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #FFFFFF; font-size: 1.1rem; margin-top: -10px;">Asistente Inteligente de Triaje (MVP)</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# --- CONFIGURACIÓN DE IA (GEMINI API) ---
# Intenta obtener la API KEY desde los secretos de Streamlit
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("No se encontró la clave API 'GEMINI_API_KEY' en los secretos de Streamlit (st.secrets). Por favor, configúrala en el panel de control de Streamlit Cloud.")
    st.stop() # Detiene la ejecución si no hay clave

# --- SYSTEM PROMPT ESTRICTO (LA PERSONALIDAD DEL BOT) ---
SYSTEM_PROMPT = """Eres el asistente técnico inteligente de 'Electrónica Julio', un taller experto en reparación de electrónica de consumo en Tafí Viejo, Tucumán.
Tu objetivo es guiar al usuario de forma empática a través de un triaje de problemas.
Sigue estrictamente estas reglas:
1.  **Recepción:** Comienza saludando amablemente con un toque tucumano sutil (ej. "¡Hola! ¿En qué te puedo ayudar hoy?") y pregúntale qué equipo le está fallando (Smart TV, Audio, Refrigeración, etc.).
2.  **Diagnóstico Nivel 1:** Haz preguntas clave y sugiere 1-2 soluciones simples "en casa" que no requieran conocimientos técnicos profundos (ej. "Asegúrate de que esté enchufado", "Intenta reiniciar el equipo", "Limpia los filtros del aire").
3.  **Nivel 2 (Taller):** Si las soluciones de Nivel 1 no funcionan o si la falla es claramente de hardware (ej. pantalla rota, no enciende en absoluto, humo), proporciona un pre-diagnóstico corto y directo (ej. "Podría ser un problema en la fuente de alimentación") y dile que debe traer el equipo al taller.
4.  **No Inventar Precios:** Tienes terminantemente PROHIBIDO inventar precios o presupuestos. Siempre di que el presupuesto se dará en el taller tras la revisión.
5.  **Derivación a WhatsApp:** Cuando determines que se necesita una visita al taller, dile al usuario: "Para coordinar, haz clic en el botón de abajo y envíale un WhatsApp a Julio con el resumen de la falla. Él te responderá pronto."
"""

# Configuración del modelo Gemini Pro
model = genai.GenerativeModel('gemini-pro')


# --- MANEJO DEL CHAT Y ESTADO DE SESIÓN ---
# Inicializar el historial de chat si no existe
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Mensaje de bienvenida inicial del bot
    initial_bot_message = "¡Hola! Soy el Asistente Inteligente de Electrónica Julio. 😊 Contame, ¿qué equipo te está dando problemas (Smart TV, aire, audio, heladera...) y qué le pasa?"
    st.session_state.messages.append({"role": "assistant", "content": initial_bot_message})

# Mostrar mensajes de chat del historial (con el CSS personalizado aplicado)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --- LÓGICA DE INPUT DEL USUARIO Y RESPUESTA DE LA IA ---
# Campo de texto para chatear
if prompt := st.chat_input("Escribe tu consulta aquí..."):
    # Mostrar mensaje del usuario inmediatamente
    st.chat_message("user").markdown(prompt)
    # Agregar mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generar respuesta de la IA (incluyendo el historial y el system prompt)
    try:
        # Combinar System Prompt y el historial de mensajes para el modelo
        full_conversation = [{"role": "user", "parts": [SYSTEM_PROMPT]}]
        for m in st.session_state.messages:
            # Gemini requiere mapear roles a 'user' o 'model'
            if m["role"] == "user":
                full_conversation.append({"role": "user", "parts": [m["content"]]})
            else:
                full_conversation.append({"role": "model", "parts": [m["content"]]})

        # Llamada a la API de Gemini
        response = model.generate_content(full_conversation)
        bot_response = response.text

        # Mostrar respuesta del bot
        st.chat_message("assistant").markdown(bot_response)
        # Agregar respuesta del bot al historial
        st.session_state.messages.append({"role": "assistant", "content": bot_response})


        # --- LÓGICA DEL BOTÓN DE WHATSAPP ---
        # Analizar la respuesta del bot para ver si sugiere ir al taller
        # Buscamos palabras clave de derivación
        if any(keyword in bot_response.lower() for keyword in ["traer el equipo", "visita al taller", "presupuesto se dará", "coordinar"]):
            
            # --- Generar resumen de la falla para el mensaje de WhatsApp ---
            # Usamos la IA para generar un resumen corto y técnico del historial de chat
            summary_prompt = f"Resume brevemente el problema técnico del usuario basándose en esta conversación. El resumen es para enviar a un técnico. Conversación:\n\n{full_conversation}"
            try:
                # Llamada rápida a la IA para el resumen
                summary_response = model.generate_content([{"role": "user", "parts": [summary_prompt]}])
                fault_summary = summary_response.text.strip()
            except Exception:
                # Fallback si el resumen falla
                fault_summary = "Consulta técnica de triaje."

            # --- Crear el enlace de WhatsApp ---
            # CONFIGURACIÓN: REEMPLAZAR POR EL NÚMERO REAL DE JULIO (formato: país+área+número sin + ni espacios)
            JULIO_WHATSAPP_NUMBER = "5493810000000" 
            
            # Armar el mensaje para WhatsApp
            wa_message = f"Hola Julio, soy un cliente del taller y estuve hablando con tu Asistente de Triaje. Tengo un problema con mi equipo. Resumen de la falla:\n\n{fault_summary}"
            
            # Codificar el mensaje para la URL
            encoded_wa_message = urllib.parse.quote(wa_message)
            wa_link = f"https://wa.me/{JULIO_WHATSAPP_NUMBER}?text={encoded_wa_message}"

            # --- Mostrar el botón de WhatsApp ---
            # Se usa st.markdown con HTML para aplicar el CSS personalizado
            st.markdown(f'<a href="{wa_link}" target="_blank" class="whatsapp-btn">📲 SOLICITAR PRESUPUESTO POR WHATSAPP</a>', unsafe_allow_html=True)
        # --- FIN LÓGICA DEL BOTÓN DE WHATSAPP ---

    except Exception as e:
        # Manejo de errores de API
        st.error(f"Hubo un error al generar la respuesta de la IA. Por favor, intenta de nuevo. Detalle: {e}")
