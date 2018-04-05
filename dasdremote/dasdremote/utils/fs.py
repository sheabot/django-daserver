import errno
import os
import shutil

def mkdir_p(dir):
    try:
        # Create dir and all intermediate directories
        os.makedirs(dir)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(dir):
            # Ignore exceptions if dir already exists
            pass
        else:
            # Another exception occurred that shouldn't be ignored
            raise

def rm_rf(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)

def rm_dir_contents(dirpath):
    for root, dirs, files in os.walk(dirpath):
        for f in files:
            os.remove(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))

def write_random_file(path, size_bytes, block_size=16*1024):
    with open(path, 'wb') as f:
        while size_bytes > 0:
            if size_bytes < block_size:
                block_size = size_bytes
            f.write(os.urandom(block_size))
            size_bytes -= block_size
