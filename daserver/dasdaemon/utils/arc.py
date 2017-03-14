"""Archive functions utility module"""
import os
import rarfile
import re
import tarfile


def create_tar_file(tarpath, paths, basenames=False):
    """Create tar file containing files and directories in paths"""
    with tarfile.open(tarpath, 'w') as tar:
        for path in paths:
            if basenames:
                # Store in archive with filename or directory name
                path = os.path.abspath(path)
                if os.path.isdir(path):
                    arcname = os.path.dirname(path)
                else:
                    arcname = os.path.basename(path)
                tar.add(path, arcname)
            else:
                # Store in archive as absolute path (without leading slash)
                tar.add(path)


def find_master_rar_files(dirpath):
    """Return list of master rar archives in a directory that RarFile needs
    to operate on.
    """
    master_files = []
    for root, _, files in os.walk(dirpath):
        for filename in files:
            if is_master_rar_file(filename):
                master_files.append(os.path.join(root, filename))
    return master_files

# Matches files with the following formats
#   filename.part#.rar
#   filename.part##.rar
#   ...
MASTER_RAR_FILE_REGEX = re.compile(r'^.*\.part([0-9]+)\.rar$')

def is_master_rar_file(filename):
    """Determine if `filename` matches the format for a master rar archive.
    There are several different formats of multi-volume rar files. This
    function will locate the correct one.
    """
    if filename.endswith('.000'):
        # Handle multi-volume rar (.000 is master):
        #   filename.000, filename.001, ...
        return True
    elif filename.endswith('.rar'):
        match = MASTER_RAR_FILE_REGEX.match(filename)
        if match:
            # Handle multi-volume rar (filename.part01.rar is master):
            #   filename.part01.rar, filename.part02.rar, ...
            part_number = int(match.group(1))
            return part_number == 1
        else:
            # Single-volume rar
            return True
    # Not a rar file
    return False
