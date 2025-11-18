"""
Seed script to create an initial admin user in the database.
Run this after running migrations to create your first admin user.

Usage:
    python seed_admin.py
"""

import asyncio
import sys
from getpass import getpass
from pathlib import Path

# Ensure the project root is on sys.path so `app` imports work when running directly
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.db import AsyncSessionLocal
from app.models.user import User, UserRole


async def create_admin_user(
    email: str,
    password: str,
    full_name: str = None
) -> User:
    """Create an admin user in the database."""
    async with AsyncSessionLocal() as session:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"❌ User with email {email} already exists!")
            
            # Ask if they want to promote to admin
            promote = input("Do you want to promote this user to admin? (y/n): ")
            if promote.lower() == 'y':
                existing_user.role = UserRole.ADMIN
                existing_user.is_superuser = True
                existing_user.is_verified = True
                await session.commit()
                print(f"✅ User {email} promoted to admin!")
                return existing_user
            else:
                print("❌ Operation cancelled.")
                return None
        
        # Create new admin user
        hashed_password = get_password_hash(password)
        
        admin_user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=UserRole.ADMIN,
            is_active=True,
            is_superuser=True,
            is_verified=True
        )
        
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        
        print(f"✅ Admin user created successfully!")
        print(f"   Email: {admin_user.email}")
        print(f"   Role: {admin_user.role.value}")
        print(f"   ID: {admin_user.id}")
        
        return admin_user


async def seed_multiple_admins():
    """Seed multiple predefined admin users."""
    admins = [
        {
            "email": "admin@armadaden.com",
            "password": "Admin@123",  # Change this!
            "full_name": "System Administrator"
        },
        # Add more admins here if needed
    ]
    
    print("🌱 Seeding admin users...\n")
    
    for admin_data in admins:
        await create_admin_user(**admin_data)
        print()


async def interactive_seed():
    """Interactive mode to create admin user."""
    print("=" * 60)
    print("🌱 Admin User Seeding Script")
    print("=" * 60)
    print()
    
    email = input("Enter admin email: ").strip()
    if not email:
        print("❌ Email is required!")
        return
    
    full_name = input("Enter full name (optional): ").strip() or None
    
    password = getpass("Enter password: ")
    if not password:
        print("❌ Password is required!")
        return
    
    password_confirm = getpass("Confirm password: ")
    if password != password_confirm:
        print("❌ Passwords do not match!")
        return
    
    print()
    print("Creating admin user...")
    await create_admin_user(email, password, full_name)


async def promote_existing_user():
    """Promote an existing user to admin."""
    print("=" * 60)
    print("👑 Promote User to Admin")
    print("=" * 60)
    print()
    
    email = input("Enter user email to promote: ").strip()
    if not email:
        print("❌ Email is required!")
        return
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User with email {email} not found!")
            return
        
        if user.role == UserRole.ADMIN:
            print(f"ℹ️  User {email} is already an admin!")
            return
        
        user.role = UserRole.ADMIN
        user.is_superuser = True
        user.is_verified = True
        await session.commit()
        
        print(f"✅ User {email} promoted to admin!")
        print(f"   ID: {user.id}")
        print(f"   Role: {user.role.value}")


async def list_admins():
    """List all admin users."""
    print("=" * 60)
    print("👥 Current Admin Users")
    print("=" * 60)
    print()
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.role == UserRole.ADMIN)
        )
        admins = result.scalars().all()
        
        if not admins:
            print("No admin users found.")
            return
        
        for admin in admins:
            print(f"📧 {admin.email}")
            print(f"   Name: {admin.full_name or 'N/A'}")
            print(f"   ID: {admin.id}")
            print(f"   Superuser: {admin.is_superuser}")
            print(f"   Verified: {admin.is_verified}")
            print()


def print_menu():
    """Print the main menu."""
    print()
    print("=" * 60)
    print("🌱 Admin User Management")
    print("=" * 60)
    print()
    print("1. Create new admin user (interactive)")
    print("2. Promote existing user to admin")
    print("3. List all admin users")
    print("4. Seed predefined admins")
    print("5. Exit")
    print()


async def main():
    """Main function."""
    while True:
        print_menu()
        choice = input("Select an option (1-5): ").strip()
        print()
        
        if choice == "1":
            await interactive_seed()
        elif choice == "2":
            await promote_existing_user()
        elif choice == "3":
            await list_admins()
        elif choice == "4":
            await seed_multiple_admins()
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
