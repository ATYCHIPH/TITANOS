import os
from pathlib import Path

def generate_dev_certs():
    cert_dir = Path("cert")
    cert_dir.mkdir(exist_ok=True)
    
    key_path = cert_dir / "key.pem"
    cert_path = cert_dir / "cert.pem"
    
    if key_path.exists() and cert_path.exists():
        print("Certificates already exist.")
        return
        
    print("Generating self-signed development certificates...")
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import hashes
        from cryptography.x509.oid import NameOID
        from cryptography import x509
        import datetime
        
        # Generate private key
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Generate certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
        ])
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
            critical=False,
        ).sign(key, hashes.SHA256())
        
        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))
            
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
            
        print(f"Successfully generated {key_path} and {cert_path}")
    except ImportError:
        print("Please install cryptography to generate certificates: pip install cryptography")

if __name__ == "__main__":
    generate_dev_certs()
