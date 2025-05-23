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
source env/bin/activate     # En macOS/Linux
```

### 📦 Instalar dependencias

```bash
pip install -r requirements.txt
```

### 🔐 Crear archivo `.env`

En la raíz del proyecto:

```
SECRET_KEY=clave_secreta_entregada_por_el_admin
DEBUG=True
```

---

### ⚙️ Inicializar la base de datos con modelo de usuario personalizado

> ⚠️ Si es la primera vez que trabajas con este proyecto (o vas a clonar desde cero), elimina las migraciones previas y la base de datos si ya existen para evitar conflictos con el modelo de usuario personalizado.

```bash
# Solo si es la primera vez (y no tienes datos importantes)
rm db.sqlite3
rmdir /s /q inventario\migrations
rmdir /s /q usuarios\migrations
```

> En macOS/Linux cambia `\` por `/` y usa `rm -r`.

---

### 🧱 Crear nuevas migraciones y aplicarlas

```bash
python manage.py makemigrations usuarios inventario
python manage.py migrate
python manage.py createsuperuser  # (opcional)
```

---

### ▶️ Iniciar el servidor

```bash
python manage.py runserver
```

Abre en navegador: http://127.0.0.1:8000

---

### 🔐 Acceder al panel de administración

Visita: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

Inicia sesión con el superusuario que creaste para gestionar:

- Productos
- Movimientos de inventario
- Proveedores
- Proyectos y asignaciones
- Usuarios con roles personalizados

---

### 👤 Roles disponibles en el sistema

El modelo `Usuario` tiene un campo `rol` con las siguientes opciones:

- `administrador`
- `gestor`
- `auditor`
- `logistica`
- `comprador`
- `produccion`

Estos roles pueden usarse para restringir funcionalidades y vistas específicas en el sistema (como vistas de stock, alertas, entradas/salidas, etc.).

---

### 📦 Cargar datos iniciales (opcional)

Si cuentas con archivos de datos de ejemplo (fixtures), puedes cargarlos con:

```bash
python manage.py loaddata nombre_archivo.json
```

Los fixtures pueden contener productos, proveedores, usuarios de prueba, etc.

---

### ⚠️ Nota para usuarios de PowerShell

Recuerda ejecutar comandos como:

```bash
python .\manage.py runserver
```

en lugar de `python manage.py runserver`, ya que PowerShell requiere `.\` para ejecutar archivos del directorio actual.

---

## 📌 Notas adicionales

- Si una carpeta está vacía pero quieres mantenerla en Git, agrega un archivo `.gitkeep`.
- Usa `.env` para mantener fuera del repositorio tu clave secreta, base de datos y configuraciones sensibles.
- El archivo `.gitignore` ya está preparado para ignorar entorno virtual, base de datos, archivos temporales y secretos.

---

## 🤝 Cómo contribuir

1. Haz un fork del repositorio
2. Crea una nueva rama: `git checkout -b nueva-funcionalidad`
3. Realiza tus cambios y haz commit: `git commit -m 'Agrega nueva funcionalidad'`
4. Sube tu rama: `git push origin nueva-funcionalidad`
5. Abre un Pull Request

Este proyecto es académico, pero sigue buenas prácticas de colaboración Git.

---

## 🧾 Créditos

Proyecto desarrollado por estudiantes de Ingeniería en Informática  
**Asignatura:** Gestión Ágil de Proyectos  
**Institución:** Duoc UC  
**Año:** 2025
