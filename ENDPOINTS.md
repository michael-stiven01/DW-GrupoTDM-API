# 📚 DW GrupoTDM API — Guía de Referencia

> **Base URL:** `http://localhost:8000`  
> **Versión:** `1.0.0`  
> **Autenticación:** Bearer Token (JWT)

---

## ⚙️ Información General

| Parámetro | Valor |
|---|---|
| **Duración del Token JWT** | `480 minutos` (8 horas) |
| **Algoritmo de firma** | `HS256` |
| **Límite de rate en Login** | `5 intentos / minuto` por IP |
| **Límite de rate en Vistas** | `100 requests / minuto` por IP |
| **Máximo de registros por consulta** | `5,000` (endpoints normales) |
| **Máximo de registros en exportación** | `10,000` |
| **Caché de lista de vistas** | `5 minutos` (TTL) |

---

## 🔐 Autenticación

Todos los endpoints de Vistas requieren enviar el token en el **header** de cada request:

```
Authorization: Bearer <tu_token_jwt>
```

El token expira automáticamente a los **480 minutos (8 horas)**. Cuando recibas un error `401 Unauthorized`, simplemente vuelve a hacer login para obtener uno nuevo.

---

## 🗂️ Endpoints

### 🟢 Health Check

#### `GET /`
Verifica que el servidor está activo. No requiere autenticación.

**Response:**
```json
{
  "api": "DW GrupoTDM API",
  "version": "1.0.0",
  "status": "healthy"
}
```

---

### 🔑 Auth — Autenticación

#### `POST /auth/login`
Genera un token JWT válido para acceder a todos los endpoints protegidos.

> ⚠️ **Límite:** 5 intentos por minuto por IP (protección anti fuerza bruta).

**Body (JSON):**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response exitoso:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5...",
  "token_type": "bearer",
  "expires_in": 28800
}
```
> `expires_in` está expresado en **segundos** (28800 = 8 horas).

---

#### `GET /auth/me`
Retorna la información del usuario actualmente autenticado (el que generó el token en uso).

**Response:**
```json
{
  "username": "admin",
  "role": "admin",
  "is_active": true
}
```

---

#### `GET /auth/verify`
Valida si el token que estás enviando sigue siendo válido.

**Response:**
```json
{
  "valid": true,
  "username": "admin"
}
```

---

### 🗃️ Views — Consulta de Vistas

> Todos los endpoints de esta sección requieren el header `Authorization: Bearer <token>`.

---

#### `GET /views/`
Lista todas las vistas disponibles en el Data Warehouse (`DW_GrupoTdm`, esquema `dbo`).

**Response:**
```json
[
  { "name": "cls_Dim_Tiendas",        "description": null },
  { "name": "cls_dim_clientes_pos",   "description": null },
  { "name": "cls_Dim_Vendedores",     "description": null }
]
```

---

#### `GET /views/{view_name}/schema`
Devuelve la estructura completa de una vista: nombre de columna, tipo de dato y si acepta nulos. Útil antes de filtrar para saber exactamente cómo se llaman las columnas.

**Ejemplo:**
`GET /views/cls_Dim_Tiendas/schema`

**Response:**
```json
[
  { "column_name": "rowid_bodega",  "data_type": "int",     "is_nullable": "NO" },
  { "column_name": "Nombre_Bodega", "data_type": "varchar", "is_nullable": "YES" },
  { "column_name": "MARCA",         "data_type": "varchar", "is_nullable": "YES" }
]
```

---

#### `GET /views/{view_name}`
Consulta paginada de todos los registros de una vista.

**Query Params opcionales:**

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `limit` | int | `100` | Cantidad de registros a retornar (máx. 5000) |
| `offset` | int | `0` | Número de registros a saltar (para paginar) |
| `order_by` | string | *(primera columna)* | Nombre de columna por la cual ordenar |

**Ejemplos de uso:**
```
# Primeros 100 registros (default)
GET /views/cls_Dim_Tiendas

