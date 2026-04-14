import streamlit as st
import google.generativeai as genai
import urllib.parse
import os
import time
from PIL import Image

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Soporte Técnico Virtual", page_icon="🔧", layout="centered")

# --- 2. CSS LIMPIO Y FOOTER ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .whatsapp-btn {
        display: block; width: 100%; background-color: #25D366; color: white !important;
        text-align: center; padding: 15px; border-radius: 10px; text-decoration: none;
        font-weight: bold; margin-top: 15px; margin-bottom: 20px; transition: 0.3s;
    }
    .whatsapp-btn:hover { background-color: #1DA851; }
    [data-testid="stChatMessageContainer"] { padding-bottom: 150px !important; }
    [data-testid="stBottom"] > div {
        background-color: #1E1E1E !important; border-top: 1px solid #333333;
        padding-top: 10px; padding-bottom: 10px; margin-bottom: 25px !important;
    }
    .stChatInputContainer {
        border-radius: 25px !important; border: 1px solid #333333 !important;
        background-color: #333333 !important;
    }
    .stChatInputContainer textarea { color: #FFFFFF !important; font-size: 1rem; }
    .copyright {
        position: fixed; bottom: 5px; left: 0; width: 100%; text-align: center;
        color: #666666; font-size: 0.75rem; z-index: 1000; font-family: sans-serif;
    }
    /* Estilo para el botón de subir imagen */
    [data-testid="stFileUploader"] { margin-bottom: -15px; }
</style>
""", unsafe_allow_html=True)

# --- 3. CABECERA ---
st.markdown("""
<div style="text-align: center; margin-top: 20px; color: #FFD700;">
    <svg width="50" height="50" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
        <path d="M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4zM10.2 10.2l-1.4 1.4c-.6.6-1.5.6-2.1 0l-1.4-1.4c-.6-.6-.6-1.5 0-2.1l1.4-1.4c.6-.6 1.5-.6 2.1 0l1.4 1.4c.7.6.7 1.5 0 2.1z"/>
    </svg>
    <h3 style='color: #FFD700; margin-top: 5px; margin-bottom: 0px; font-weight: 700;'>SOPORTE VIRTUAL AVANZADO</h3>
    <p style='color: #888888; margin-top: 0px;'>Análisis de imágenes y manuales</p>
</div>
""", unsafe_allow_html=True)
st.divider()

# --- 4. CONFIGURACIÓN DE IA ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Falta la API Key en los secretos de Streamlit.")
    st.stop()

# EL NUEVO CEREBRO: Investigador de Manuales
SYSTEM_PROMPT = """Eres un Investigador Técnico Experto. Tu objetivo es ayudar al usuario a arreglar cualquier equipo buscando información específica como si leyeras el manual del fabricante.
Reglas:
1. PREGUNTA EL MODELO: Lo primero que debes hacer es preguntar la MARCA y el MODELO EXACTO del equipo.
2. INVESTIGA: Una vez que tengas el modelo, actúa como si estuvieras buscando en internet el manual de ese equipo. Da pasos ESPECÍFICOS para ese modelo, no generalidades.
3. PASO A PASO: NUNCA des todo el proceso junto. Dale UNA instrucción, espera a que lo haga y te responda, y luego dale el siguiente paso.
4. ANALIZA FOTOS: Si el usuario te envía una foto (de un cable, un error en pantalla, la etiqueta trasera), analízala con sumo detalle y explícale qué estás viendo.
5. DERIVACIÓN (ÚLTIMO RECURSO): Solo si agotaron todos los pasos del manual y el equipo (Smart TV, Audio, Refrigeración) tiene una falla interna confirmada, dile: "Hemos agotado los pasos del manual y parece una falla interna. Para repararlo con seguridad, te sugiero contactar a Julio, un técnico de confianza. Toca el botón abajo." NO derives celulares ni PC.
"""

# Usamos el modelo más potente que lee imágenes (flash o pro-vision)
model = genai.GenerativeModel('gemini-1.5-flash')

# Función para simular el tipeo (Streaming visual)
def stream_text(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04) # Controla la velocidad de tipeo

# --- 5. LÓGICA DE CHAT CON IMÁGENES Y STREAMING ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¡Hola! Soy tu asistente investigador. 🕵️‍♂️ Para poder buscar el manual exacto y ayudarte mejor, ¿me decís qué equipo está fallando y cuál es su **marca y modelo**? (Si no sabés el modelo, podés subirme una foto de la etiqueta de atrás)."}]

# Renderizar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "image" in msg:
            st.image(msg["image"], width=200)

# El Footer ahora incluye un cargador de fotos sutil
col1, col2 = st.columns([0.15, 0.85])
with col1:
    uploaded_file = st.file_uploader("📷", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
with col2:
    prompt = st.chat_input("Escribe tu modelo o problema...")

if prompt or uploaded_file:
    # Mostrar el mensaje/foto del usuario
    with st.chat_message("user"):
        if prompt:
            st.markdown(prompt)
        user_img_obj = None
        if uploaded_file:
            user_img_obj = Image.open(uploaded_file)
            st.image(user_img_obj, width=200)
    
    # Guardar en el estado
    msg_dict = {"role": "user", "content": prompt if prompt else "Te envío esta imagen."}
    if uploaded_file:
        msg_dict["image"] = user_img_obj
    st.session_state.messages.append(msg_dict)

    # Preparar paquete para Gemini (con o sin foto)
    gemini_history = [{"role": "user", "parts": [SYSTEM_PROMPT]}]
    
    for msg in st.session_state.messages:
        role = "model" if msg["role"] == "assistant" else "user"
        parts = []
        if msg["content"]:
            parts.append(msg["content"])
        if "image" in msg:
            parts.append(msg["image"])
        gemini_history.append({"role": role, "parts": parts})

    # Respuesta de la IA con EFECTO TÍPEO
    with st.chat_message("assistant"):
        try:
            # Pedimos la respuesta a la IA
            response = model.generate_content(gemini_history)
            
            # MAGIA DEL TÍPEO: Mostramos la respuesta letra a letra
            st.write_stream(stream_text(response.text))
            
            # Guardamos la respuesta final
            st.session_state.messages.append({"role": "assistant", "content": response.text})

            # Botón de derivación
            if "julio" in response.text.lower() or "botón abajo" in response.text.lower():
                NUMERO = "5493810000000" # <-- Número real
                res = f"Hola Julio, el Asistente evaluó el modelo y me sugirió contactarte. Tengo este equipo: '{prompt}'"
                link = f"https://wa.me/{NUMERO}?text={urllib.parse.quote(res)}"
                st.markdown(f'<a href="{link}" target="_blank" class="whatsapp-btn">📲 CONTACTAR A JULIO (TÉCNICO)</a>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error técnico: {e}")

st.markdown('<div class="copyright">© 2026 Soporte Técnico Virtual</div>', unsafe_allow_html=True)
