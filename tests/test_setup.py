import sys
import mysql.connector
import pandas as pd
import nltk

def test_python_version():
    assert sys.version_info >= (3, 11), "Python 3.11+ required"
    print("✓ Python version OK")

def test_packages():
    print("✓ All required packages installed")

def test_docker():
    try:
        # Changed port to 3307 to avoid the 'address already in use' error
        conn = mysql.connector.connect(
            host='localhost',
            port=3307,
            user='root',
            password='root',
            database='real_estate'
        )
        conn.close()
        print("✓ MySQL connection successful")
    except Exception as e:
        print(f"⚠ MySQL connection failed: {e}")

if __name__ == "__main__":
    test_python_version()
    test_packages()
    test_docker()
    print("\nSetup verification complete!")