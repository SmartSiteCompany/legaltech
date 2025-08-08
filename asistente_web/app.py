from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash
from db import get_db_connection, get_dict_cursor
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


import uuid
import os
import copy
import mysql.connector


# === RAG y configuración del sistema ===
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

PDF_PATH = "documentos/CONSTITUCION MEXICANA_.pdf"
CHROMA_DB_PATH = "./chroma_db"
EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_MODEL = "deepseek-r1:1.5b"

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

# === Inicialización Flask ===
app = Flask(__name__)
app.secret_key = "supersecreto"

# Decorador para proteger rutas que requieren login
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Ruta login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        cursor.close()
        conexion.close()


        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
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

        # Validar que las contraseñas coincidan
        if password != confirm_password:
            flash('Las contraseñas no coinciden')
            return render_template('register.html')

        password_hash = generate_password_hash(password)

        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)

        # Verificar si usuario existe
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            flash('El usuario ya existe')
            return render_template('register.html')

        # Insertar usuario nuevo
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password_hash))
        conexion.commit()

        cursor.close()
        conexion.close()

        flash('Usuario creado exitosamente. Por favor inicia sesión.')
        return redirect(url_for('login'))

    return render_template('register.html')

# Ruta logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Ruta principal con sistema RAG y protegida con login
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    user_id = session.get("user_id")

    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    # Cargar chats del usuario para mostrar en el historial lateral
    cursor.execute("SELECT id, nombre_chat FROM chats WHERE user_id = %s ORDER BY fecha_creacion DESC", (user_id,))
    chats = cursor.fetchall()

    current_chat_id = session.get("current_chat_id")

    mensajes = []
    if current_chat_id:
        # Cargar mensajes del chat seleccionado
        cursor.execute("SELECT tipo, contenido FROM mensajes WHERE chat_id = %s ORDER BY fecha ASC", (current_chat_id,))
        mensajes = cursor.fetchall()

    if request.method == "POST":
        pregunta = request.form.get("pregunta", "").strip()

        if pregunta:
            # Obtiene la respuesta del sistema RAG
            respuesta = qa.invoke({"query": pregunta})["result"]

            if not current_chat_id:
                # Crear un nuevo chat
                cursor.execute(
                    "INSERT INTO chats (user_id, nombre_chat) VALUES (%s, %s)",
                    (user_id, pregunta[:30])
                )
                conexion.commit()
                current_chat_id = cursor.lastrowid
                session["current_chat_id"] = current_chat_id

            # Guardar mensaje del usuario
            cursor.execute(
                "INSERT INTO mensajes (chat_id, tipo, contenido) VALUES (%s, %s, %s)",
                (current_chat_id, 'usuario', pregunta)
            )
            # Guardar mensaje del asistente
            cursor.execute(
                "INSERT INTO mensajes (chat_id, tipo, contenido) VALUES (%s, %s, %s)",
                (current_chat_id, 'asistente', respuesta)
            )
            conexion.commit()

            # Recargar mensajes para mostrar la conversación actualizada
            cursor.execute("SELECT tipo, contenido FROM mensajes WHERE chat_id = %s ORDER BY fecha ASC", (current_chat_id,))
            mensajes = cursor.fetchall()

        else:
            flash("Pregunta no válida.")

    cursor.close()
    conexion.close()

    return render_template("ia.html", 
                           historial_chats=chats,  # lista de chats del usuario
                           historial=mensajes,     # mensajes del chat activo
                           current_chat_id=current_chat_id)

# Rutas para manejo de chats (nuevo, ver, renombrar, eliminar)
@app.route("/nuevo_chat")
@login_required
def nuevo_chat():
    session.pop("current_chat_id", None)
    return redirect(url_for("index"))

@app.route("/chat/<int:chat_id>")
@login_required
def ver_chat(chat_id):
    user_id = session.get("user_id")
    conexion = get_db_connection()
    cursor = conexion.cursor(dictionary=True)

    # Validar que el chat pertenece al usuario
    cursor.execute("SELECT id FROM chats WHERE id = %s AND user_id = %s", (chat_id, user_id))
    chat = cursor.fetchone()

    cursor.close()
    conexion.close()

    if chat:
        session["current_chat_id"] = chat_id
    else:
        flash("No tienes acceso a este chat.")
        session.pop("current_chat_id", None)

    return redirect(url_for("index"))

@app.route("/renombrar/<int:chat_id>", methods=["POST"])
@login_required
def renombrar_conversacion(chat_id):
    user_id = session.get("user_id")
    nuevo_titulo = request.json.get("nuevo_titulo", "").strip()
    if not nuevo_titulo:
        return jsonify({"error": "Título vacío"}), 400

    conexion = get_db_connection()
    cursor = conexion.cursor()

    # Validar que el chat es del usuario
    cursor.execute("SELECT id FROM chats WHERE id = %s AND user_id = %s", (chat_id, user_id))
    if not cursor.fetchone():
        cursor.close()
        conexion.close()
        return jsonify({"error": "Conversación no encontrada"}), 404

    # Actualizar título
    cursor.execute("UPDATE chats SET nombre_chat = %s WHERE id = %s", (nuevo_titulo, chat_id))
    conexion.commit()
    cursor.close()
    conexion.close()

    return jsonify({"mensaje": "Título actualizado correctamente"}), 200

@app.route("/eliminar/<int:chat_id>", methods=["POST"])
@login_required
def eliminar_conversacion(chat_id):
    user_id = session.get("user_id")
    conexion = get_db_connection()
    cursor = conexion.cursor()

    # Validar que el chat es del usuario
    cursor.execute("SELECT id FROM chats WHERE id = %s AND user_id = %s", (chat_id, user_id))
    if not cursor.fetchone():
        cursor.close()
        conexion.close()
        return jsonify({"error": "Chat no encontrado"}), 404

    # Borrar mensajes
    cursor.execute("DELETE FROM mensajes WHERE chat_id = %s", (chat_id,))
    # Borrar chat
    cursor.execute("DELETE FROM chats WHERE id = %s", (chat_id,))
    conexion.commit()

    cursor.close()
    conexion.close()

    # Si borraste el chat activo, limpiar sesión
    if session.get("current_chat_id") == chat_id:
        session.pop("current_chat_id", None)

    return jsonify({"mensaje": "Conversación eliminada"}), 200

# Ruta prueba conexión
@app.route("/home")
def home():
    return "Conexión a MySQL exitosa"

if __name__ == "__main__":
    app.run(debug=True)
