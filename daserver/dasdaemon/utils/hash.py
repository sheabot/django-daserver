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
