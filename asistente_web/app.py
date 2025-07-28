from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import uuid
import os
import copy
import mysql.connector


from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# === Configuración ===
PDF_PATH = "documentos/CONSTITUCION MEXICANA_.pdf"
CHROMA_DB_PATH = "./chroma_db"
EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_MODEL = "deepseek-r1:1.5b"

app = Flask(__name__)
app.secret_key = "supersecreto"  # Requerido para session

# === Cargar y preparar sistema RAG ===
print("📄 Cargando y procesando el PDF...")
loader = PyPDFLoader(PDF_PATH)
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(documents)

embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

if os.path.exists(CHROMA_DB_PATH) and os.listdir(CHROMA_DB_PATH):
    vectordb = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embeddings)
else:
    vectordb = Chroma.from_documents(chunks, embedding=embeddings, persist_directory=CHROMA_DB_PATH)
    vectordb.persist()

llm = OllamaLLM(model=OLLAMA_MODEL)

prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""
Responde en español claro y formal, utilizando solo la información del contexto.
Si la respuesta no está en el contexto, responde: "La Constitución no menciona esa información."

Contexto:
{context}

Pregunta:
{question}
"""
)

qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectordb.as_retriever(),
    return_source_documents=False,
    chain_type_kwargs={"prompt": prompt}
)

print("✅ Sistema cargado. Listo para recibir preguntas.")

# === RUTA PRINCIPAL ===
@app.route("/", methods=["GET", "POST"])
def index():
    if "historial" not in session:
        session["historial"] = []

    if "historial_chats" not in session:
        session["historial_chats"] = {}

    if request.method == "POST":
        pregunta = request.form.get("pregunta", "").strip()

        if pregunta:
            result = qa.invoke({"query": pregunta})
            respuesta = result["result"]

            if not session["historial"]:
                chat_id = str(uuid.uuid4())[:8]
                session["current_chat_id"] = chat_id
                session["historial"] = [{"pregunta": pregunta, "respuesta": respuesta}]
                session["historial_chats"][chat_id] = {
                    "titulo": pregunta[:30],  # título inicial (puedes personalizar esto)
                    "mensajes": copy.deepcopy(session["historial"])
                }
            else:
                session["historial"].append({"pregunta": pregunta, "respuesta": respuesta})
                chat_id = session.get("current_chat_id")
                if chat_id:
                    session["historial_chats"][chat_id]["mensajes"] = copy.deepcopy(session["historial"])

            session.modified = True
        else:
            session["historial"].append({"pregunta": "", "respuesta": "Pregunta no válida."})
            session.modified = True

    return render_template("index.html",
                           historial=session["historial"],
                           historial_chats=session["historial_chats"])


# === RUTA PARA INICIAR UN NUEVO CHAT ===
@app.route("/nuevo_chat")
def nuevo_chat():
    # Elimina el historial actual y el chat ID activo
    session["historial"] = []
    session.pop("current_chat_id", None)
    session.modified = True
    return redirect(url_for("index"))


# === RUTA PARA VER UN CHAT GUARDADO ===
@app.route("/chat/<chat_id>")
def ver_chat(chat_id):
    historial_chats = session.get("historial_chats", {})
    chat = historial_chats.get(chat_id)
    if chat:
        session["historial"] = copy.deepcopy(chat["mensajes"])
        session["current_chat_id"] = chat_id
    else:
        session["historial"] = []
        session.pop("current_chat_id", None)

    session.modified = True
    return redirect(url_for("index"))

# === RUTA PARA RENOMBRAR CHAT ===
@app.route("/renombrar/<chat_id>", methods=["POST"])
def renombrar_conversacion(chat_id):
    historial_chats = session.get("historial_chats", {})
    chat = historial_chats.get(chat_id)

    if not chat:
        return jsonify({"error": "Conversación no encontrada"}), 404

    nuevo_titulo = request.json.get("nuevo_titulo", "").strip()
    if not nuevo_titulo:
        return jsonify({"error": "Título vacío"}), 400

    chat["titulo"] = nuevo_titulo
    historial_chats[chat_id] = chat
    session["historial_chats"] = historial_chats
    session.modified = True

    return jsonify({"mensaje": "Título actualizado correctamente"}), 200

# === RUTA PARA ELIMINAR ===
# ✅ Ruta para eliminar una conversación
@app.route("/eliminar/<chat_id>", methods=["POST"])
def eliminar_conversacion(chat_id):
    historial_chats = session.get("historial_chats", {})
    if chat_id in historial_chats:
        del historial_chats[chat_id]
        session["historial_chats"] = historial_chats
        # Si estabas viendo ese chat, limpiamos el current
        if session.get("current_chat_id") == chat_id:
            session["current_chat_id"] = None
            session["historial"] = []
        session.modified = True
        return jsonify({"mensaje": "Conversación eliminada"}), 200
    return jsonify({"error": "Chat no encontrado"}), 404

# Conexión a la base de datos
conexion = mysql.connector.connect(
    host="localhost",
    user="paduk_admin",
    password="smartsite",
    database="asistente_db"
)

@app.route("/home")
def home():
    return "Conexión a MySQL exitosa"

if __name__ == "__main__":
    app.run(debug=True)