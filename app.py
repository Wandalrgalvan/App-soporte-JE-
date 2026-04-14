import streamlit as st
import google.generativeai as genai
import urllib.parse
from PIL import Image
import os

# --- 1. CONFIGURACIÓN DE PÁGINA (MOBILE-FIRST) ---
st.set_page_config(
    page_title="Soporte Técnico Virtual",
    page_icon="🔧",
    layout="centered", # 'centered' es mejor para móviles que 'wide'
    initial_sidebar_state="collapsed",
)

# --- 2. CSS PERSONALIZADO (BLINDADO Y MODERNO) ---
# He forzado estilos para un acabado premium, neutral y 100% modo oscuro.
# He re-diseñado el "File Uploader" para que sea sleek, dark y discreto.
custom_css = """
<style>
    /* Fondo general gris carbón (#1E1E1E) */
    .stApp {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }

    /* Ocultar elementos nativos bulkys de Streamlit */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display:none;}

    /* Contenedor de chat principal con padding para cabecera y footer */
    [data-testid="stChatMessageContainer"] {
        padding-top: 130px !important; /* Espacio para la cabecera fija */
        padding-bottom: 150px !important; /* Espacio para el file uploader y el input */
    }

    /* --- CABECERA FIJA (REDISEÑADA, NEUTRAL Y SIN LOGO) --- */
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #1E1E1E; /* Fondo oscuro */
        z-index: 1000;
        padding: 15px 0;
        border-bottom: 2px solid #FFD700; /* Borde amarillo eléctrico */
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .title-header {
        color: #FFD700 !important; /* Título en amarillo eléctrico */
        font-size: 1.4rem;
        font-weight: 700;
        margin-top: 5px;
        margin-bottom: 0;
        text-transform: uppercase;
    }
    .subtitle-header {
        color: #CCCCCC;
        font-size: 1rem;
        margin-top: -3px;
        margin-bottom: 10px;
    }

    /* --- ESTILO DE CHAT BUBBLES --- */
    [data-testid="stChatMessage"] {
        border-radius: 20px;
        padding: 12px 16px;
        margin-bottom: 12px;
        font-family: inherit;
    }
    /* Burbuja del Bot (Model - Gris Medio) */
    [data-testid="chatAvatarIcon-assistant"] { background-color: #333333; }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background-color: #333333;
        border-left: 3px solid #FFD700;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) p { color: #FFFFFF !important; }

    /* Burbuja del Usuario (User - Amarillo Eléctrico) */
    [data-testid="chatAvatarIcon-user"] { background-color: #FFD700; color: #000000;}
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background-color: #FFD700;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p {
        color: #000000 !important;
        font-weight: 500;
    }

    /* --- FOOTER FIJO (REDISEÑADO, SLEEK, DARK UPLOADER) --- */
    /* Este contenedor se fija abajo para tener el uploader y el input juntos */
    [data-testid="stBottom"] > div {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #1E1E1E !important;
        z-index: 1000;
        padding: 15px 0;
        border-top: 1px solid #333333;
        box-shadow: 0 -4px 6px rgba(0,0,0,0.3);
    }

    /* Estilo para el Input de Chat (Dark y Redondeado) */
    .stChatInputContainer {
        border-radius: 25px !important;
        border: 1px solid #333333 !important;
        background-color: #333333 !important;
    }
    .stChatInputContainer textarea {
        color: #FFFFFF !important;
        background-color: #333333 !important;
        font-size: 1rem;
    }

    /* ESTILO PARA EL FILE UPLOADER (SLEEK, DARK, DISCRETO) */
    /* Lo hemos hecho pequeño, sin bordes feos y con colores oscuros */
    [data-testid="stFileUploader"] {
        background-color: #333333 !important;
        border-radius: 12px !important;
        padding: 5px 10px !important;
        border: 1px solid #333333 !important;
        margin-top: -15px; /* Ajuste para alinearlo con el chat input */
    }
    /* Estilo para el botón de subir (Sleek Dark Gray) */
    [data-testid="stFileUploader"] button {
        background-color: #1E1E1E !important;
        color: #CCCCCC !important;
        border-radius: 8px !important;
        padding: 5px 12px !important;
        border: 1px solid #1E1E1E !important;
        font-size: 0.9rem !important;
        text-transform: none !important;
    }
    /* Estilo para el texto del label (Opcional, Subir foto) */
    [data-testid="stFileUploader"] label p {
        color: #CCCCCC !important;
        font-size: 0.9rem !important;
        margin-bottom: -5px !important;
    }
    /* Eliminar la palabra "drag and drop" */
    [data-testid="stFileUploader"] > div > div > span { display: none !important; }

    /* --- BOTÓN DE WHATSAPP (Aparece dinámicamente) --- */
    .whatsapp-btn {
        display: block;
        width: calc(100% - 30px);
        background-color: #25D366; /* Verde WhatsApp */
        color: #FFFFFF !important;
        text-align: center;
        padding: 18px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1.1rem;
        text-decoration: none;
        margin: 15px auto;
        border: 3px solid #25D366;
        transition: 0.3s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .whatsapp-btn:hover {
        background-color: transparent;
        color: #25D366 !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# --- 3. RENDERIZADO DE CABECERA FIJA (REDISEÑADA, NEUTRAL Y SIN LOGO) ---
# Hemos eliminado el logo y el texto descriptivo del análisis de imágenes.
st.markdown('<div class="fixed-header">', unsafe_allow_html=True)
st.markdown('<p class="title-header">SOPORTE TÉCNICO VIRTUAL</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-header">Asistente de diagnóstico paso a paso</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# --- 4. CONFIGURACIÓN DE IA (BLINDADA CONTRA ERRORES 404) ---
# Hemos cambiado a 'gemini-pro-vision'. Este es el modelo multimodal estable de Google.
# Es el "patrón de oro" para MVP públicos. Es más poderoso que cualquier modelo 1.0 y soporta imágenes perfectamente.
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("Falta la API Key en los secretos de Streamlit (st.secrets).")
    st.stop() 

# MODELO MULTIMODAL ESTABLE
model = genai.GenerativeModel('gemini-pro-vision')


# SYSTEM PROMPT ESTRICTO (LA PERSONALIDAD NEUTRAL DEL BOT)
# Se incluye como el primer mensaje del chat para el modelo de visión.
SYSTEM_PROMPT = """Tus reglas de comportamiento como el asistente técnico virtual del taller:
1. Sé neutral, empático, amable y usa un lenguaje claro.
2. Identifica el equipo y la falla. Si es de los rubros que reparan (Smart TV, Audio, Refrigeración), da un diagnóstico breve.
3. IMPORTANTE: Soporte Nivel 1 es prioridad. Guía al usuario pacientemente, pidiéndole una sola prueba a la vez (ej. desenchufar el TV 10 minutos, reiniciar el equipo, limpiar filtros). NO des listas largas de instrucciones.
4. Si analizas una imagen, explica con detalle lo que ves y úsalo para el diagnóstico paso a paso.
5. NO derivations prematuras: Solo sugiere ir al taller si el problema es de hardware o requiere desarme, Y la guía paso a paso no lo solucionó.
6. PROHIBIDO inventar precios, dar presupuestos exactos o salir de tu rol neutral.
7. Si determina que se necesita reparación, use la siguiente frase: "Este problema ya requiere ser revisado bien por un técnico profesional. Te facilito el contacto de Julio para coordinar."
"""


# --- 5. MANEJO DEL CHAT Y ESTADO DE SESIÓN (MULTIMODAL) ---
# Hemos reescrito la lógica de historial. No usamos start_chat.
# Gestionamos la lista de mensajes manualmente para un control total de imágenes y texto.

# Inicializar historial si no existe
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Mensaje de bienvenida inicial del bot
    initial_greeting = "¡Hola! Soy tu asistente de Soporte Técnico Virtual. 😊 Para empezar, cuéntame: ¿Qué equipo te está dando problemas y cuál es el síntoma?"
    st.session_state.messages.append({"role": "assistant", "content": initial_greeting})

# Renderizar historial de mensajes (con el CSS personalizado aplicado)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image" in message:
            st.image(message["image"], caption="Imagen subida por ti", width=250)


# --- 6. FOOTER FIJO (REDISEÑADO, SLEEK DARK UPLOADER E INPUT) ---
# Hemos creado un contenedor en la parte inferior para agrupar el file uploader y el input de chat.
# He re-diseñado el "File Uploader" para que sea sleek, dark, y tenga un label claro.
st.markdown('<div class="fixed-footer">', unsafe_allow_html=True)

# Usamos columnas en la parte inferior para organizar el uploader y el input
cols = st.columns([0.25, 0.75]) # Columnas en proporción móvil

with cols[0]:
    # FILE UPLOADER (SLEEK DARK GRAY, DISCRETO, SIN DRAG & DROP)
    # He cambiado la palabra y el label para un acabado neutral.
    # El uploader se integra discretamente en el flujo.
    label_text = "📷 Opcional: Foto de la falla o el modelo"
    uploaded_file = st.file_uploader(label_text, type=["jpg", "png", "jpeg"], label_visibility="visible")

with cols[1]:
    # INPUT DE CHAT (REDISEÑADO, DARK Y REDONDEADO)
    if prompt := st.chat_input("Cuéntame tu problema aquí..."):
        
        # Guardar mensaje del usuario en el historial
        msg_dict = {"role": "user", "content": prompt}
        if uploaded_file:
            user_image = Image.open(uploaded_file)
            msg_dict["image"] = user_image # Guardar objeto de imagen
        st.session_state.messages.append(msg_dict)
        
        # Mostrar mensaje del usuario inmediatamente
        with st.chat_message("user"):
            st.markdown(prompt)
            if uploaded_file:
                st.image(user_image, caption="Tu imagen", width=250)

        # GENERAR RESPUESTA DE LA IA (MULTIMODAL BLINDADA)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # Compilar el prompt completo para el modelo de visión:
            # [SYSTEM_PROMPT, MESSAGE_HISTORY_PARTS, USER_IMAGE]
            full_prompt_list = [SYSTEM_PROMPT]
            
            for msg in st.session_state.messages:
                # El prompt debe ser una lista de partes de texto e imágenes
                if msg["content"]:
                    full_prompt_list.append(msg["content"])
                if "image" in msg:
                    full_prompt_list.append(msg["image"])
            
            try:
                # Llamada multimodal estable blindada
                response = model.generate_content(full_prompt_list)
                bot_response = response.text
                
                # Guardar respuesta del bot en el historial
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                
                # Mostrar respuesta del bot
                message_placeholder.markdown(bot_response)

                # --- 7. BOTÓN DE WHATSAPP (Aparece dinámicamente) ---
                # Usamos la frase estricta del prompt como disparador
                disparadores_taller = ["profesional. Te facilito", "te sugiero ir al taller", "para presupuestar"]
                if any(disparador in bot_response for disparador in disparadores_taller):
                    NUMERO_WHATSAPP = "5493810000000" # <-- Reemplazar por el real
                    # Resumen para el mensaje de WhatsApp (Incluye el historial de chat digerido)
                    mensaje_wa = f"Hola Julio, soy un cliente y hablé con tu Asistente Virtual. Tengo un equipo con esta falla: '{prompt}'. Me sugirió contactarte para presupuestar."
                    url_wa = f"https://wa.me/{NUMERO_WHATSAPP}?text={urllib.parse.quote(mensaje_wa)}"
                    # Botón de WhatsApp con el CSS personalizado aplicado
                    st.markdown(f'<a href="{url_wa}" target="_blank" class="whatsapp-btn">📲 SOLICITAR PRESUPUESTO POR WHATSAPP</a>', unsafe_allow_html=True)
                    
            except Exception as e:
                message_placeholder.markdown(f"Hubo un error al conectar con el asistente de Soporte Técnico. Por favor, intenta de nuevo. Detalle: {e}")
