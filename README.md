# 🛠️ Sistema de Control de Inventarios - Maestranzas Unidos S.A.

Este proyecto corresponde al desarrollo de un sistema web de control de inventarios para la empresa **Maestranzas Unidos S.A.**, desarrollado en el marco del módulo **Gestión Ágil de Proyectos**. Está construido con Django y sigue buenas prácticas de modularidad, uso de variables de entorno, despliegue y versionado.

---

## 🚀 Funcionalidades clave

- Registro y gestión de productos
- Seguimiento de movimientos de inventario (entrada, salida, ajustes)
- Control por lotes y fechas de vencimiento
- Roles de usuario: administrador, gestor, auditor
- Reportes básicos y alertas por stock bajo
- Sistema extensible y modular

---

## 🧰 Tecnologías utilizadas

- **Python 3.10+**
- **Django 5.2**
- **SQLite (para desarrollo)**
- **Bootstrap 5 + crispy-forms**
- **python-dotenv** (manejo de secretos)
- **Git + GitHub**

---

## 📁 Estructura del proyecto

```
inventario_maestranza/
├── inventario_maestranza/     # Configuración principal del proyecto
├── inventario/                # App principal para productos, stock, movimientos
├── usuarios/                  # App para autenticación personalizada
├── static/                    # Archivos estáticos
├── templates/                 # Plantillas globales
├── media/                     # Archivos cargados por usuarios
├── .env                       # Variables secretas (no se sube a Git)
├── manage.py
├── requirements.txt           # Dependencias del proyecto
└── README.md                  # Instrucciones y aclaraciones del proyecto
```

---

## 🛠️ Instrucciones de instalación y ejecución local

### 🔁 Clonar el repositorio

```bash
git clone https://github.com/javegaf/inventario_maestranza.git
cd inventario_maestranza
```

### 🐍 Crear entorno virtual

```bash
python -m venv env
# Activar entorno
env\Scripts\activate      # En Windows
source env/bin/activate   # En macOS/Linux
```

### 📦 Instalar dependencias

```bash
pip install -r requirements.txt
```

### 🔐 Crear archivo `.env`

En la raíz del proyecto:

```
SECRET_KEY= clave_secreta_entregada_por_el_admin
DEBUG=True
```

### 🧱 Ejecutar migraciones

```bash
python manage.py migrate
python manage.py createsuperuser  # (opcional)
```

### ▶️ Iniciar el servidor

```bash
python manage.py runserver
```

Abre en navegador: http://127.0.0.1:8000

---

## 📌 Notas adicionales

- Si una carpeta está vacía pero quieres mantenerla en Git, agrega un archivo `.gitkeep`.
- Usa `.env` para mantener fuera del repositorio tu clave secreta, base de datos y configuraciones sensibles.
- El archivo `.gitignore` ya está preparado para ignorar entorno virtual, base de datos, archivos temporales y secretos.

---

## 🤝 Créditos

Proyecto desarrollado por estudiantes de Ingeniería en Informática  
**Asignatura:** Gestión Ágil de Proyectos  
**Institución:** Duoc UC  
**Año:** 2025
