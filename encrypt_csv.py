# encrypt_csv.py
#!/usr/bin/env python3
"""
Simple script to encrypt a CSV file using the existing decript.py module. its for demo testing;
"""

import sys
from pathlib import Path

# Add the decryption module path to sys.path
from decription.decript import CSVEncryptor

def encrypt_csv_file(input_file: str, output_file: str = None) -> bool:
    """
    Encrypt a CSV file using the CSVEncryptor.
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output encrypted CSV file (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Set default output filename if not provided
        if output_file is None:
            input_path = Path(input_file)
            output_file = f"{input_path.stem}_encrypted{input_path.suffix}"
        
        # Initialize encryptor with the key
        encryptor = CSVEncryptor(key=b'MySecKey')  # Using the same key as your decryption
        
        print(f"Encrypting '{input_file}' to '{output_file}'...")
        
        # Encrypt the CSV file
        success = encryptor.encrypt_csv(input_file, output_file)
        
        if success:
            print(f"✅ Encryption completed successfully!")
            print(f"   Original file: {input_file}")
            print(f"   Encrypted file: {output_file}")
            return True
        else:
            print("❌ Encryption failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during encryption: {str(e)}")
        return False

if __name__ == "__main__":
    # Check if filename was provided as argument
    if len(sys.argv) < 2:
        print("Usage: python encrypt_csv.py <input_csv_file> [output_csv_file]")
        print("Example: python encrypt_csv.py user_csv.csv user_csv_encrypted.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Check if input file exists
    if not Path(input_file).exists():
        print(f"❌ Error: File '{input_file}' not found!")
        sys.exit(1)
    
    # Encrypt the file
    success = encrypt_csv_file(input_file, output_file)
    sys.exit(0 if success else 1)