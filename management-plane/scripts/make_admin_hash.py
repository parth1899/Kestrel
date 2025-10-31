import sys
from utils.security import hash_password


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.make_admin_hash <password>")
        sys.exit(1)
    pw = sys.argv[1]
    print(hash_password(pw))


if __name__ == "__main__":
    main()
