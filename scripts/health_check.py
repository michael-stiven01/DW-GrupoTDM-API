import os
import sys
import argparse
import urllib.request
import json
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Health Check DW_GrupoTDM API")
    parser.add_argument("--api-url", default=os.getenv("API_URL", "http://localhost:8000"), help="URL base de la API")
    args = parser.parse_args()
    
    overall_status = True
    print(f"=== Health Check DW_GrupoTDM API ===")
    
    # Check 1: API
    print(f"\n1. Verificando API ({args.api_url})...")
    try:
        req = urllib.request.Request(f"{args.api_url}/")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                if "status" in data:
                    print("✅ OK: La API está respondiendo correctamente.")
                else:
                    print("❌ FALLO: La API no retornó el JSON esperado.")
                    overall_status = False
            else:
                print(f"❌ FALLO: La API retornó status {response.getcode()}.")
                overall_status = False
    except Exception as e:
        print(f"❌ FALLO: No se pudo conectar a la API. Error: {e}")
        overall_status = False

    # Check 2: Database Connection
    print("\n2. Verificando conexión a la Base de Datos (pyodbc)...")
    try:
        driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
        server = os.getenv("DB_SERVER", "")
        database = os.getenv("DB_DATABASE", "DW_GrupoTdm")
        username = os.getenv("DB_USERNAME", "")
        password = os.getenv("DB_PASSWORD", "")
        
        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        
        conn = pyodbc.connect(conn_str, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        
        print("✅ OK: Conexión a la base de datos SQL Server exitosa.")
    except Exception as e:
        print(f"❌ FALLO: No se pudo conectar a la Base de Datos. Error: {e}")
        overall_status = False
        
    print("\n====================================")
    if overall_status:
        print("✅ TODOS LOS CHECKS PASARON CORRECTAMENTE.")
        sys.exit(0)
    else:
        print("❌ AL MENOS UN CHECK FALLÓ. REVISE LOS LOGS.")
        sys.exit(1)

if __name__ == "__main__":
    main()
