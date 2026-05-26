# API DW_GrupoTDM — Documentación del Proyecto

## 1. Resumen del Proyecto
- Nombre: DW GrupoTDM API
- Tipo: REST API privada
- Propósito: Consulta de vistas del Data Warehouse GrupoTDM
- Base de datos: SQL Server 16.0, base de datos DW_GrupoTDM
- Framework: FastAPI (Python 3.11)
- Autenticación: JWT (Bearer Token)

## 2. Stack Tecnológico
| Dependencia | Versión | Rol |
|---|---|---|
| fastapi | 0.111.0 | Framework web principal |
| uvicorn[standard] | 0.29.0 | Servidor ASGI para ejecutar la API |
| sqlalchemy | 2.0.30 | ORM y Query Builder para base de datos |
| pyodbc | 5.1.0 | Driver ODBC para conectar a SQL Server |
| python-dotenv | 1.0.1 | Manejo de variables de entorno |
| python-jose[cryptography] | 3.3.0 | Generación y validación de tokens JWT |
| passlib[bcrypt] | 1.7.4 | Hashing y verificación de contraseñas |
| pydantic-settings | 2.2.1 | Gestión de configuraciones tipadas |
| pydantic | 2.7.1 | Validación de datos y esquemas |
| slowapi | 0.1.9 | Rate limiting para los endpoints |

## 3. Estructura del Proyecto
```text
dw_grupotdm_api/
├── app/                        # Código principal de la aplicación
│   ├── __init__.py             # Inicializador del módulo app
│   ├── main.py                 # Punto de entrada y configuración de FastAPI
│   ├── config.py               # Configuraciones y carga de variables de entorno
│   ├── database.py             # Configuración de conexión y sesión de DB
│   ├── auth/                   # Lógica de autenticación y seguridad
│   │   ├── __init__.py
│   │   ├── jwt_handler.py      # Funciones para crear y decodificar JWT
│   │   └── dependencies.py     # Dependencias de seguridad (ej. validar token)
│   ├── routers/                # Controladores (Endpoints)
│   │   ├── __init__.py
│   │   ├── auth.py             # Endpoints de login y perfil
│   │   └── views.py            # Endpoints para consulta de vistas
│   ├── schemas/                # Modelos Pydantic (Request/Response)
│   │   ├── __init__.py
│   │   ├── auth.py             # Esquemas para login, token, usuario
│   │   └── views.py            # Esquemas para queries y datos
│   └── services/               # Lógica de negocio (Capa intermedia)
│       ├── __init__.py
│       └── view_service.py     # Lógica para interactuar con vistas y DB
├── tests/                      # Pruebas automatizadas (pytest)
│   └── __init__.py
├── scripts/                    # Scripts utilitarios (migraciones, tareas)
│   └── __init__.py
├── .env.example                # Plantilla de variables de entorno
├── .gitignore                  # Archivos a ignorar por git
├── Dockerfile                  # Definición de la imagen Docker de la API
├── docker-compose.yml          # Orquestación de servicios locales
├── requirements.txt            # Dependencias del proyecto Python
├── README.md                   # Instrucciones generales del repositorio
└── API_DW_GrupoTDM.md          # Documentación viva del proyecto
```

## 4. Variables de Entorno
| Variable | Descripción | Requerida |
|---|---|---|
| DB_SERVER | IP o Host del servidor SQL | Sí |
| DB_DATABASE | Nombre de la base de datos (DW_GrupoTDM) | Sí |
| DB_USERNAME | Usuario de la base de datos | Sí |
| DB_PASSWORD | Contraseña de la base de datos | Sí |
| DB_DRIVER | Driver ODBC a utilizar | Sí |
| JWT_SECRET_KEY | Clave secreta para firmar tokens | Sí |
| JWT_ALGORITHM | Algoritmo de encriptación (HS256) | Sí |
| JWT_EXPIRE_MINUTES | Tiempo de validez del token en minutos | Sí |
| API_TITLE | Título de la API para OpenAPI | No |
| API_VERSION | Versión de la API | No |
| API_HOST | Host donde corre el servidor | No |
| API_PORT | Puerto del servidor | No |
| ALLOWED_HOSTS | Orígenes permitidos (CORS) | No |
| ENVIRONMENT | Entorno (development, production) | No |
| ENABLE_EXPORT | Bandera para habilitar endpoint de exportación | No |

## 5. Endpoints Planificados
| Método | Ruta | Descripción | Autenticación | Estado |
|---|---|---|---|---|
| POST | `/auth/login` | Obtiene un token JWT | No | ✅ Implementado |
| GET | `/auth/me` | Retorna la información del usuario actual | Sí | ✅ Implementado |
| GET | `/auth/verify` | Verifica si el token es válido | Sí | ✅ Implementado |
| GET | `/views/` | Lista las vistas disponibles | Sí | ✅ Implementado |
| GET | `/views/{view_name}/schema` | Obtiene el esquema/columnas de la vista | Sí | ✅ Implementado |
| GET | `/views/{view_name}` | Consulta los datos con paginación/filtros | Sí | ✅ Implementado |
| GET | `/views/{view_name}/filter` | Obtiene valores únicos para filtros | Sí | ✅ Implementado |
| POST | `/views/{view_name}/query` | Consulta compleja mediante JSON body | Sí | ✅ Implementado |
| GET | `/views/{view_name}/export` | Exporta datos de la vista a CSV/Excel | Sí | ✅ Implementado |

