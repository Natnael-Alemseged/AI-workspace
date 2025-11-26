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
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    import base64
    
    print("=" * 60)
    print("VAPID Key Generator for Web Push Notifications")
    print("=" * 60)
    print()
    
    # Generate VAPID keys using cryptography library
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    
    # Get private key in PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    # Get public key in uncompressed format
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()
    
    # Convert to uncompressed format (0x04 + x + y)
    x = public_numbers.x.to_bytes(32, byteorder='big')
    y = public_numbers.y.to_bytes(32, byteorder='big')
    uncompressed = b'\x04' + x + y
    
    # Base64 URL-safe encode
    public_key_b64 = base64.urlsafe_b64encode(uncompressed).decode('utf-8').rstrip('=')
    
    print("✅ VAPID keys generated successfully!")
    print()
    print("Add these to your .env file:")
    print("-" * 60)
    print(f"VAPID_PRIVATE_KEY={private_pem}")
    print(f"VAPID_PUBLIC_KEY={public_key_b64}")
    print("-" * 60)
    print()
    print("⚠️  IMPORTANT:")
    print("- Keep the private key secret and never commit it to version control")
    print("- The public key will be shared with the frontend")
    print("- Both keys must be kept together (don't mix keys from different generations)")
    print()
    
except ImportError as e:
    print(f"❌ Error: Required library not installed: {e}")
    print()
    print("Install cryptography using:")
    print("  pip install cryptography")
    print()
    print("Or if using poetry:")
    print("  poetry add cryptography")
    print()
except Exception as e:
    print(f"❌ Error generating VAPID keys: {e}")
    import traceback
    traceback.print_exc()
    print()
