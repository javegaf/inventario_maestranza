
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
- **python-dotenv**
- **Git + GitHub**

---

## 📁 Estructura del proyecto

```
inventario_maestranza/
├── inventario_maestranza/     # Configuración principal del proyecto
├── inventario/                # App principal: productos, stock, movimientos
├── usuarios/                  # App para autenticación y roles
├── static/                    # Archivos estáticos
├── templates/                 # Plantillas globales
├── media/                     # Archivos subidos por usuarios
├── carga_datos/               # Archivos JSON para poblar la base de datos
├── db.sqlite3                 # Base de datos (solo para desarrollo)
├── .env                       # Variables secretas
├── manage.py
└── requirements.txt
```

---

## 🛠️ Instalación y ejecución local

### 1️⃣ Clonar el repositorio

```bash
git clone https://github.com/javegaf/inventario_maestranza.git
cd inventario_maestranza
```

### 2️⃣ Crear y activar entorno virtual

```bash
python -m venv env
env\Scripts\activate   # Windows
# o en Linux/macOS:
# source env/bin/activate
```

### 3️⃣ Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4️⃣ Crear archivo `.env` con clave secreta

```env
SECRET_KEY=clave_super_secreta
DEBUG=True
```

---

## ⚙️ Inicializar base de datos

> Solo si es la primera vez:

```bash
rm db.sqlite3
rmdir /s /q inventario\migrations
rmdir /s /q usuarios\migrations
```

Crear migraciones y aplicarlas:

```bash
python manage.py makemigrations usuarios inventario
python manage.py migrate
```

Crear superusuario para manejar datos:

```bash
python manage.py createsuperuser
```

---

## ▶️ Ejecutar el servidor

```bash
python manage.py runserver
```

Ir a: http://127.0.0.1:8000  
Admin: http://127.0.0.1:8000/admin

---

## 📦 Cargar datos con archivos JSON

```bash
python manage.py loaddata carga_datos/datos_usuarios.json
python manage.py loaddata carga_datos/datos_maestranza.json
python manage.py loaddata carga_datos/datos_complementarios_maestranza.json
```

> Esto insertará usuarios, productos, proveedores, movimientos, auditorías, alertas y más.

---

## 🧪 Verificar e ingresar datos al sistema

### ✔️ Panel de Administración

1. Inicia el servidor
2. Visita: http://127.0.0.1:8000/admin
3. Usa:
   - Usuario: `super_usuario_creado`
   - Contraseña: `contraseña_que_creaste`

Puedes gestionar productos, kits, auditorías, stock, proyectos, etc.

---

## 👤 Roles disponibles

- `administrador`
- `gestor`
- `auditor`
- `logistica`
- `comprador`
- `produccion`

---

## 🤝 Cómo contribuir

1. Forkea el repositorio
2. Crea una rama: `git checkout -b nueva-funcionalidad`
3. Haz tus cambios y commitea
4. Abre un Pull Request

---

## 🧾 Créditos

Proyecto académico - Ingeniería en Informática  
**Asignatura:** Gestión Ágil de Proyectos  
**Institución:** Duoc UC  
**Año:** 2025
