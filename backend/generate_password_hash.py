#!/usr/bin/env python3
"""
Generate bcrypt password hash for admin user
Usage: python generate_password_hash.py
"""
import bcrypt
import getpass

def generate_password_hash():
    password = getpass.getpass("Enter admin password: ")
    confirm = getpass.getpass("Confirm password: ")
    
    if password != confirm:
        print("Passwords don't match!")
        return
    
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    print(f"\nAdd this to your .env file:")
    print(f"ADMIN_PASSWORD_HASH={hashed.decode('utf-8')}")
    print(f"\nRemove ADMIN_PASSWORD from .env for security")

if __name__ == "__main__":
    generate_password_hash()