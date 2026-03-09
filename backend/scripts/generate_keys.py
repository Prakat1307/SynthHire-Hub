
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import os

def generate_rsa_keys(output_dir="./keys"):

    os.makedirs(output_dir, exist_ok=True)
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    public_key = private_key.public_key()
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    private_key_path = os.path.join(output_dir, "jwt_private.pem")
    public_key_path = os.path.join(output_dir, "jwt_public.pem")
    
    with open(private_key_path, "wb") as f:
        f.write(private_pem)
    
    with open(public_key_path, "wb") as f:
        f.write(public_pem)
    
    print(f"✅ RSA keys generated successfully!")
    print(f"   Private key: {private_key_path}")
    print(f"   Public key: {public_key_path}")
    print("\n⚠️  Keep the private key secure and never commit it to version control!")

if __name__ == "__main__":
    generate_rsa_keys()