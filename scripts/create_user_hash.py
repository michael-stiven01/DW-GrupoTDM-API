import argparse
import sys
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def main():
    parser = argparse.ArgumentParser(description="Generar hash bcrypt para nuevo usuario.")
    parser.add_argument("--username", required=True, help="Nombre de usuario")
    parser.add_argument("--password", required=True, help="Contraseña a encriptar")
    parser.add_argument("--role", default="user", help="Rol del usuario (admin, user, etc)")
    
    args = parser.parse_args()
    
    hashed_password = pwd_context.hash(args.password)
    
    print("\n# ----------------------------------------------------")
    print("# Copia y pega el siguiente bloque en USERS_DB (dependencies.py):")
    print("# ----------------------------------------------------\n")
    print(f'    "{args.username}": {{')
    print(f'        "username": "{args.username}",')
    print(f'        "hashed_password": "{hashed_password}",')
    print(f'        "is_active": True,')
    print(f'        "role": "{args.role}"')
    print('    },')
    print("\n# ----------------------------------------------------\n")

if __name__ == "__main__":
    main()