## 6. Vistas Disponibles en la Base de Datos
- cls_dim_clientes_pos
- cls_Dim_Prodcutos
- cls_dim_terceros_cial
- cls_Dim_Tiendas
- cls_Dim_Transacciones
- cls_dw_stock_por_bodegas
- cls_h_Movs_inventarios
- cls_h_saldos_ref_bodega
- cls_h_saldos_sku_bodega
- cls_H_ventas_a
- cls_H_ventas_d
- cls_huella_tienda_xsku
- cls_inf_top_Ventas_referencias
- cls_inf_Venta_SKU_bodega
- cls_Ingesta_OC
- cls_items_barras
- cls_items_criterios
- cls_items_exensiones
- cls_STG_h_movs_inv_transaccion
- cls_t200_mm_terceros_distinct
- cls_t200_t015_terceros_contactos
- cls_t9740_pdv_clientes_distinct
- vw_Historial_Ingesta_H_ventas

## 7. Vista Principal (Primera en Implementar): cls_Dim_Tiendas
Columnas:
| Columna | Tipo | Nullable |
|---|---|---|
| rowid_bodega | int | NOT NULL |
| id_cia | smallint | NOT NULL |
| MARCA | varchar(8) | NOT NULL |
| id_bodega | char(5) | NOT NULL |
| Nombre_Bodega | varchar(40) | NOT NULL |
| id_co | char(3) | NOT NULL |
| nombre_co | varchar(40) | NOT NULL |
| id_clase_tpv | varchar(20) | NOT NULL |
| nombre_clase_tpv | varchar(50) | NOT NULL |
| contacto | varchar(50) | NOT NULL |
| direccion1 | varchar(40) | NOT NULL |
| direccion2 | varchar(40) | NOT NULL |
| direccion3 | varchar(40) | NOT NULL |
| Pais | varchar(44) | NULL |
| Depto | varchar(43) | NULL |
| Ciudad | varchar(44) | NULL |
| id_barrio | varchar(40) | NULL |
| telefono | varchar(20) | NOT NULL |
| fax | varchar(20) | NOT NULL |
| cod_postal | varchar(10) | NOT NULL |
| email | varchar(255) | NOT NULL |
| rowid_dir3 | int | NOT NULL |
| celular | varchar(50) | NULL |
| m2 | varchar(8000) | NULL |
| coordenadas | varchar(1) | NOT NULL |

## 8. Estado de Implementación
| Paso | Descripción | Estado |
|---|---|---|
| 1 | Scaffolding del proyecto | ✅ Completado |
| 2 | Conexión SQL Server + View Service | ✅ Completado |
| 3 | Autenticación JWT | ✅ Completado |
| 4 | Endpoints REST de vistas | ✅ Completado |
| 5 | Docker + Docker Compose | ⏳ Pendiente |
| 6 | Tests automatizados | ⏳ Pendiente |
| 7 | Seguridad y hardening | ⏳ Pendiente |
| 8 | Swagger personalizado + entrega final | ⏳ Pendiente |

## 9. Decisiones de Arquitectura
- REST sobre GraphQL: menor complejidad, adecuado para consultas de vistas
- FastAPI sobre Flask/Django: async nativo, Swagger automático, Pydantic integrado
- JWT sobre API Keys: estándar de industria, expiración configurable
- Endpoint genérico de vistas: soporta vistas futuras sin cambios de código
- SQLAlchemy text() con binding: previene SQL injection
- Caché en memoria para metadatos: reduce carga en INFORMATION_SCHEMA

## 10. Notas de Desarrollo
- **2026-05-26 (Paso 2):** Implementación de `pydantic-settings` para la configuración, y `SQLAlchemy` con `pyodbc` para conexión a SQL Server. Se definió un pool de 10 conexiones. Se desarrolló `view_service.py` con caché en memoria (TTL 5 mins) para `INFORMATION_SCHEMA` con el fin de mejorar latencias, y se aplicaron queries con parameters binding y corchetes `[ ]` para evitar SQL injection al leer vistas.
- **2026-05-26 (Paso 3):** Sistema de autenticación con JWT implementado.
  - **Estructura del payload JWT:** El token incluye `sub` (username del usuario), `role`, `iat` (marca de tiempo de creación), y `exp` (marca de tiempo de expiración).
  - **Tiempo de expiración:** Calculado según la variable `JWT_EXPIRE_MINUTES` de la configuración.
  - **Nuevos usuarios:** En esta iteración base, el sistema usa un diccionario estático `USERS_DB` en memoria en `dependencies.py` para persistencia de credenciales. Para registrar usuarios adicionales, se debe añadir el registro en este diccionario cifrando previamente su contraseña mediante bcrypt.
- **2026-05-26 (Paso 4):** Desarrollo de los endpoints REST para consultas a las vistas, completamente protegidos mediante la dependencia JWT.
  - **Validación robusta:** Se programó una capa de validación extra de `view_name` por medio de Expresiones Regulares (`^[a-zA-Z0-9_]+$`) que descarta strings maliciosos y los corta si exceden de 100 caracteres arrojando un 422, robusteciendo la prevención SQL Injection.
  - **Auditoría Sistemática:** Se configuró el logger nativo para registrar qué usuario consultó qué endpoint, vista, formato y cantidad de registros extraídos, lo que crea un registro histórico útil y transparente en un ambiente privado.
