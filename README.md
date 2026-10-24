# Semillero-SOPE — Backend API REST

Backend desarrollado como parte del semillero de investigación del Instituto Tecnológico Metropolitano (ITM). Este proyecto expone una API REST construida con FastAPI para gestionar la lógica de negocio y las operaciones de la plataforma.

## Descripción
Este proyecto implementa el backend del sistema central para el semillero de investigación. Su arquitectura está diseñada para ofrecer un alto rendimiento, facilitar la escalabilidad y exponer puntos de enlace seguros para el consumo desde el frontend.

El sistema cuenta con una API REST documentada automáticamente con Swagger, accesible directamente desde el navegador en la ruta `/docs`.

## Tecnologías
| Tecnología | Uso |
| :--- | :--- |
| **Python** | Lenguaje principal del backend |
| **FastAPI** | Framework web de alto rendimiento para construir la API REST |
| **Uvicorn** | Servidor ASGI para la ejecución de la aplicación |
| **python-jose** | Generación y validación de tokens JWT |
| **bcrypt** | Hash seguro para el almacenamiento de contraseñas |
| **python-dotenv** | Gestión de configuraciones del entorno local |

## Instalación y configuración

### Requisitos previos
* Python 3.10 o superior
* pip

### Pasos
1. Clonar el repositorio:
   ```bash
   git clone https://github.com/Mafe-Palacio/Semillero-SOPE.git
   cd Semillero-SOPE
   ```
2. Crear y activar el entorno virtual:
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Ejecución

Para iniciar el servidor de la API REST, ejecuta el siguiente comando en la raíz del proyecto:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Accede a la documentación interactiva:
* **Swagger UI:** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`

## Seguridad

### Autenticación JWT
La API utiliza JSON Web Tokens (JWT) para proteger los endpoints. El flujo asegura las conexiones exigiendo que el token devuelto tras el inicio de sesión se incluya en el encabezado `Authorization: Bearer <token>` en cada petición a las rutas protegidas.

### Contraseñas
Las contraseñas de los usuarios se almacenan utilizando algoritmos de derivación de claves con `bcrypt`. Nunca se guardan contraseñas en texto plano.

### CORS
El middleware CORS está configurado de manera centralizada para controlar qué orígenes y clientes web están autorizados para consumir los recursos de la API.

## Elaborado por
* María Fernanda Palacio Agudelo
* Salomé Gil Chancí
