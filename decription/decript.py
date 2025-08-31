#!/usr/bin/env python3
"""
Real one to use 
CSV DES Encryption/Decryption modlue
--------------------------
This program encrypts and decrypts CSV files line by line using DES encryption.
It handles all edge cases and provides clear error messages.


Our code uses DES encryption to secure CSV files. DES is a symmetric encryption algorithm, which means the same secret key is used for both encryption and decryption.
We split each CSV line into blocks of 8 bytes, encrypt it using DES in ECB mode, and store the encrypted data as Base64 so it’s safe in CSV.
When decrypting, we reverse the process — Base64 decode → DES decrypt → remove padding → get the original CSV back

Takes your 64-bit blocks.

Applies 16 rounds of bit substitutions, shuffling, and XORing.

Produces encrypted 64-bit blocks.


Requirements:
- pip install pycryptodome


"""

import os
import sys
import csv
from typing import Optional, Tuple
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad, unpad
import base64


class CSVEncryptor:
    """
    A class to handle DES encryption and decryption of CSV files line by line.
    """
    
    def __init__(self, key: bytes = b'MySecKey'):  # 8-byte key for DES
        """
        Initialize the encryptor with a static key.
        
        Args:
            key (bytes): 8-byte DES key (default: b'MySecKey')
        """
        if len(key) != 8:
            raise ValueError("DES key must be exactly 8 bytes long")
        self.key = key
    
    def encrypt_line(self, line: str) -> str:
        """
        Encrypt a single line using DES encryption.
        
        Args:
            line (str): The line to encrypt
            
        Returns:
            str: Base64-encoded encrypted line
            
        Raises:
            Exception: If encryption fails
        """
        try:
            # Convert string to bytes using UTF-8 encoding
            line_bytes = line.encode('utf-8')
            
            # Create DES cipher in ECB mode
            cipher = DES.new(self.key, DES.MODE_ECB)
            """You tell DES to use ECB mode.

            ECB mode → encrypts each 8-byte block independently.

            """
            # Pad the data to be multiple of 8 bytes (DES block size)
            padded_data = pad(line_bytes, DES.block_size)
            
            # Encrypt the padded data
            encrypted_data = cipher.encrypt(padded_data)
            
            # Encode to base64 for safe storage in CSV
            encrypted_b64 = base64.b64encode(encrypted_data).decode('ascii')
            """After encryption, the result is binary garbage.

            If we put raw encrypted bytes into a CSV, it would break the file.

            So, we convert the encrypted bytes to a Base64 string → safe to store in a CSV."""
            return encrypted_b64
            
        except Exception as e:
            raise Exception(f"Failed to encrypt line: {str(e)}")
    
    def decrypt_line(self, encrypted_line: str) -> str:
        """
        Decrypt a single encrypted line.
        
        Args:
            encrypted_line (str): Base64-encoded encrypted line
            
        Returns:
            str: Decrypted original line
            
        Raises:
            Exception: If decryption fails
        """
        try:
            # Decode from base64
            encrypted_data = base64.b64decode(encrypted_line.encode('ascii'))
            
            # Create DES cipher in ECB mode
            cipher = DES.new(self.key, DES.MODE_ECB)
            
            # Decrypt the data
            decrypted_padded = cipher.decrypt(encrypted_data)
            
            # Remove padding
            decrypted_data = unpad(decrypted_padded, DES.block_size)
            
            # Convert back to string using UTF-8 encoding
            original_line = decrypted_data.decode('utf-8')
            """Base64 decode → Get back the original encrypted bytes.

                cipher.decrypt(...) → Use the same key to decrypt.

                unpad(...) → Remove padding we added earlier.

                decode('utf-8') → Convert bytes back to a string."""
            return original_line
            
        except Exception as e:
            raise Exception(f"Failed to decrypt line: {str(e)}")
    
    def encrypt_csv(self, input_file: str, output_file: str) -> bool:
        """
        Encrypt an entire CSV file row by row using proper CSV parsing.
        
        Args:
            input_file (str): Path to input CSV file
            output_file (str): Path to output encrypted CSV file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if input file exists
            if not os.path.exists(input_file):
                print(f"Error: Input file '{input_file}' not found.")
                return False
            
            # Check if input file is empty
            if os.path.getsize(input_file) == 0:
                print(f"Warning: Input file '{input_file}' is empty.")
                # Create empty output file
                with open(output_file, 'w', encoding='utf-8', newline='') as f:
                    pass
                return True
            
            rows_processed = 0
            
            with open(input_file, 'r', encoding='utf-8', newline='') as infile, \
                 open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                
                # Use CSV reader to properly handle multi-line fields
                csv_reader = csv.reader(infile)
                csv_writer = csv.writer(outfile)
                
                # Process each CSV row
                for row_num, row in enumerate(csv_reader, 1):
                    try:
                        # Handle empty rows
                        if not row:
                            csv_writer.writerow([])
                            continue
                        
                        # Encrypt each field in the row
                        encrypted_row = []
                        for field in row:
                            if field:  # Only encrypt non-empty fields
                                encrypted_field = self.encrypt_line(field)
                                encrypted_row.append(encrypted_field)
                            else:
                                encrypted_row.append('')  # Preserve empty fields
                        
                        # Write encrypted row to output
                        csv_writer.writerow(encrypted_row)
                        rows_processed += 1
                        
                    except Exception as e:
                        print(f"Error encrypting row {row_num}: {str(e)}")
                        return False
            
            print(f"Successfully encrypted {rows_processed} rows from '{input_file}' to '{output_file}'")
            return True
            
        except UnicodeDecodeError as e:
            print(f"Error: Unable to read file '{input_file}' - invalid UTF-8 encoding: {str(e)}")
            return False
        except PermissionError as e:
            print(f"Error: Permission denied accessing files: {str(e)}")
            return False
        except csv.Error as e:
            print(f"Error: Invalid CSV format in '{input_file}': {str(e)}")
            return False
        except Exception as e:
            print(f"Error encrypting CSV file: {str(e)}")
            return False
    
    def decrypt_csv(self, encrypted_file: str, output_file: str) -> bool:
        """
        Decrypt an encrypted CSV file back to original form using proper CSV parsing.
        
        Args:
            encrypted_file (str): Path to encrypted CSV file
            output_file (str): Path to output decrypted CSV file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if encrypted file exists
            if not os.path.exists(encrypted_file):
                print(f"Error: Encrypted file '{encrypted_file}' not found.")
                return False
            
            # Check if encrypted file is empty
            if os.path.getsize(encrypted_file) == 0:
                print(f"Warning: Encrypted file '{encrypted_file}' is empty.")
                # Create empty output file
                with open(output_file, 'w', encoding='utf-8', newline='') as f:
                    pass
                return True
            
            rows_processed = 0
            
            with open(encrypted_file, 'r', encoding='utf-8', newline='') as infile, \
                 open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                
                # Use CSV reader to properly handle the encrypted CSV structure
                csv_reader = csv.reader(infile)
                csv_writer = csv.writer(outfile)
                
                # Process each encrypted CSV row
                for row_num, row in enumerate(csv_reader, 1):
                    try:
                        # Handle empty rows
                        if not row:
                            csv_writer.writerow([])
                            continue
                        
                        # Decrypt each field in the row
                        decrypted_row = []
                        for field in row:
                            if field:  # Only decrypt non-empty fields
                                decrypted_field = self.decrypt_line(field)
                                decrypted_row.append(decrypted_field)
                            else:
                                decrypted_row.append('')  # Preserve empty fields
                        
                        # Write decrypted row to output
                        csv_writer.writerow(decrypted_row)
                        rows_processed += 1
                        
                    except Exception as e:
                        print(f"Error decrypting row {row_num}: {str(e)}")
                        return False
            
            print(f"Successfully decrypted {rows_processed} rows from '{encrypted_file}' to '{output_file}'")
            return True
            
        except UnicodeDecodeError as e:
            print(f"Error: Unable to read encrypted file '{encrypted_file}' - invalid encoding: {str(e)}")
            return False
        except PermissionError as e:
            print(f"Error: Permission denied accessing files: {str(e)}")
            return False
        except csv.Error as e:
            print(f"Error: Invalid CSV format in encrypted file '{encrypted_file}': {str(e)}")
            return False
        except Exception as e:
            print(f"Error decrypting CSV file: {str(e)}")
            return False
    
    def verify_files_match(self, file1: str, file2: str) -> bool:
        """
        Verify that two files have identical content.
        
        Args:
            file1 (str): Path to first file
            file2 (str): Path to second file
            
        Returns:
            bool: True if files match, False otherwise
        """
        try:
            with open(file1, 'r', encoding='utf-8') as f1, \
                 open(file2, 'r', encoding='utf-8') as f2:
                
                content1 = f1.read()
                content2 = f2.read()
                
                return content1 == content2
                
        except Exception as e:
            print(f"Error comparing files: {str(e)}")
            return False


