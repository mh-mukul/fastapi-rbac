import secrets
import argparse
from fastapi import Depends
from sqlalchemy.orm import Session

from config.database import get_db
from utils.auth import hash_password

from models import ApiKey, Department, User, Module, Permission


def generate_key(db: Session = Depends(get_db)):
    """Generates a new API key."""
    new_key = secrets.token_urlsafe(32)  # Generate a random key
    api_key = ApiKey(key=new_key)

    db.add(api_key)
    db.commit()

    print(f"New API key generated: {new_key}")


def create_department(db: Session = Depends(get_db)):
    """Creates a new department."""
    department_name = input("Enter department name: ")
    if not department_name:
        print("Department name is required.")
        return
    department = Department(name=department_name)
    db.add(department)
    db.commit()

    print(f"Department created: ID={department.id}, Name={department.name}")


def create_superuser(db: Session = Depends(get_db)):
    """Creates a new superuser."""
    name = input("Name: ")
    email = input("Email: ")
    phone = input("Phone: ")
    password = input("Password: ")

    if not name or not email or not phone or not password:
        print("All fields are required.")
        return
    hashed_password = hash_password(password)

    user = User(name=name, email=email, phone=phone,
                password=hashed_password, is_superuser=True)
    db.add(user)
    db.commit()

    print(f"Superuser created: ID={user.id}, Name={user.name}")


def create_module(db: Session = Depends(get_db)):
    """Creates a new module."""
    module_name = input("Enter module name: ")
    if not module_name:
        print("Module name is required.")
        return
    module = Module(name=module_name)
    db.add(module)
    db.commit()

    print(f"Module created: ID={module.id}, Name={module.name}")


def create_permission(db: Session = Depends(get_db)):
    """Creates a new permission."""
    permission_name = input("Enter permission name: ")
    module_id = input("Enter module ID: ")
    if not permission_name or not module_id:
        print("Permission name and module ID are required.")
        return
    permission = Permission(name=permission_name, module_id=module_id)
    db.add(permission)
    db.commit()

    print(f"Permission created: ID={permission.id}, Name={permission.name}")


def main():
    db = next(get_db())
    parser = argparse.ArgumentParser(description="Management Commands")
    parser.add_argument("command", help="Command to run",
                        choices=["generate_key", "create_department", "create_superuser", "create_module", "create_permission"])

    args = parser.parse_args()

    if args.command == "generate_key":
        generate_key(db)
    elif args.command == "create_department":
        create_department(db)
    elif args.command == "create_superuser":
        create_superuser(db)
    elif args.command == "create_module":
        create_module(db)
    elif args.command == "create_permission":
        create_permission(db)


if __name__ == "__main__":
    main()
