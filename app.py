import streamlit as st
import google.generativeai as genai
import urllib.parse
from PIL import Image
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Asistente - Electrónica Julio", page_icon="🔧", layout="centered")

# --- 2. CSS LIMPIO (Diseño Oscuro Nativo) ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .whatsapp-btn {
        display: block;
        width: 100%;
        background-color: #25D366;
        color: white !important;
        text-align: center;
        padding: 15px;
        border-radius: 10px;
        text-decoration: none;
        font-weight: bold;
        margin-top: 15px;
        margin-bottom: 20px;
        transition: 0.3s;
    }
    .whatsapp-btn:hover {
        background-color: #1DA851;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ESTÉTICA: LOGO CENTRADO ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    LOGO_FILENAME = "logo_electronica_julio.png.jpg" 
    try:
        if os.path.exists(LOGO_FILENAME):
            st.image(LOGO_FILENAME, use_container_width=True)
        else:
            st.markdown("<h3 style='text-align: center; color: #FFD700;'>ELECTRÓNICA JULIO</h3>", unsafe_allow_html=True)
    except:
        pass

st.markdown("<p style='text-align: center; color: #888888; margin-top: -10px;'>Asistente Inteligente de Triaje (MVP)</p>", unsafe_allow_html=True)
st.divider()

# --- 4. CONFIGURACIÓN DE IA (MÉTODO INFALIBLE) ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Falta la API Key en los secretos de Streamlit.")
    st.stop()

SYSTEM_PROMPT = """Eres el asistente técnico inteligente de 'Electrónica Julio', un taller experto en reparación de electrónica de consumo en Tafí Viejo, Tucumán.
Tu objetivo es guiar al usuario de forma empática a través de un triaje de problemas.
Reglas:
1. Recepción: Saluda amablemente y pregunta qué equipo le falla (Smart TV, Audio, Refrigeración). NO reparan celulares ni PC.
2. Diagnóstico Nivel 1: Haz preguntas clave y sugiere 1-2 soluciones simples "en casa" (ej. "Asegúrate de que esté enchufado", "Limpia los filtros").
3. Nivel 2 (Taller): Si la falla es de hardware, da un pre-diagnóstico corto y dile que debe traer el equipo al taller.
4. No Inventar Precios: Tienes PROHIBIDO inventar precios. Di que el presupuesto se dará en el taller.
5. Derivación: Cuando determines que necesita taller, dile: "Para coordinar, haz clic en el botón de abajo y envíale un WhatsApp a Julio con el resumen de tu falla."
"""

# Usamos gemini-pro que es 100% estable en todas las regiones y versiones
model = genai.GenerativeModel('gemini-pro')

# --- 5. LÓGICA DE CHAT MANUAL (A prueba de errores) ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¡Hola! Soy el Asistente Inteligente de Electrónica Julio. 😊 Contame, ¿qué equipo te está dando problemas (Smart TV, aire, audio, heladera...) y qué le pasa?"}]

# Renderizar mensajes visuales
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input del usuario
if prompt := st.chat_input("Escribe tu consulta aquí..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Preparar el historial estrictamente alternado para engañar a la API y que no falle
    gemini_history = [
        {"role": "user", "parts": [SYSTEM_PROMPT]},
        {"role": "model", "parts": ["Entendido. Actuaré estrictamente bajo estas reglas como el asistente de Julio."]}
    ]
    
    # Añadir la conversación real
    for msg in st.session_state.messages:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    # Respuesta de la IA
    with st.chat_message("assistant"):
        try:
            # Enviamos el paquete completo
            response = model.generate_content(gemini_history)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

            # --- BOTÓN DE WHATSAPP DINÁMICO ---
            palabras_clave = ["taller", "presupuesto", "coordinar", "revisar", "traer"]
            if any(palabra in response.text.lower() for palabra in palabras_clave):
                NUMERO_WHATSAPP = "5493810000000" # <-- ¡Recuerda poner el número real aquí!
                resumen_falla = f"Hola Julio, soy cliente y hablé con tu Asistente. Mi equipo tiene este problema: '{prompt}'"
                link_wa = f"https://wa.me/{NUMERO_WHATSAPP}?text={urllib.parse.quote(resumen_falla)}"
                st.markdown(f'<a href="{link_wa}" target="_blank" class="whatsapp-btn">📲 SOLICITAR PRESUPUESTO POR WHATSAPP</a>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error de conexión. Detalle técnico: {e}")