def create_sample_csv(filename: str) -> bool:
    """
    Create a sample CSV file for demonstration.
    
    Args:
        filename (str): Name of the CSV file to create
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        sample_data = [
            ['Name', 'Age', 'City', 'Salary', 'Notes'],
            ['John Doe', '30', 'New York', '50000', 'Senior Developer'],
            ['Jane Smith', '25', 'San Francisco', '75000', 'Data Scientist'],
            ['María García', '28', 'Madrid', '45000', 'Contains ñ and á'],
            ['李小明', '35', '北京', '60000', 'Chinese characters test'],
            ['', '', '', '', ''],  # Empty row
            ['Special "Chars"', '40', 'Boston,MA', '80000', 'Quotes, commas & symbols!@#$%'],
            ['Multi\nLine', '32', 'Chicago', '55000', 'Contains\nnewline characters'],
        ]
        
        with open(filename, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(sample_data)
        
        print(f"Sample CSV file '{filename}' created successfully.")
        return True
        
    except Exception as e:
        print(f"Error creating sample CSV: {str(e)}")
        return False


def main():
    """
    Main function to demonstrate CSV encryption and decryption.
    """
    print("=== CSV DES Encryption/Decryption Tool ===\n")
    
    # File names
    original_file = "input.csv"
    encrypted_file = "encrypted.csv"
    decrypted_file = "decrypted.csv"
    
    # Initialize encryptor with static key
    encryptor = CSVEncryptor(key=b'MySecKey')  # 8-byte key
    
    print("Step 1: Creating sample CSV file...")
    if not create_sample_csv(original_file):
        return 1
    
    print("\nStep 2: Encrypting CSV file...")
    if not encryptor.encrypt_csv(original_file, encrypted_file):
        return 1
    
    print("\nStep 3: Decrypting CSV file...")
    if not encryptor.decrypt_csv(encrypted_file, decrypted_file):
        return 1
    
    print("\nStep 4: Verifying that original and decrypted files match...")
    if encryptor.verify_files_match(original_file, decrypted_file):
        print("✅ SUCCESS: Original and decrypted files match perfectly!")
    else:
        print("❌ ERROR: Original and decrypted files do not match!")
        return 1
    
    print("\n=== File Information ===")
    try:
        print(f"Original file size: {os.path.getsize(original_file)} bytes")
        print(f"Encrypted file size: {os.path.getsize(encrypted_file)} bytes")
        print(f"Decrypted file size: {os.path.getsize(decrypted_file)} bytes")
    except Exception as e:
        print(f"Error getting file sizes: {str(e)}")
    
    print("\n=== Sample Content Preview ===")
    try:
        print("Original CSV (first 5 lines):")
        with open(original_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 5:
                    break
                print(f"  {line.rstrip()}")
        
        print("\nEncrypted CSV (first 3 rows showing field-level encryption):")
        with open(encrypted_file, 'r', encoding='utf-8', newline='') as f:
            csv_reader = csv.reader(f)
            for i, row in enumerate(csv_reader):
                if i >= 3:
                    break
                # Show structure but truncate long encrypted strings for readability
                display_row = []
                for field in row:
                    if len(field) > 30:
                        display_row.append(field[:30] + "...")
                    else:
                        display_row.append(field)
                print(f"  Row {i+1}: {display_row}")
        
        print("\nDecrypted CSV (first 3 rows showing successful reconstruction):")
        with open(decrypted_file, 'r', encoding='utf-8', newline='') as f:
            csv_reader = csv.reader(f)
            for i, row in enumerate(csv_reader):
                if i >= 3:
                    break
                print(f"  Row {i+1}: {row}")
    
    except Exception as e:
        print(f"Error reading files for preview: {str(e)}")
    
    print("\n=== Demo Complete ===")
    print("Files generated:")
    print(f"  - {original_file} (original)")
    print(f"  - {encrypted_file} (encrypted)")
    print(f"  - {decrypted_file} (decrypted)")
    
    return 0


if __name__ == "__main__":
    """
    Command-line usage examples:
    
    1. Run the demo:
       python csv_encryptor.py
    
    2. Use as a module:
       from csv_encryptor import CSVEncryptor
       encryptor = CSVEncryptor(key=b'YourKey!')
       encryptor.encrypt_csv('input.csv', 'encrypted.csv')
       encryptor.decrypt_csv('encrypted.csv', 'decrypted.csv')
    """
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)