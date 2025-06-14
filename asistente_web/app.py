from flask import Flask, render_template, request, session
import os
import re

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

    if request.method == "POST":
        pregunta = request.form["pregunta"]
        if pregunta.strip():
            result = qa.invoke({"query": pregunta})
            respuesta = result["result"]
            session["historial"].append({"pregunta": pregunta, "respuesta": respuesta})
            session.modified = True  # importante para que guarde los cambios
        else:
            session["historial"].append({"pregunta": pregunta, "respuesta": "Pregunta no válida."})

    return render_template("index.html", historial=session["historial"])

if __name__ == "__main__":
    app.run(debug=True)
