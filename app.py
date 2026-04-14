import streamlit as st
import google.generativeai as genai
import urllib.parse
from PIL import Image
import os
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Soporte Técnico Virtual", page_icon="🔧", layout="centered")

# --- 2. CSS EXTREMO (MINIMALISTA) ---
st.markdown("""
<style>
    .stApp { background-color: #1E1E1E !important; color: #FFFFFF !important; }
    #MainMenu, footer, header {visibility: hidden;}
    [data-testid="stChatMessageContainer"] { padding-bottom: 120px !important; }
    
    /* Burbujas de chat */
    [data-testid="chatAvatarIcon-assistant"] { background-color: #333333; }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) { background-color: #333333; border-left: 3px solid #FFD700; }
    [data-testid="chatAvatarIcon-user"] { background-color: #FFD700; color: #000000;}
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) { background-color: #FFD700; }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p { color: #000000 !important; font-weight: 500;}

    /* Footer Fijo */
    [data-testid="stBottom"] > div {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background-color: #1E1E1E !important; z-index: 1000;
        padding: 10px 0; border-top: 1px solid #333333;
    }

    /* Input de Chat */
    .stChatInputContainer { border-radius: 20px !important; border: 1px solid #333333 !important; background-color: #333333 !important; }
    .stChatInputContainer textarea { color: #FFFFFF !important; }

    /* HACK VISUAL: Reducir el Uploader a un simple botón */
    [data-testid="stFileUploader"] {
        width: 60px !important; 
        margin-top: -15px !important;
        margin-left: 10px !important;
    }
    [data-testid="stFileUploader"] section {
        padding: 0 !important;
        background-color: transparent !important;
        border: none !important;
    }
    [data-testid="stFileUploader"] button {
        background-color: #333333 !important;
        color: #FFD700 !important;
        border: 1px solid #333333 !important;
        border-radius: 50% !important; /* Botón redondo */
        width: 45px !important;
        height: 45px !important;
        padding: 0 !important;
        font-size: 0px !important; /* Oculta el texto 'Browse files' */
    }
    [data-testid="stFileUploader"] button::after {
        content: "📷"; /* Pone el ícono de la cámara */
        font-size: 20px;
        display: block;
    }
    /* Ocultar textos basura del uploader */
    [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] span, .st-emotion-cache-1golkje { display: none !important; }

    /* Botón WhatsApp */
    .whatsapp-btn {
        display: block; width: calc(100% - 30px); background-color: #25D366; color: #FFFFFF !important;
        text-align: center; padding: 15px; border-radius: 12px; font-weight: 600; text-decoration: none;
        margin: 10px auto;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. CABECERA NEUTRAL ---
st.markdown("<h3 style='text-align: center; color: #FFD700; margin-top: 10px;'>SOPORTE TÉCNICO VIRTUAL</h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #CCCCCC; margin-top: -10px;'>Asistente de diagnóstico</p>", unsafe_allow_html=True)

# --- 4. CONFIGURACIÓN DE IA ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Falta la API Key.")
    st.stop() 

# Usamos el modelo ultrarrápido y multimodal actual
model = genai.GenerativeModel('gemini-1.5-flash')

SYSTEM_PROMPT = """Eres un asistente técnico virtual paciente. 
1. Exige saber la marca y modelo del equipo. Si mandan foto, analízala minuciosamente (luces, códigos de error en pantallas, etc.).
2. Da UNA sola indicación a la vez, esperando que el usuario responda si funcionó. No des listas largas.
3. Agota las opciones de arreglo casero (reset, limpieza, cables).
4. SÓLO si el problema no se resuelve Y es de Smart TV, Audio o Refrigeración, usa esta frase exacta: "Este problema requiere ser revisado por un técnico. Te facilito el contacto para coordinar."
5. NUNCA derives fallas de impresoras, celulares o PCs a taller; si no tienen arreglo casero, diles que busquen soporte especializado de esa marca.
"""

def stream_text(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.03)

# --- 5. LÓGICA DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¡Hola! Contame: ¿Qué equipo te está dando problemas? (Podés tocar la 📷 abajo para subir una foto del error o del modelo)."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image" in message:
            st.image(message["image"], width=200)

# --- 6. FOOTER Y UPLOADER (Lado a Lado) ---
st.markdown('<div class="fixed-footer">', unsafe_allow_html=True)
cols = st.columns([0.15, 0.85])

with cols[0]:
    uploaded_file = st.file_uploader("Upload", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

with cols[1]:
    if prompt := st.chat_input("Escribí acá..."):
        msg_dict = {"role": "user", "content": prompt}
        if uploaded_file:
            user_image = Image.open(uploaded_file)
            msg_dict["image"] = user_image
        st.session_state.messages.append(msg_dict)
        
        with st.chat_message("user"):
            st.markdown(prompt)
            if uploaded_file:
                st.image(user_image, width=200)

        with st.chat_message("assistant"):
            try:
                full_prompt = [SYSTEM_PROMPT]
                for msg in st.session_state.messages:
                    if msg["content"]: full_prompt.append(msg["content"])
                    if "image" in msg: full_prompt.append(msg["image"])
                
                response = model.generate_content(full_prompt)
                st.write_stream(stream_text(response.text))
                st.session_state.messages.append({"role": "assistant", "content": response.text})

                if "contacto para coordinar" in response.text.lower():
                    # Reemplaza aquí por el número correcto
                    link = f"https://wa.me/5493810000000?text=Hola,%20el%20asistente%20virtual%20me%20derivó.%20Mi%20falla%20es:%20{urllib.parse.quote(prompt)}"
                    st.markdown(f'<a href="{link}" target="_blank" class="whatsapp-btn">📲 CONTACTAR AL TÉCNICO</a>', unsafe_allow_html=True)
                    
            except Exception as e:
                st.error("Hubo un error de conexión con la IA. Intentá de nuevo.")

st.markdown('</div>', unsafe_allow_html=True)
