"""
Script to generate VAPID keys for Web Push notifications.

Usage:
    python scripts/generate_vapid_keys.py

This will generate a new pair of VAPID keys (public and private)
that can be used for Web Push notifications.

Add the generated keys to your .env file:
    VAPID_PRIVATE_KEY=<generated_private_key>
    VAPID_PUBLIC_KEY=<generated_public_key>
"""

try:
    from pywebpush import webpush
    
    print("=" * 60)
    print("VAPID Key Generator for Web Push Notifications")
    print("=" * 60)
    print()
    
    # Generate VAPID keys
    vapid_keys = webpush.generate_vapid_keys()
    
    print("✅ VAPID keys generated successfully!")
    print()
    print("Add these to your .env file:")
    print("-" * 60)
    print(f"VAPID_PRIVATE_KEY={vapid_keys['private_key']}")
    print(f"VAPID_PUBLIC_KEY={vapid_keys['public_key']}")
    print("-" * 60)
    print()
    print("⚠️  IMPORTANT:")
    print("- Keep the private key secret and never commit it to version control")
    print("- The public key will be shared with the frontend")
    print("- Both keys must be kept together (don't mix keys from different generations)")
    print()
    
except ImportError:
    print("❌ Error: pywebpush is not installed")
    print()
    print("Install it using:")
    print("  pip install pywebpush")
    print()
    print("Or if using poetry:")
    print("  poetry add pywebpush")
    print()
except Exception as e:
    print(f"❌ Error generating VAPID keys: {e}")
    print()
