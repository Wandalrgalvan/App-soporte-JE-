import streamlit as st
import google.generativeai as genai
import urllib.parse
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Soporte Técnico Virtual", page_icon="🔧", layout="centered")

# --- 2. CSS LIMPIO Y FOOTER (Diseño Oscuro Nativo) ---
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

    [data-testid="stChatMessageContainer"] {
        padding-bottom: 100px !important; 
    }
    [data-testid="stBottom"] > div {
        background-color: #1E1E1E !important;
        border-top: 1px solid #333333;
        padding-top: 15px;
        padding-bottom: 15px;
        margin-bottom: 25px !important;
    }
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
    
    .copyright {
        position: fixed;
        bottom: 5px;
        left: 0;
        width: 100%;
        text-align: center;
        color: #666666;
        font-size: 0.75rem;
        z-index: 1000;
        font-family: sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ESTÉTICA: CABECERA NEUTRAL CON ICONO SVG ---
st.markdown("""
<div style="text-align: center; margin-top: 20px; color: #FFD700;">
    <svg width="60" height="60" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
        <path d="M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4zM10.2 10.2l-1.4 1.4c-.6.6-1.5.6-2.1 0l-1.4-1.4c-.6-.6-.6-1.5 0-2.1l1.4-1.4c.6-.6 1.5-.6 2.1 0l1.4 1.4c.7.6.7 1.5 0 2.1z"/>
        <path d="M19.5 7.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4z" opacity=".5"/>
    </svg>
    <h3 style='color: #FFD700; margin-top: 10px; margin-bottom: 0px; font-weight: 700;'>SOPORTE TÉCNICO VIRTUAL</h3>
    <p style='color: #888888; margin-top: 0px;'>Asistente de diagnóstico paso a paso</p>
</div>
""", unsafe_allow_html=True)
st.divider()

# --- 4. CONFIGURACIÓN DE IA ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Falta la API Key en los secretos de Streamlit.")
    st.stop()

# EL CEREBRO ACTUALIZADO: Paciencia extrema y derivación como último recurso
SYSTEM_PROMPT = """Eres un técnico reparador experto, paciente y muy amable. Tu objetivo es ayudar genuinamente al usuario a resolver problemas con CUALQUIER equipo electrónico (celulares, computadoras, Smart TV, Audio, Refrigeración, etc.) como si estuvieras chateando con un amigo.
Reglas ESTRICTAS de comportamiento:
1. PASO A PASO (CRÍTICO): NUNCA des una lista larga de instrucciones. Haz UNA sola pregunta o sugiere UNA sola prueba a la vez, y ESPERA la respuesta.
2. Soporte Exhaustivo: Acompaña al usuario pacientemente. Si una prueba no funciona, sugiere otra alternativa (revisar cables, reiniciar, limpiar filtros, ver configuraciones). Tu objetivo es AGOTAR TODAS las opciones posibles de solución "en casa" antes de rendirte.
3. La Derivación (ÚLTIMO RECURSO): SÓLO debes derivar al taller de Julio cuando se cumplan estas DOS condiciones:
   A) El usuario confirma que ya intentó todas tus sugerencias y el equipo sigue sin funcionar.
   B) El equipo es un Smart TV, equipo de Audio o Refrigeración (Julio no arregla celulares ni PCs).
4. Mensaje de Derivación: Cuando ya no queden opciones y aplique la derivación, dile exactamente esto: "Ya intentamos todo lo posible en casa y parece ser una falla interna. Para este problema vas a necesitar que un técnico lo abra y lo revise bien. Te facilito el contacto de Julio, un técnico de confianza en Tafí Viejo. Podés escribirle tocando el botón de abajo."
5. Límite con otros equipos: Si es un celular o PC que definitivamente no tiene arreglo en casa, dile amablemente que requiere un servicio técnico especializado en ese rubro, pero NO ofrezcas a Julio ni el botón.
6. Cero promesas: No inventes precios ni tiempos de reparación.
"""

@st.cache_resource
def get_best_model():
    modelos_disponibles = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name.lower():
                    return m.name
                modelos_disponibles.append(m.name)
        if modelos_disponibles:
            return modelos_disponibles[0]
    except Exception:
        return None

nombre_modelo_real = get_best_model()

if not nombre_modelo_real:
    st.error("Error con la API Key. Revisa tu cuenta en Google AI Studio.")
    st.stop()

model = genai.GenerativeModel(nombre_modelo_real)

# --- 5. LÓGICA DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¡Hola! Soy tu asistente técnico virtual. 😊 Contame, ¿con qué equipo estás teniendo problemas hoy?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Escribe tu respuesta aquí..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    gemini_history = [
        {"role": "user", "parts": [SYSTEM_PROMPT]},
        {"role": "model", "parts": ["Entendido. Guiaré al usuario paso a paso, agotaré todas las opciones posibles primero, y solo ofreceré el contacto de Julio como último recurso absoluto si es un TV, Audio o Refrigeración."]}
    ]
    
    for msg in st.session_state.messages:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    with st.chat_message("assistant"):
        try:
            response = model.generate_content(gemini_history)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

            # --- BOTÓN DE WHATSAPP ---
            if "julio" in response.text.lower() or "botón de abajo" in response.text.lower():
                NUMERO_WHATSAPP = "5493810000000" # <-- Poner el número real
                resumen_falla = f"Hola Julio, el Asistente Virtual me sugirió contactarte luego de intentar varias pruebas. Tengo un equipo con esta falla: '{prompt}'"
                link_wa = f"https://wa.me/{NUMERO_WHATSAPP}?text={urllib.parse.quote(resumen_falla)}"
                st.markdown(f'<a href="{link_wa}" target="_blank" class="whatsapp-btn">📲 CONTACTAR A JULIO (TÉCNICO)</a>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error de conexión. Detalle técnico: {e}")

st.markdown('<div class="copyright">© 2026 Soporte Técnico Virtual</div>', unsafe_allow_html=True)
