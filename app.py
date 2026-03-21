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

    /* Footer fijo y elegante */
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
    
    /* Copyright neutral */
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

# --- 3. ESTÉTICA: CABECERA NEUTRAL (Sin Logo) ---
st.markdown("<h3 style='text-align: center; color: #FFD700; margin-top: 20px;'>SOPORTE TÉCNICO VIRTUAL</h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888888; margin-top: -10px;'>Asistente de diagnóstico rápido</p>", unsafe_allow_html=True)
st.divider()

# --- 4. CONFIGURACIÓN DE IA (Búsqueda Dinámica Anti-Errores) ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Falta la API Key en los secretos de Streamlit.")
    st.stop()

# EL NUEVO CEREBRO: Secuencial y sutil
SYSTEM_PROMPT = """Eres un técnico reparador experto, paciente y muy amable. Tu objetivo es ayudar genuinamente al usuario a resolver problemas con sus equipos electrónicos (Smart TV, Audio, Refrigeración) como si estuvieras chateando con un amigo.
Reglas ESTRICTAS de comportamiento:
1. PASO A PASO (CRÍTICO): NUNCA des una lista larga de instrucciones. Haz UNA sola pregunta o sugiere UNA sola prueba a la vez, y ESPERA la respuesta del usuario.
2. Tono Humano: Tus respuestas deben ser cortas, naturales y conversacionales. No suenes como un manual de instrucciones de IA.
3. Diagnóstico Nivel 1: Intenta 1 o 2 soluciones simples "en casa" (revisar enchufes, limpiar filtros, reiniciar de fábrica). 
4. La Derivación (La Venta Suave): SÓLO si las pruebas básicas fallan o es evidente que hay daño de hardware (pantalla rota, no enciende nada, olor a quemado), dile que necesita revisión técnica por un profesional. Ahí, ofrécele el contacto de un taller. 
Dile exactamente esto: "Para ese problema ya vas a necesitar que un técnico lo abra y lo revise bien. Si querés, te puedo facilitar el contacto de Julio, que es un técnico de mucha confianza en Tafí Viejo. Podés escribirle tocando el botón de abajo."
5. Cero promesas: No inventes precios ni tiempos de reparación.
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

# --- 5. LÓGICA DE CHAT SECUENCIAL ---
if "messages" not in st.session_state:
    # Saludo mucho más natural y que invita a una sola respuesta
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
        {"role": "model", "parts": ["Entendido. Seré súper conversacional, haré una pregunta a la vez y solo recomendaré a Julio si es estrictamente necesario ir a un taller."]}
    ]
    
    for msg in st.session_state.messages:
        role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    with st.chat_message("assistant"):
        try:
            response = model.generate_content(gemini_history)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

            # --- BOTÓN DE WHATSAPP (Aparece solo cuando el bot menciona a Julio) ---
            if "julio" in response.text.lower() or "botón de abajo" in response.text.lower():
                NUMERO_WHATSAPP = "5493810000000" # <-- Reemplazar por el real
                resumen_falla = f"Hola Julio, el Asistente Virtual me sugirió contactarte. Tengo un equipo con esta falla: '{prompt}'"
                link_wa = f"https://wa.me/{NUMERO_WHATSAPP}?text={urllib.parse.quote(resumen_falla)}"
                st.markdown(f'<a href="{link_wa}" target="_blank" class="whatsapp-btn">📲 CONTACTAR A JULIO (TÉCNICO)</a>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error de conexión. Detalle técnico: {e}")

# Footer de Copyright
st.markdown('<div class="copyright">© 2026 Soporte Técnico Virtual</div>', unsafe_allow_html=True)
