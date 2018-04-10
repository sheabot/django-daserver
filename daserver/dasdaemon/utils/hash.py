"""Hashing functions utility module"""
import hashlib


def md5_file(filepath, block_size=4096):
    """Calculate MD5 of file"""
    md5 = hashlib.md5()
    with open(filepath, 'rb') as in_file:
        while True:
            chunk = in_file.read(block_size)
            if not chunk:
                break
            md5.update(chunk)
    return md5.hexdigest()

def md5_bytes(bytestring):
    """Calculate MD5 of bytestring"""
    md5 = hashlib.md5()
    md5.update(bytestring)
    return md5.hexdigest()

def sha256_file(filepath, block_size=4096):
    """Calculate SHA256 of file"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as in_file:
        while True:
            chunk = in_file.read(block_size)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()

def sha256_bytes(bytestring):
    """Calculate SHA256 of bytestring"""
    sha256 = hashlib.sha256()
    sha256.update(bytestring)
    return sha256.hexdigest()
