import hashlib


def compute_md5(path):
    md5 = hashlib.md5()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(16*1024)
            if not chunk:
                break
            md5.update(chunk)
    return md5.hexdigest()

def compute_sha256(path):
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(16*1024)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()
