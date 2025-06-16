import streamlit as st
import requests
import json
import time
import html

st.set_page_config(page_title="inference-ui | Lekta ES", layout="wide")

st.title("inference-ui | Lekta ES")

CSS = """
.respuesta-box {
    padding: 15px 20px;
    border-radius: 10px;
    border: 1px solid #ccc;
    margin-bottom: 1em;
}
@media (prefers-color-scheme: dark) {
    .respuesta-box {
        background-color: #222;
        color: #eee;
        border: 1px solid #444;
    }
}
@media (prefers-color-scheme: light) {
    .respuesta-box {
        background-color: #f9f9f9;
        color: #000;
        border: 1px solid #ddd;
    }
}
.frag-card {
    padding: 10px 15px;
    border-radius: 6px;
    margin-bottom: 10px;
    border-left: 4px solid #4a90e2;
}
@media (prefers-color-scheme: dark) {
    .frag-card {
        background-color: #1e1e1e;
        color: #eee;
        border-color: #3e8ef7;
    }
}
@media (prefers-color-scheme: light) {
    .frag-card {
        background-color: #f0f2f6;
        color: #000;
    }
}
"""

st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

def call_classifier(payload):
    try:
        response = requests.post(
            "https://dynamic-classifier-models-es.up.railway.app/classify",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.Timeout:
        return None, "⏳ Tiempo de espera agotado, intenta de nuevo."
    except requests.exceptions.ConnectionError:
        return None, "❌ No se pudo conectar con el servidor, revisa tu conexión."
    except Exception as e:
        return None, f"Error inesperado: {e}"

def call_rag(payload):
    try:
        response = requests.post(
            "https://api-rag-models-es.up.railway.app/query",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.Timeout:
        return None, "⏳ Tiempo de espera agotado, intenta de nuevo."
    except requests.exceptions.ConnectionError:
        return None, "❌ No se pudo conectar con el servidor, revisa tu conexión."
    except Exception as e:
        return None, f"Error inesperado: {e}"

def render_dynamic_classifier():
    with st.form("form_classify"):
        user_input = st.text_area(
            "Entrada del usuario",
            value="Hola, quiero reservar un vuelo para mañana",
            help="Introduce el texto que quieres clasificar."
        )

        st.markdown("#### Intents")
        intents_input = st.text_area(
            "Introduce las intenciones",
            value="book_flight, cancel_booking, get_status",
            help="Ejemplo: book_flight, cancel_booking, get_status"
        )

        st.markdown("#### Entities")
        entities_input = st.text_area(
            "Introduce las entidades",
            value="date, destination, origin",
            help="Ejemplo: date, destination, origin"
        )

        submit_button = st.form_submit_button("🚀 GO!")

    if submit_button:
        if not user_input.strip():
            st.warning("⚠️ Por favor, introduce un texto para clasificar.")
            return

        intents = {i.strip(): "" for i in intents_input.split(",") if i.strip()}
        entities = {e.strip(): "" for e in entities_input.split(",") if e.strip()}

        payload = {
            "user_input": user_input.strip(),
            "intents": {k: v.strip() for k, v in intents.items()},
            "entities": {k: v.strip() for k, v in entities.items()}
        }

        with st.spinner("⌛ Enviando petición al clasificador..."):
            start = time.time()
            resp_json, error = call_classifier(payload)
            duration = time.time() - start

        if error:
            st.error(f"❌ {error}")
        else:
            st.success(f"✅ Clasificación recibida en {duration:.2f}s")
            st.code(json.dumps(resp_json, indent=2, ensure_ascii=False), language="json")

def render_rag():
    with st.form("form_rag"):
        rag_id = st.selectbox(
            "Tipo de consulta",
            options=["rag_salud", "rag_laserum", "rag_teleasistencia", "rag_tarjeta65", "construccion", "out_of_scope"],
            help="Elige el dominio de conocimiento para la consulta."
        )

        question = st.text_area(
            "Pregunta",
            value="",
            placeholder="Escribe aquí tu pregunta",
            help="Haz una pregunta clara y específica."
        )

        k = st.number_input(
            "Número de documentos a recuperar (k)",
            min_value=1,
            max_value=20,
            value=5,
            help="Cuántos documentos quieres que se usen para responder."
        )

        submit_button_rag = st.form_submit_button("🚀 GO!")

    if submit_button_rag:
        if not question.strip():
            st.warning("⚠️ Por favor, escribe una pregunta para realizar la consulta.")
            return

        payload = {
            "id": rag_id,
            "question": question.strip(),
            "k": k  
        }

        with st.spinner("⌛ Enviando consulta RAG..."):
            start = time.time()
            resp_json, error = call_rag(payload)
            duration = time.time() - start

        if error:
            st.error(f"❌ {error}")
            return

        st.success(f"✅ Respuesta recibida en {duration:.2f}s")

        answer = resp_json.get("answer", "No hay respuesta")
        fragments = resp_json.get("fragments", [])

        escaped_answer = html.escape(answer).replace("\n", "<br>")

        with st.container():
            st.markdown("### Respuesta generada")
            st.markdown(
                f'<div class="respuesta-box">{escaped_answer}</div>',
                unsafe_allow_html=True
            )

        if fragments:
            st.markdown("### 📄 Fragmentos recuperados")
            for i, frag in enumerate(fragments, 1):
                text = frag.get("content") or frag.get("page_content", "⚠️ Fragmento vacío")
                st.markdown(
                    f'<div class="frag-card"><strong>Fragmento {i}:</strong><br>{html.escape(text).replace(chr(10), "<br>")}</div>',
                    unsafe_allow_html=True
                )

        with st.expander("JSON completo de la respuesta"):
            st.code(json.dumps(resp_json, indent=4, ensure_ascii=False), language="json")

def main():
    service = st.selectbox("Selecciona el servicio", ["Dynamic Classifier", "RAG + consultas"])
    if service == "Dynamic Classifier":
        render_dynamic_classifier()
    else:
        render_rag()

if __name__ == "__main__":
    main()
