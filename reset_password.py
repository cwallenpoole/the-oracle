#!/usr/bin/env python3
"""
Password Reset Script for The Oracle I Ching App

Usage: python reset_password.py <username> <new_password>

This script allows administrators to reset user passwords.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.user import User

def reset_password(username, new_password):
    """Reset a user's password using the User model"""
    if len(new_password) < 6:
        print("Error: Password must be at least 6 characters long.")
        return False

    # Get user from database
    user = User.get_by_username(username)
    if not user:
        print(f"Error: User '{username}' not found.")
        return False

    # Change password
    if user.change_password(new_password):
        print(f"Success: Password for user '{username}' has been reset.")
        return True
    else:
        print(f"Error: Failed to reset password for user '{username}'.")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python reset_password.py <username> <new_password>")
        print("Example: python reset_password.py john_doe new_secure_password123")
        sys.exit(1)

    username = sys.argv[1]
    new_password = sys.argv[2]

    print(f"Resetting password for user: {username}")
    print("WARNING: This will permanently change the user's password.")

    confirm = input("Are you sure you want to proceed? (y/N): ").lower().strip()
    if confirm not in ['y', 'yes']:
        print("Operation cancelled.")
        sys.exit(0)

    if reset_password(username, new_password):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
