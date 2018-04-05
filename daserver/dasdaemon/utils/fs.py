"""File system operations utility module"""
import errno
import grp
import os
import pwd
import shutil


def mkdir_p(dirpath):
    """Emulate `mkdir -p` shell command"""
    try:
        os.makedirs(dirpath)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(dirpath):
            # Ignore directory already exists errors
            pass
        else:
            raise

def mkdir_chownmod(dirpath, owner=None, group=None, uid=None, gid=None, mode=None):
    """Make directory and set ownership and permissions"""
    mkdir_p(dirpath)
    if owner is not None:
        uid = get_uid_from_user(owner)
    if group is not None:
        gid = get_gid_from_group(group)
    if uid is not None:
        os.chown(dirpath, uid, -1)
    if gid is not None:
        os.chown(dirpath, -1, gid)
    if mode is not None:
        os.chmod(dirpath, mode)

def chownmod(dirpath, owner=None, group=None, uid=None, gid=None, dmode=None, fmode=None):
    """Recursively set ownership and permissions for a directory contents"""
    if owner is not None:
        uid = get_uid_from_user(owner)
    if group is not None:
        gid = get_gid_from_group(group)

    for root, dirs, files in os.walk(dirpath):
        # Directories
        for dname in dirs:
            path = os.path.join(root, dname)
            if uid is not None:
                os.chown(path, uid, -1)
            if gid is not None:
                os.chown(path, -1, gid)
            if dmode is not None:
                os.chmod(path, dmode)
        # Files
        for fname in files:
            path = os.path.join(root, fname)
            if uid is not None:
                os.chown(path, uid, -1)
            if gid is not None:
                os.chown(path, -1, gid)
            if fmode is not None:
                os.chmod(path, fmode)

def rm_rf(path):
    """Emulate `rm -rf` shell command"""
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)

def write_random_file(filepath, size_bytes, block_size=4096):
    """Write random file with bytes from os.urandom"""
    with open(filepath, 'wb') as output_file:
        while size_bytes > 0:
            if size_bytes < block_size:
                block_size = size_bytes
            output_file.write(os.urandom(block_size))
            size_bytes -= block_size

def split_file(filepath, output_dir, split_size=4096):
    """Split file into multiple files of the same size"""
    if not os.path.isfile(filepath):
        raise ValueError('filepath is not a file')
    basename = os.path.basename(filepath)

    part_num = 0
    split_files = []
    with open(filepath, 'rb') as in_file:
        while True:
            # Read file chunk
            chunk = in_file.read(split_size)
            if not chunk:
                break

            # Get split file path
            split_filepath = os.path.join(
                output_dir,
                '%s.%04d' % (basename, part_num)
            )

            # Write chunk to split file
            with open(split_filepath, 'wb') as out_file:
                out_file.write(chunk)

            # Add split file to list
            split_files.append(os.path.basename(split_filepath))

            # Increment part number for split file name
            part_num += 1

    return split_files

def join_files(output_filename, source_dir, source_filenames):
    """Open output file for binary writing, loop
    through source files in order, and write
    their contents to output file
    """
    with open(output_filename, 'wb') as output_file:
        for filename in source_filenames:
            filepath = os.path.join(source_dir, filename)
            with open(filepath, 'rb') as input_file:
                shutil.copyfileobj(input_file, output_file)

def get_user_from_uid(uid):
    """Get username from user ID"""
    return pwd.getpwuid(uid)[0]

def get_uid_from_user(user):
    """Get user ID from username"""
    return pwd.getpwnam(user)[2]

def get_ids_from_user(user):
    """Get user ID and group ID from username"""
    uid = pwd.getpwnam(user)[2]
    gid = pwd.getpwnam(user)[3]
    return uid, gid

def get_group_from_gid(gid):
    """Get group name from group ID"""
    return grp.getgrgid(gid)[0]

def get_gid_from_group(user):
    """Get group ID from group name"""
    return grp.getgrnam(user)[2]

def get_ownership_ids(path):
    """Get owner and group ID of file or directory"""
    stat = os.stat(path)
    return stat.st_uid, stat.st_gid

def get_ownership_names(path):
    """Get owner username and group name of file or directory"""
    uid, gid = get_ownership_ids(path)
    return get_user_from_uid(uid), get_group_from_gid(gid)

def get_mode(path):
    """Get file or directory mode (as integer)"""
    return int(oct(os.stat(path).st_mode & 0o777), 8)
