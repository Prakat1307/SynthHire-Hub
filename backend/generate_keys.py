import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def generate_keys():
    keys_dir = 'keys'
    if not os.path.exists(keys_dir):
        os.makedirs(keys_dir)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption())
    public_pem = key.public_key().public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
    with open(os.path.join(keys_dir, 'jwt_private.pem'), 'wb') as f:
        f.write(private_pem)
    with open(os.path.join(keys_dir, 'jwt_public.pem'), 'wb') as f:
        f.write(public_pem)
    print('Keys generated in ./keys/')
if __name__ == '__main__':
    generate_keys()