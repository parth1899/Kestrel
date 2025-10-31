import os
import sys

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.db import session_scope, init_database
from models import User
from utils.security import hash_password


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m scripts.create_user <username> <password> [role]")
        sys.exit(1)
    username = sys.argv[1]
    password = sys.argv[2]
    role = sys.argv[3] if len(sys.argv) > 3 else "viewer"

    init_database()
    with session_scope() as db:
        if db.query(User).filter(User.username == username).first():
            print("User already exists")
            sys.exit(1)
        u = User(username=username, password_hash=hash_password(password), role=role)
        db.add(u)
        print(f"Created user {username} with role {role}")


if __name__ == "__main__":
    main()
