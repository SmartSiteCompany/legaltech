# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from db import get_db_connection
from functools import wraps
import os

# LangChain
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# === Configuración general ===
app = Flask(__name__)
app.secret_key = "supersecreto"

# === Sistema RAG ===
PDF_PATH = "documentos/constitucionmexicana.pdf"
CHROMA_DB_PATH = "./chroma_db"
EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_MODEL = "deepseek-r1:1.5b"

print("📄 Cargando PDF y creando vectores...")
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

# === Decorador para rutas protegidas ===
def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped

# === Rutas de autenticación ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            flash('Usuario o contraseña incorrectos')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Las contraseñas no coinciden')
            return render_template('register.html')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            flash('El usuario ya existe')
            return render_template('register.html')

        password_hash = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password_hash))
        conn.commit()

        cursor.close()
        conn.close()

        flash('Usuario registrado. Inicia sesión.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# === Rutas principales ===
@app.route('/')
@login_required
def home():
    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, nombre_chat FROM chats WHERE user_id = %s ORDER BY fecha_creacion DESC", (user_id,))
    chats = cursor.fetchall()

    current_chat_id = session.get("current_chat_id")

    historial = []
    if current_chat_id:
        cursor.execute("SELECT tipo, contenido FROM mensajes WHERE chat_id = %s ORDER BY fecha ASC", (current_chat_id,))
        mensajes = cursor.fetchall()

        # Convertimos a formato pregunta/respuesta para tu index.html
        par = {}
        for m in mensajes:
            if m['tipo'] == 'usuario':
                par = {"pregunta": m['contenido']}
            elif m['tipo'] == 'asistente':
                par["respuesta"] = m['contenido']
                historial.append(par)

    cursor.close()
    conn.close()

    return render_template("index.html",
                           historial=historial,
                           chat_id=current_chat_id,
                           conversaciones={str(chat['id']): {"titulo": chat["nombre_chat"]} for chat in chats},
                           username=session['username'])

@app.route("/nuevo_chat")
@login_required
def nuevo_chat():
    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Crear nuevo chat con título por defecto y fecha actual
    cursor.execute(
        "INSERT INTO chats (user_id, nombre_chat, fecha_creacion) VALUES (%s, %s, NOW())",
        (user_id, "Nuevo chat")
    )
    conn.commit()

    nuevo_chat_id = cursor.lastrowid
    session["current_chat_id"] = nuevo_chat_id

    cursor.close()
    conn.close()

    return redirect(url_for("home"))


@app.route("/chat/<int:chat_id>", methods=["GET", "POST"])
@login_required
def ver_chat(chat_id):
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM chats WHERE id = %s AND user_id = %s", (chat_id, user_id))
    chat = cursor.fetchone()

    if not chat:
        cursor.close()
        conn.close()
        flash("No tienes acceso a este chat.")
        return redirect(url_for("home"))

    session["current_chat_id"] = chat_id

    if request.method == "POST":
        pregunta = request.form.get("pregunta", "").strip()
        if pregunta:
            respuesta = qa.invoke({"query": pregunta})["result"]

            # Guardar pregunta y respuesta
            cursor.execute("INSERT INTO mensajes (chat_id, tipo, contenido) VALUES (%s, %s, %s)", (chat_id, 'usuario', pregunta))
            cursor.execute("INSERT INTO mensajes (chat_id, tipo, contenido) VALUES (%s, %s, %s)", (chat_id, 'asistente', respuesta))
           

            # Verificar si el título del chat es "Nuevo chat"
            cursor.execute("SELECT nombre_chat FROM chats WHERE id = %s", (chat_id,))
            chat_info = cursor.fetchone()

            if chat_info and (chat_info["nombre_chat"] == "Nuevo chat" or not chat_info["nombre_chat"].strip()):
                cursor.execute("UPDATE chats SET nombre_chat = %s WHERE id = %s", (pregunta[:100], chat_id))


            conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("home"))

@app.route("/renombrar/<int:chat_id>", methods=["POST"])
@login_required
def renombrar_conversacion(chat_id):
    user_id = session['user_id']
    nuevo_titulo = request.json.get("nuevo_titulo", "").strip()
    if not nuevo_titulo:
        return jsonify({"error": "Título vacío"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM chats WHERE id = %s AND user_id = %s", (chat_id, user_id))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "Conversación no encontrada"}), 404

    cursor.execute("UPDATE chats SET nombre_chat = %s WHERE id = %s", (nuevo_titulo, chat_id))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"mensaje": "Título actualizado"}), 200

@app.route("/eliminar/<int:chat_id>", methods=["POST"])
@login_required
def eliminar_conversacion(chat_id):
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM chats WHERE id = %s AND user_id = %s", (chat_id, user_id))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "Chat no encontrado"}), 404

    cursor.execute("DELETE FROM mensajes WHERE chat_id = %s", (chat_id,))
    cursor.execute("DELETE FROM chats WHERE id = %s", (chat_id,))
    conn.commit()

    cursor.close()
    conn.close()

    if session.get("current_chat_id") == chat_id:
        session.pop("current_chat_id", None)

    return jsonify({"mensaje": "Conversación eliminada"}), 200

# === Ruta prueba conexión ===
@app.route("/inicio")
def inicio():
    return "Conexión a MySQL exitosa"

# === Ejecutar servidor ===
if __name__ == '__main__':
    app.run(debug=True)
