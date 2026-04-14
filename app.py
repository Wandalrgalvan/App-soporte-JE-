import streamlit as st
import google.generativeai as genai
import urllib.parse
from PIL import Image
import os
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Soporte Técnico Virtual", page_icon="🔧", layout="centered")

# --- 2. CSS LIMPIO Y SEGURO (Sin romper el celular) ---
st.markdown("""
<style>
    /* Fondo Oscuro */
    .stApp { background-color: #1E1E1E !important; color: #FFFFFF !important; }
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Espacio inferior para que no se superponga el chat */
    [data-testid="stChatMessageContainer"] { padding-bottom: 150px !important; }
    
    /* Burbujas de chat */
    [data-testid="chatAvatarIcon-assistant"] { background-color: #333333; }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) { background-color: #333333; border-left: 3px solid #FFD700; }
    [data-testid="chatAvatarIcon-user"] { background-color: #FFD700; color: #000000;}
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) { background-color: #FFD700; }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p { color: #000000 !important; font-weight: 500;}

    /* Input de Chat */
    .stChatInputContainer { border-radius: 20px !important; border: 1px solid #333333 !important; background-color: #333333 !important; }
    .stChatInputContainer textarea { color: #FFFFFF !important; }

    /* Estilo del Uploader de Fotos (Garantizado que se vea) */
    [data-testid="stFileUploader"] {
        background-color: #1E1E1E;
    }
    [data-testid="stFileUploader"] section {
        padding: 15px !important;
        border-radius: 15px !important;
        border: 1px dashed #FFD700 !important;
        background-color: #333333 !important;
    }
    /* Ocultar la frase "Drag and drop file here" para que quede minimalista */
    [data-testid="stFileUploader"] section > div > span { display: none !important; }
    [data-testid="stFileUploader"] small { display: none !important; }

    /* Botón WhatsApp */
    .whatsapp-btn {
        display: block; width: calc(100% - 30px); background-color: #25D366; color: #FFFFFF !important;
        text-align: center; padding: 15px; border-radius: 12px; font-weight: 600; text-decoration: none;
        margin: 10px auto;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. CABECERA CON EL ICONO DE HERRAMIENTA ---
st.markdown("""
<div style="text-align: center; margin-top: 10px; color: #FFD700;">
    <svg width="60" height="60" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
        <path d="M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4zM10.2 10.2l-1.4 1.4c-.6.6-1.5.6-2.1 0l-1.4-1.4c-.6-.6-.6-1.5 0-2.1l1.4-1.4c.6-.6 1.5-.6 2.1 0l1.4 1.4c.7.6.7 1.5 0 2.1z"/>
        <path d="M19.5 7.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4z" opacity=".5"/>
    </svg>
    <h3 style='color: #FFD700; margin-top: 10px; margin-bottom: 0px; font-weight: 700;'>SOPORTE TÉCNICO VIRTUAL</h3>
    <p style='color: #CCCCCC; margin-top: 0px;'>Asistente de diagnóstico visual</p>
</div>
""", unsafe_allow_html=True)
st.divider()

# --- 4. CONFIGURACIÓN DE IA ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Falta la API Key en Streamlit.")
    st.stop() 

model = genai.GenerativeModel('gemini-1.5-flash')

SYSTEM_PROMPT = """Eres un asistente técnico virtual paciente. 
1. Exige saber la marca y modelo del equipo. Si mandan foto, analízala minuciosamente (luces, códigos de error en pantallas, etc.).
2. Da UNA sola indicación a la vez, esperando que el usuario responda si funcionó. No des listas largas.
3. Agota las opciones de arreglo casero (reset, limpieza, cables).
4. SÓLO si el problema no se resuelve Y es de Smart TV, Audio o Refrigeración, usa esta frase exacta: "Este problema requiere ser revisado por un técnico. Te facilito el contacto para coordinar."
5. NUNCA derives fallas de impresoras, celulares o PCs a taller; diles que busquen soporte especializado de esa marca.
"""

def stream_text(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.03)

# --- 5. LÓGICA DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¡Hola! Contame: ¿Qué equipo te está dando problemas? (Podés usar el botón de abajo para adjuntar una foto del modelo o la falla)."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image" in message:
            st.image(message["image"], width=200)

# --- 6. CONTROLES DEL USUARIO (Foto y Chat separados de forma segura) ---

# Uploader nativo con recuadro punteado amarillo para que no se pierda
uploaded_file = st.file_uploader("📷 Subir foto de la falla (Opcional)", type=["jpg", "png", "jpeg"])

# Input de chat nativo
if prompt := st.chat_input("Escribí tu mensaje acá..."):
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
            st.error(f"Hubo un error de conexión con la IA. Detalle: {e}")
