MAQUINA 1:

Lista de Comandos para la Instalación de la IA
PC PC1 - Usuario: desarrolladores
INSTALACIÓN Instalación de dependencias y Ollama
1.	Actualizar el sistema: sudo apt update && sudo apt upgrade -y
2.	Instalar curl:
sudo apt update && sudo apt install curl -y
3.	Instalar Ollama:
curl -fsSL https://ollama.com/install.sh | sh
4.	Ejecutar el modelo: ollama run deepseek-r1:1.5b
(Ctrl + D para cerrar la IA)
5.	Editar el servicio de Ollama: sudo systemctl edit ollama.service
Agregar dentro del bloque [Service]: Environment="OLLAMA_HOST=0.0.0.0"
6.	Recargar y reiniciar el servicio:
sudo systemctl daemon-reload && sudo systemctl restart ollama
DOCKER Instalación de Docker y configuración de Open WebUI
7.	Instalar Docker: curl --ssl https://get.docker.com | sh
8.	Crear carpeta para Open WebUI: mkdir -p ~/docker/openwebui
9.	Copiar a /opt: sudo cp -r ~/docker/openwebui /opt/
10.	Crear y editar compose.yaml: nano compose.yaml
Contenido del archivo: services: open-webui:
image: ghcr.io/open-webui/open-webui:main container_name: open-webui volumes:
-	./data:/app/backend/dataports: - "3000:8080" extra_hosts:
-	"host.docker.internal:host-gateway"restart: unless-stopped
PC Lista de Comandos para la Instalación de la IA
PC PC1 - Usuario: desarrolladores
INSTALACIÓN Instalación de dependencias y Ollama
1.	Actualizar el sistema: sudo apt update && sudo apt upgrade -y
2.	Instalar curl:
sudo apt update && sudo apt install curl -y
3.	Instalar Ollama:
curl -fsSL https://ollama.com/install.sh | sh
4.	Ejecutar el modelo: ollama run deepseek-r1:1.5b
(Ctrl + D para cerrar la IA)
5.	Editar el servicio de Ollama: sudo systemctl edit ollama.service
Agregar dentro del bloque [Service]: Environment="OLLAMA_HOST=0.0.0.0"
6.	Recargar y reiniciar el servicio:
sudo systemctl daemon-reload && sudo systemctl restart ollama
DOCKER Instalación de Docker y configuración de Open WebUI
7.	Instalar Docker: curl --ssl https://get.docker.com | sh
8.	Crear carpeta para Open WebUI: mkdir -p ~/docker/openwebui
9.	Copiar a /opt: sudo cp -r ~/docker/openwebui /opt/
10.	Crear y editar compose.yaml: nano compose.yaml
Contenido del archivo: services: open-webui:
image: ghcr.io/open-webui/open-webui:main container_name: open-webui volumes:
-	./data:/app/backend/dataports: - "3000:8080" extra_hosts:
-	"host.docker.internal:host-gateway"restart: unless-stopped
PC Abrir nueva terminal y levantar el contenedor
1.	Ctrl + Alt + T para abrir una nueva terminal.
2.	Verificar grupo: groups desarrolladores
3.	Ejecutar:
sudo docker compose up -d 4. Acceder a: http://localhost:3000
Inicio de sesión:
Nombre: desarrolladores
Correo: desarrolladores@100gmail.com
Contraseña: 123

MAQUINA 3: 
PC PC3 - Usuario: smart-site
INSTALACIÓN Instalación de dependencias y Ollama
13.	Actualizar el sistema: sudo apt update && sudo apt upgrade -y
14.	Instalar curl:
sudo apt update && sudo apt install curl -y
15.	Instalar Ollama:
curl -fsSL https://ollama.com/install.sh | sh
16.	Ejecutar el modelo: ollama run deepseek-r1:7b
(Ctrl + D para cerrar la IA)
17.	Editar servicio de Ollama: sudo systemctl edit ollama.service
Agregar:
Environment="OLLAMA_HOST=0.0.0.0"
18.	Recargar y reiniciar servicio: sudo systemctl daemon-reload && sudo systemctl restart ollama DOCKER Instalación de Docker y configuración de Open WebUI
19.	Instalar Docker: curl --ssl https://get.docker.com | sh
20.	Crear carpeta y copiar a /opt: mkdir -p ~/docker/openwebui sudo cp -r ~/docker/openwebui /opt/
21.	Crear y editar compose.yaml: nano compose.yaml
Contenido:
services: open-webui:
image: ghcr.io/open-webui/open-webui:main container_name: open-webui volumes:
-	./data:/app/backend/dataports: - "3000:8080" extra_hosts:
-	"host.docker.internal:host-gateway"restart: unless-stopped
PC Abrir nueva terminal y levantar el contenedor
1. Ctrl + Alt + T 2. Verificar grupo: groups smart-site
3. Ejecutar:
sudo docker compose up -d 4. Acceder a: http://localhost:3000
Inicio de sesión:
Nombre: smart-site
Correo: smartsite@100gmail.com
Contraseña: 123
