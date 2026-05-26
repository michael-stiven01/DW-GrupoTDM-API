import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

settings.enable_export = True

# --- Datos simulados para los mocks ---
MOCK_VIEWS = ["cls_Dim_Tiendas", "cls_dim_clientes_pos", "cls_Dim_Vendedores"]

MOCK_COLUMNS = [
    {"column_name": "rowid_bodega",    "data_type": "int",          "is_nullable": "NO"},
    {"column_name": "Nombre_Bodega",   "data_type": "varchar",      "is_nullable": "YES"},
    {"column_name": "MARCA",           "data_type": "varchar",      "is_nullable": "YES"},
    {"column_name": "Cod_Bodega",      "data_type": "varchar",      "is_nullable": "YES"},
    {"column_name": "rowid_dir3",      "data_type": "int",          "is_nullable": "YES"},
]

MOCK_ROW_1 = {"rowid_bodega": 1, "Nombre_Bodega": "Tienda Bogotá",   "MARCA": "TDM"}
MOCK_ROW_2 = {"rowid_bodega": 2, "Nombre_Bodega": "Tienda Medellín", "MARCA": "TDM"}

MOCK_PAGINATED_RESULT = {
    "data": [MOCK_ROW_1, MOCK_ROW_2],
    "total": 10,
    "limit": 5,
    "offset": 0,
    "view": "cls_Dim_Tiendas",
}

MOCK_PAGINATED_PAGE2 = {
    "data": [{"rowid_bodega": 3, "Nombre_Bodega": "Tienda Cali", "MARCA": "TDM"}],
    "total": 10,
    "limit": 5,
    "offset": 5,
    "view": "cls_Dim_Tiendas",
}

MOCK_CSV_DATA = [MOCK_ROW_1, MOCK_ROW_2]


# --- Fixtures ---

@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    response = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    return response.json()["access_token"]


# --- Tests de autenticación (sin DB) ---

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()


def test_login_success(client):
    response = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_failure(client):
    response = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401


def test_protected_without_token(client):
    response = client.get("/views/")
    assert response.status_code == 401


def test_invalid_token(client):
    headers = {"Authorization": "Bearer fake_token"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401


def test_auth_me(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "admin"


def test_invalid_view_name(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/views/.._invalid_name/schema", headers=headers)
    assert response.status_code == 422


# --- Tests de vistas (con DB mockeada) ---

def test_list_views(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    with patch("app.routers.views.view_service.get_available_views", return_value=MOCK_VIEWS):
        response = client.get("/views/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(v["name"] == "cls_Dim_Tiendas" for v in data)


def test_view_schema_tiendas(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    with patch("app.routers.views.view_service.get_view_columns", return_value=MOCK_COLUMNS):
        response = client.get("/views/cls_Dim_Tiendas/schema", headers=headers)
    assert response.status_code == 200
    columns = response.json()
    column_names = [c["column_name"] for c in columns]
    assert "rowid_bodega" in column_names
    assert "Nombre_Bodega" in column_names


def test_query_view_tiendas(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    with patch("app.routers.views.view_service.query_view", return_value=MOCK_PAGINATED_RESULT):
        response = client.get("/views/cls_Dim_Tiendas?limit=5", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data
    assert data["view"] == "cls_Dim_Tiendas"


def test_view_not_found(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    with patch("app.routers.views.view_service.query_view", side_effect=ValueError("Vista no encontrada")):
        response = client.get("/views/vista_que_no_existe", headers=headers)
    assert response.status_code == 404


def test_pagination(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    with patch("app.routers.views.view_service.query_view", return_value=MOCK_PAGINATED_RESULT):
        resp1 = client.get("/views/cls_Dim_Tiendas?limit=5&offset=0", headers=headers)
    with patch("app.routers.views.view_service.query_view", return_value=MOCK_PAGINATED_PAGE2):
        resp2 = client.get("/views/cls_Dim_Tiendas?limit=5&offset=5", headers=headers)
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["data"] != resp2.json()["data"]


def test_export_csv(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    mock_result = {
        "data": MOCK_CSV_DATA,
        "total": 2,
        "limit": 10000,
        "offset": 0,
        "view": "cls_Dim_Tiendas",
    }
    with patch("app.routers.views.view_service.query_view", return_value=mock_result):
        response = client.get("/views/cls_Dim_Tiendas/export?format=csv", headers=headers)
    assert response.status_code == 200
    assert "Content-Disposition" in response.headers
    assert "attachment" in response.headers["Content-Disposition"]
