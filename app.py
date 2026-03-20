import streamlit as st
import google.generativeai as genai
import urllib.parse
from PIL import Image
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Asistente - Electrónica Julio",
    page_icon="🔧",
    layout="centered", 
    initial_sidebar_state="collapsed",
)

LOGO_FILENAME = "logo_electronica_julio.png.jpg" 
logo_image = None
try:
    if os.path.exists(LOGO_FILENAME):
        logo_image = Image.open(LOGO_FILENAME)
except Exception:
    pass

# --- 2. FUERZA BRUTA CSS (COLORES Y LEGIBILIDAD) ---
custom_css = """
<style>
    /* Fondo general oscuro */
    .stApp, .stApp > header {
        background-color: #1E1E1E !important;
    }

    /* --- BURBUJAS DE CHAT --- */
    /* 1. Regla general para TODO el texto dentro de la burbuja (Forzar a BLANCO) */
    [data-testid="stChatMessage"] * {
        color: #FFFFFF !important; 
        font-size: 16px !important;
        font-weight: 500 !important;
    }

    /* 2. Fondo de la burbuja del Bot */
    [data-testid="stChatMessage"] {
        background-color: #333333 !important;
        border-radius: 10px !important;
        padding: 15px !important;
        border-left: 4px solid #FFD700 !important;
        margin-bottom: 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important;
    }

    /* 3. Excepción para la burbuja del Usuario (Fondo Amarillo + Texto Negro) */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background-color: #FFD700 !important;
        border-left: none !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) * {
        color: #000000 !important; 
        font-weight: 600 !important;
    }

    /* --- CAJA DE TEXTO INFERIOR (INPUT) --- */
    /* Fondo oscuro para la caja donde el usuario escribe */
    [data-testid="stChatInput"] {
        background-color: #333333 !important;
        border: 1px solid #FFD700 !important;
        border-radius: 15px !important;
    }
    [data-testid="stChatInput"] * {
        color: #FFFFFF !important;
    }
    [data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #FFFFFF !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #CCCCCC !important;
    }
    
    /* Ocultar menú de streamlit */
    #MainMenu, footer, header {visibility: hidden;}

    /* Botón de WhatsApp */
    .whatsapp-btn {
        display: block;
        width: 100%;
        background-color: #FFD700;
        color: #000000 !important;
        text-align: center;
        padding: 15px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 18px;
        text-decoration: none;
        margin-top: 20px;
        border: 2px solid #FFD700;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 3. RENDERIZADO DE CABECERA ---
st.markdown("<br>", unsafe_allow_html=True) # Espacio
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if logo_image:
        st.image(logo_image, use_container_width=True)
st.markdown('<h2 style="text-align: center; color: #FFFFFF;">ELECTRÓNICA JULIO</h2>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #CCCCCC;">Asistente Inteligente de Triaje</p>', unsafe_allow_html=True)
st.divider()

# --- 4. IA Y CHAT ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Falta API KEY.")
    st.stop()

SYSTEM_PROMPT = """Eres el asistente técnico de 'Electrónica Julio' en Tafí Viejo. 
Saluda, pregunta qué equipo falla (TV, Audio, Refrigeración). Da 1 o 2 soluciones simples para hacer en casa. Si es grave, da un diagnóstico corto y dile que lo traiga al taller. NUNCA inventes precios."""
model = genai.GenerativeModel('gemini-1.5-flash')

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "¡Hola! Soy el Asistente de Electrónica Julio. 😊 Contame, ¿qué equipo te está dando problemas y qué le pasa?"})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Escribe tu consulta aquí..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        full_conversation = [{"role": "user", "parts": [SYSTEM_PROMPT]}]
        for m in st.session_state.messages:
            role = "user" if m["role"] == "user" else "model"
            full_conversation.append({"role": role, "parts": [m["content"]]})

        response = model.generate_content(full_conversation)
        bot_response = response.text

        st.chat_message("assistant").markdown(bot_response)
        st.session_state.messages.append({"role": "assistant", "content": bot_response})

        if any(word in bot_response.lower() for word in ["taller", "presupuesto", "traer", "revisar", "julio"]):
            JULIO_WA = "5493810000000" 
            resumen = urllib.parse.quote("Hola Julio, necesito presupuesto para mi equipo. Hablé con tu asistente virtual.")
            link = f"https://wa.me/{JULIO_WA}?text={resumen}"
            st.markdown(f'<a href="{link}" target="_blank" class="whatsapp-btn">📲 ENVIAR WHATSAPP A JULIO</a>', unsafe_allow_html=True)

    except Exception as e:
        st.error("Error conectando con la IA.")