# Traer solo 5 registros
GET /views/cls_Dim_Tiendas?limit=5

# Página 2: saltarse los primeros 100 y traer los siguientes 100
GET /views/cls_Dim_Tiendas?limit=100&offset=100

# Ordenados por nombre
GET /views/cls_Dim_Tiendas?order_by=Nombre_Bodega
```

**Response:**
```json
{
  "data": [ { "rowid_bodega": 1, "Nombre_Bodega": "Tienda Bogotá", ... } ],
  "total": 64,
  "limit": 100,
  "offset": 0,
  "view": "cls_Dim_Tiendas",
  "page": 1,
  "pages": 1
}
```

---

#### `GET /views/{view_name}/filter`
Filtra dinámicamente la vista usando columnas como parámetros en la URL. Equivalente a escribir un `WHERE col = 'valor'` en SQL, pero desde la URL.

> 💡 Solo puedes filtrar por columnas que existan en la vista (si usas una columna que no existe, retorna `422`).

**Ejemplos de uso:**
```
# Tiendas de una marca específica
GET /views/cls_Dim_Tiendas/filter?MARCA=TDM

# Tiendas en un departamento
GET /views/cls_Dim_Tiendas/filter?Depto=76-Valle del Cauca

# Combinación de filtros
GET /views/cls_Dim_Tiendas/filter?MARCA=TDM&Depto=76-Valle del Cauca&limit=10
```

---

#### `POST /views/{view_name}/query`
Alternativa a `/filter` cuando quieres enviar filtros complejos en el **body JSON** en lugar de la URL. Ideal para integraciones programáticas.

**Body (JSON):**
```json
{
  "filters": {
    "MARCA": "TDM",
    "Depto": "76-Valle del Cauca"
  },
  "limit": 20,
  "offset": 0,
  "order_by": "Nombre_Bodega"
}
```

---

#### `GET /views/{view_name}/export`
Exporta hasta **10,000 registros** de una vista en formato JSON o CSV. Ideal para análisis en Excel o PowerBI.

**Query Params:**

| Parámetro | Valores | Default |
|---|---|---|
| `format` | `json` o `csv` | `json` |

**Ejemplos:**
```
# Exportar como CSV (listo para abrir en Excel)
GET /views/cls_Dim_Tiendas/export?format=csv

# Exportar como JSON
GET /views/cls_Dim_Tiendas/export?format=json
```

> 💡 **Tip en Postman:** Cuando hagas el request con `format=csv`, ve a **"Save Response" → "Save to a file"** y guárdalo con extensión `.csv`. Excel lo abrirá directamente.

---

## 🔴 Códigos de Error Comunes

| Código | Significado | Solución |
|---|---|---|
| `401 Unauthorized` | Token inválido o expirado | Vuelve a hacer `POST /auth/login` |
| `404 Not Found` | La vista no existe en la DB | Verifica el nombre con `GET /views/` |
| `422 Unprocessable Entity` | Nombre de vista inválido o columna inexistente | Revisa el esquema con `/schema` |
| `429 Too Many Requests` | Superaste el rate limit | Espera un minuto e intenta de nuevo |
| `403 Forbidden` | Exportación deshabilitada en el servidor | Habilita `ENABLE_EXPORT=true` en `.env` |

---

## 📋 Colección Postman — Setup Rápido

1. Crea un **Environment** en Postman con estas variables:

| Variable | Valor inicial |
|---|---|
| `backend_url` | `http://localhost:8000` |
| `token_jwt` | *(déjalo vacío, se llenará solo)* |

2. En el request de Login (`POST /auth/login`), ve a la pestaña **"Scripts"** → **"Post-response"** y agrega este script para que el token se guarde automáticamente:

```javascript
const response = pm.response.json();
if (response.access_token) {
    pm.environment.set("token_jwt", response.access_token);
    console.log("✅ Token guardado automáticamente.");
}
```

3. En todos los demás requests, usa `{{token_jwt}}` en la pestaña **Authorization → Bearer Token**.
