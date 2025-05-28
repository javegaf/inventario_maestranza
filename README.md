# 🛠️ Sistema de Control de Inventarios  
## 📦 Maestranzas Unidos S.A.

Este es un sistema web que ayuda a **llevar el control de productos, stock y movimientos** dentro de una empresa. Fue desarrollado por estudiantes de Ingeniería en Informática como parte del ramo **Gestión Ágil de Proyectos**.

Está construido con **Django**, un framework que permite crear sitios web de forma organizada, segura y rápida.

---

## 🚀 ¿Qué se puede hacer con este sistema?

- ✅ Registrar productos y kits
- 🔄 Ver entradas, salidas y ajustes de productos
- 🗂️ Gestionar lotes y fechas de vencimiento
- 🔐 Asignar usuarios con diferentes roles (permisos)
- 📊 Ver reportes de movimientos y auditorías
- 🚨 Recibir alertas cuando falte stock
- ⚙️ Escalable y fácil de mantener

---

## 🧰 Tecnologías utilizadas

| Tecnología     | Para qué se usa                                  |
|----------------|--------------------------------------------------|
| Python 3.10+    | Lenguaje de programación del sistema             |
| Django 5.2      | Framework web para crear la aplicación           |
| SQLite          | Base de datos simple (ideal para pruebas)        |
| Bootstrap 5     | Diseñar páginas web que se vean bien             |
| crispy-forms    | Mejora el diseño de los formularios de Django    |
| python-dotenv   | Guardar claves y configuraciones de forma segura |
| Git + GitHub    | Llevar control de los cambios y colaborar        |

---

## 📁 Estructura del proyecto

```bash
inventario_maestranza/
├── carga_datos/               # Archivos con datos de ejemplo
├── env                        # Espacio aislado para instalar dependencias (entorno virtual de trabajo)
├── inventario/                # Lógica de productos, movimientos, stock
├── inventario_maestranza/     # Configuración general del proyecto
├── media/                     # Archivos que suben los usuarios
├── static/                    # Archivos como CSS e imágenes
├── templates/                 # Páginas HTML del sistema
├── usuarios/                  # Inicio de sesión y roles de usuarios
├── .env                       # Claves privadas (no se sube a GitHub)
├── .gitignore                 # Conjunto de cosas que se ignora a la hora de subirlo a GitHub (como el punto anterior)
├── db.sqlite3                 # Base de datos local
├── manage.py                  # Archivo principal para arrancar el sistema
├── README.md                  # Archivo que estas leyendo ahora que contiene las instrucciones a seguir
└── requirements.txt           # Lista de programas que necesita el sistema
```

---

## 🧑‍💻 ¿Cómo instalarlo y hacerlo funcionar?

A continuación, te explicamos cada paso **como si fuera la primera vez que haces esto**:

---

### 1️⃣ Descargar el proyecto (clonar repositorio)

Abre tu consola (CMD o Terminal) y escribe:

```bash
git clone https://github.com/javegaf/inventario_maestranza.git
```
```bash
cd inventario_maestranza
```

🔎 *Esto descarga el proyecto y entra a la carpeta.*

---

### 2️⃣ Crear un entorno virtual

Esto crea un espacio aislado para instalar los programas sin dañar tu computadora.

```bash
python -m venv env
```

Activar el entorno:

- En **Windows**:
```bash
env\Scripts\activate
```

- En **Linux/macOS**:
```bash
source env/bin/activate
```

🔎 *Verás que tu consola cambia, indicando que estás dentro del entorno virtual.*

---

### 3️⃣ Instalar los programas que el sistema necesita

```bash
pip install -r requirements.txt
```

🔎 *Esto instala Django y todas las demás herramientas necesarias.*

---

### 4️⃣ Crear el archivo `.env`

Este archivo guarda cosas privadas como claves. En la raíz del proyecto, crea un archivo llamado `.env` y escribe lo siguiente:

```env
SECRET_KEY='clave_super_secreta'
DEBUG=True
```

🔎 *La `'clave_super_secreta'` es la que genera django al generar los archivos por primera vez, debes pedirla al administrador del repositorio*

---

## ⚙️ Preparar la base de datos

Esto crea las tablas internas que el sistema necesita para guardar datos.

---

### 🧼 (Opcional) Borrar base de datos anterior

Solo si estás repitiendo el proceso:

```bash
del db.sqlite3  # Windows
```
```bash
rm db.sqlite3  # Linux/macOS
```

---

### 🧹 (Opcional) Borrar migraciones anteriores

Solo si las carpetas existen:

```bash
rmdir /s /q inventario\migrations
```
```bash
rmdir /s /q usuarios\migrations
```
🔎 *Este paso evita errores si estás rehaciendo la configuración desde cero.*

---

### 🛠️ Crear la estructura de la base de datos

```bash
python manage.py makemigrations usuarios inventario
```
```bash
python manage.py migrate
```

🔎 *Esto construye todas las tablas en la base de datos.*

---

## 📦 Cargar datos de ejemplo

Ejecuta estos comandos uno a uno:

```bash
python manage.py loaddata carga_datos/datos_usuarios.json
```
```bash
python manage.py loaddata carga_datos/datos_maestranza.json
```
```bash
python manage.py loaddata carga_datos/datos_complementarios_maestranza.json
```

🔎 *Esto llena la base con productos, movimientos, usuarios y más para probar el sistema.*

---

### 🔑 Crear un usuario administrador

```bash
python manage.py createsuperuser
```

🔎 *Escribe tu nombre, correo (puede quedar en blanco) y contraseña (puede ser corta, da igual) cuando te lo pida. Este usuario tendrá acceso completo al sistema.*

---

## ▶️ Iniciar el sistema

Levanta el servidor:

```bash
python manage.py runserver
```

Abre tu navegador y visita:

- Sitio principal: [http://127.0.0.1:8000](http://127.0.0.1:8000)  
- Panel de administración: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

🔎 *Inicia sesión con el usuario que creaste para gestionar todo el sistema.*

---

## 👥 Roles disponibles en el sistema

Cada usuario puede tener uno o más de estos roles:

- `administrador` – Control total del sistema
- `gestor` – Manejo de inventario y productos
- `auditor` – Revisión de movimientos e historial
- `logistica` – Entrada/salida de productos
- `comprador` – Control de compras/proveedores
- `produccion` – Consulta de stock para producción

---

## 🤝 ¿Cómo puedo ayudar o modificar este proyecto?

1. Crea tu propia copia del proyecto con **Fork**
2. Crea una nueva rama para tu mejora:
   ```bash
   git checkout -b mi-mejora
   ```
3. Haz cambios y guárdalos (commit)
4. Envía una solicitud de cambio (Pull Request)

---

## 🧾 Créditos

Este proyecto fue desarrollado por estudiantes de Ingeniería en Informática  
**Asignatura:** Gestión Ágil de Proyectos  
**Institución:** Duoc UC  
**Año:** 2025
