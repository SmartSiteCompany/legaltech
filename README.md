# legaltech

# 📚 LegalIA: Asistente Jurídico Inteligente SmartSite Co & Lexbit

**LegalIA/ SSCo-LEXBIT** es una aplicación experimental que integra modelos de lenguaje avanzados (LLMs), específicamente DeepSeek, para asistir en la interpretación y generación de texto jurídico. El proyecto toma como referencia documentos legales como la Constitución Mexicana para probar flujos de consulta legal automatizada.

## 🚀 Objetivo

Desarrollar un prototipo funcional que permita consultar, interpretar y generar contenido jurídico utilizando inteligencia artificial, con enfoque en accesibilidad, precisión y comprensión del lenguaje legal.

---

## 📌 Funcionalidades principales

- Consulta automatizada de la Constitución Mexicana.
- Interpretación de textos legales mediante prompts ajustables.
- Generación de respuestas jurídicas en lenguaje natural.
- Interfaz web para usuarios no técnicos.
- Backend modular con conexión a modelos locales o vía API.

---

## 🧠 Tecnologías utilizadas

- ⚙️ **DeepSeek API / Local Model**
- 🌐 **Python 3.12 / Flask / javascript** (Backend)
- 🎨 **HTML / CSS / javascript** (Frontend)
- 🧹 **NLP Preprocessing** (tokenización, limpieza)
- 🗂️ **Markdown / JSON** (estructura legal preprocesada)

---

## 📘 Documentación Proyecto LegalTech

Este documento describe paso a paso cómo instalar y ejecutar el proyecto en un sistema **Linux Ubuntu (terminal)**.

---

## 🔧 Preparación del entorno

1. Crear una carpeta llamada `dev`:
   ```bash
   mkdir dev
   cd dev
   ```

2. Clonar el repositorio:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   ```

3. Entrar en la carpeta del proyecto:
   ```bash
   cd legaltech
   ```

4. Entrar en la carpeta del asistente:
   ```bash
   cd asistente_web
   ```

---

## 🐍 Entorno virtual en Python

1. Instalar el paquete para entornos virtuales:
   ```bash
   sudo apt install python3-venv -y
   ```

2. Crear un entorno virtual:
   ```bash
   python3 -m venv smart_venv
   ```

3. Activar el entorno:
   ```bash
   source smart_venv/bin/activate
   ```

4. Actualizar **pip**:
   ```bash
   pip install --upgrade pip
   ```

5. Instalar dependencias del proyecto:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🤖 Instalación de Ollama

1. Instalar Ollama:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. Seleccionar modelos:
   ```bash
   ollama run deepseek-r1:8b
   ollama run nomic-embed-text
   ```

---

## 🗄️ Base de datos MySQL

1. Instalar MySQL:
   ```bash
   sudo apt update
   sudo apt install mysql-server -y
   ```

2. Entrar como root:
   ```bash
   sudo mysql
   ```

3. Crear base de datos y usuario:
   ```sql
   CREATE DATABASE asistente_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

   CREATE USER 'smartsite_admin'@'localhost' IDENTIFIED BY 'smartsite';
   GRANT ALL PRIVILEGES ON asistente_db.* TO 'smartsite_admin'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```

4. Conectarse como usuario:
   ```bash
   mysql -u smartsite_admin -p asistente_db
   ```

5. Crear tabla **usuarios**:
   ```sql
   CREATE TABLE IF NOT EXISTS users (
     id INT NOT NULL AUTO_INCREMENT,
     username VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL,
     password VARCHAR(255) COLLATE utf8mb4_unicode_ci NOT NULL,
     PRIMARY KEY (id),
     UNIQUE KEY username (username)
   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
   ```

6. Crear tabla **chats**:
   ```sql
   CREATE TABLE IF NOT EXISTS chats (
     id INT NOT NULL AUTO_INCREMENT,
     user_id INT DEFAULT NULL,
     nombre_chat VARCHAR(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
     fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
     PRIMARY KEY (id),
     KEY user_id (user_id),
     CONSTRAINT chats_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (id)
   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
   ```

7. Crear tabla **mensajes**:
   ```sql
   CREATE TABLE IF NOT EXISTS messages (
     id INT NOT NULL AUTO_INCREMENT,
     chat_id INT DEFAULT NULL,
     user_id INT DEFAULT NULL,
     contenido TEXT COLLATE utf8mb4_unicode_ci,
     fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
     PRIMARY KEY (id),
     KEY chat_id (chat_id),
     KEY user_id (user_id),
     CONSTRAINT messages_ibfk_1 FOREIGN KEY (chat_id) REFERENCES chats (id),
     CONSTRAINT messages_ibfk_2 FOREIGN KEY (user_id) REFERENCES users (id)
   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
   ```

8. Salir de MySQL:
   ```sql
   EXIT;
   ```

---

## ⚙️ Servicios de MySQL

- Ver estado:
  ```bash
  sudo service mysql status
  ```

- Encender servicio:
  ```bash
  sudo service mysql start
  ```

- Apagar servicio:
  ```bash
  sudo service mysql stop
  ```

---

## 🖥️ Configuración del proyecto

1. Abrir con Visual Studio Code:
   ```bash
   code .
   ```

2. En `app.py`, cambiar la versión del modelo descargado (ejemplo: `deepseek-r1:8b`).

3. En `db.py`, configurar las credenciales:
   ```python
   user = "smartsite_admin"
   password = "smartsite"
   ```

4. Instalar el conector de MySQL en el entorno virtual:
   ```bash
   pip install mysql-connector-python
   ```

---

## 🚀 Ejecutar el proyecto

Dentro del entorno virtual:
```bash
flask run
```

---

✅ Con esto tu proyecto queda listo para usarse.

