import os
import tarfile
import tempfile

import dasdaemon.utils as utils

from test.unit import DaServerUnitTest


class UtilsArcCreateTarFileUnitTests(DaServerUnitTest):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        utils.fs.rm_rf(self.tmp)

    def test_create_tar_file_one_file(self):
        # Create random file with data
        tmpfile_path = os.path.join(self.tmp, 'file1.bin')
        utils.fs.write_random_file(tmpfile_path, 1024)

        # Create tarball of random file
        tarpath = tmpfile_path + '.tar'
        utils.arc.create_tar_file(tarpath, [tmpfile_path])

        # Verify tarball was created
        self.assertTrue(os.path.exists(tarpath))

        # Get contents of tarball
        contents = None
        with tarfile.open(tarpath) as tar:
            contents = tar.getnames()

        # Verify contents
        self.assertEqual(1, len(contents))
        self.assertEqual(tmpfile_path[1:], contents[0])

    def test_create_tar_file_multiple_files(self):
        # Create random files with data
        tmpfiles = [
            'file1.bin',
            'file2.bin',
            'file3.bin'
        ]
        for tmpfile in tmpfiles:
            utils.fs.write_random_file(os.path.join(self.tmp, tmpfile), 1024)

        # Create tarball of random files
        tarpath = os.path.join(self.tmp, 'tarfile.tar')
        utils.arc.create_tar_file(
            tarpath,
            [os.path.join(self.tmp, tmpfile) for tmpfile in tmpfiles]
        )

        # Verify tarball was created
        self.assertTrue(os.path.exists(tarpath))

        # Get contents of tarball
        contents = None
        with tarfile.open(tarpath) as tar:
            contents = tar.getnames()

        # Verify contents
        self.assertEqual(len(tmpfiles), len(contents))
        for i, tmpfile in enumerate(tmpfiles):
            tmpfile_path = os.path.join(self.tmp, tmpfile)
            self.assertEqual(tmpfile_path[1:], contents[i])

    def test_is_master_rar_file(self):
        master_rar_files = [
            'filename.part1.rar',
            'filename.part01.rar',
            'filename.part001.rar',
            'filename.part0001.rar',
            'filename.rar',
            'filename.000',
            'filename.part1.blah.rar'
        ]
        not_master_rar_files = [
            'filename.part1.rar.blah',
            'filename.part2.rar',
            'filename.part02.rar',
            'filename.part002.rar',
            'filename.r00',
            'filename.001'
        ]

        # Verify
        for filename in master_rar_files:
            self.assertTrue(utils.arc.is_master_rar_file(filename))
        for filename in not_master_rar_files:
            self.assertFalse(utils.arc.is_master_rar_file(filename))


class UtilsFsWriteRandomFileUnitTests(DaServerUnitTest):

    def setUp(self):
        self.tmpfile, self.tmpfile_path = tempfile.mkstemp()

    def tearDown(self):
        utils.fs.rm_rf(self.tmpfile_path)

    def test_write_random_file_small(self):
        # Write to file
        bytes = 10
        utils.fs.write_random_file(self.tmpfile_path, bytes)

        # Verify file size
        self.assertEqual(bytes, os.path.getsize(self.tmpfile_path))

    def test_write_random_file_large(self):
        # Write to file
        bytes = 12345
        utils.fs.write_random_file(self.tmpfile_path, bytes)

        # Verify file size
        self.assertEqual(bytes, os.path.getsize(self.tmpfile_path))


class UtilsFsJoinFilesUnitTests(DaServerUnitTest):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        utils.fs.rm_rf(self.tmpdir)

    def test_join_files_small_same_size(self):
        # Create source files
        bytes = 10
        source_files = [
            'test-join-files1.bin',
            'test-join-files2.bin',
            'test-join-files3.bin'
        ]
        sourcefile1 = os.path.join(self.tmpdir, source_files[0])
        sourcefile2 = os.path.join(self.tmpdir, source_files[1])
        sourcefile3 = os.path.join(self.tmpdir, source_files[2])

        utils.fs.write_random_file(os.path.join(self.tmpdir, source_files[0]), bytes)
        utils.fs.write_random_file(os.path.join(self.tmpdir, source_files[1]), bytes)
        utils.fs.write_random_file(os.path.join(self.tmpdir, source_files[2]), bytes)

        # Join files
        output_file = os.path.join(self.tmpdir, 'joined.bin')
        utils.fs.join_files(output_file, self.tmpdir, source_files)

        # Verify output file size
        self.assertEqual(bytes*3, os.path.getsize(output_file))

        # Verify file contents
        with open(sourcefile1, 'rb') as in_file:
            contents1 = in_file.read()
        with open(sourcefile2, 'rb') as in_file:
            contents2 = in_file.read()
        with open(sourcefile3, 'rb') as in_file:
            contents3 = in_file.read()

        md5_source = utils.hash.md5_bytes(contents1+contents2+contents3)
        md5_output = utils.hash.md5_file(output_file)
        self.assertEqual(md5_source, md5_output)


    def test_join_files_large_same_size(self):
        # Create source files
        bytes = 12345
        source_files = [
            'test-join-files1.bin',
            'test-join-files2.bin',
            'test-join-files3.bin'
        ]
        sourcefile1 = os.path.join(self.tmpdir, source_files[0])
        sourcefile2 = os.path.join(self.tmpdir, source_files[1])
        sourcefile3 = os.path.join(self.tmpdir, source_files[2])

        utils.fs.write_random_file(os.path.join(self.tmpdir, source_files[0]), bytes)
        utils.fs.write_random_file(os.path.join(self.tmpdir, source_files[1]), bytes)
        utils.fs.write_random_file(os.path.join(self.tmpdir, source_files[2]), bytes)

        # Join files
        output_file = os.path.join(self.tmpdir, 'joined.bin')
        utils.fs.join_files(output_file, self.tmpdir, source_files)

        # Verify output file size
        self.assertEqual(bytes*3, os.path.getsize(output_file))

        # Verify file contents
        with open(sourcefile1, 'rb') as in_file:
            contents1 = in_file.read()
        with open(sourcefile2, 'rb') as in_file:
            contents2 = in_file.read()
        with open(sourcefile3, 'rb') as in_file:
            contents3 = in_file.read()

        md5_source = utils.hash.md5_bytes(contents1+contents2+contents3)
        md5_output = utils.hash.md5_file(output_file)
        self.assertEqual(md5_source, md5_output)

    def test_join_files_different_sizes(self):
        # Create source files
        bytes1 = 12345
        bytes2 = 10
        bytes3 = 1000
        source_files = [
            'test-join-files1.bin',
            'test-join-files2.bin',
            'test-join-files3.bin'
        ]
        sourcefile1 = os.path.join(self.tmpdir, source_files[0])
        sourcefile2 = os.path.join(self.tmpdir, source_files[1])
        sourcefile3 = os.path.join(self.tmpdir, source_files[2])

        utils.fs.write_random_file(os.path.join(self.tmpdir, source_files[0]), bytes1)
        utils.fs.write_random_file(os.path.join(self.tmpdir, source_files[1]), bytes2)
        utils.fs.write_random_file(os.path.join(self.tmpdir, source_files[2]), bytes3)

        # Join files
        output_file = os.path.join(self.tmpdir, 'joined.bin')
        utils.fs.join_files(output_file, self.tmpdir, source_files)

        # Verify output file size
        self.assertEqual(bytes1+bytes2+bytes3, os.path.getsize(output_file))

        # Verify file contents
        with open(sourcefile1, 'rb') as in_file:
            contents1 = in_file.read()
        with open(sourcefile2, 'rb') as in_file:
            contents2 = in_file.read()
        with open(sourcefile3, 'rb') as in_file:
            contents3 = in_file.read()

        md5_source = utils.hash.md5_bytes(contents1+contents2+contents3)
        md5_output = utils.hash.md5_file(output_file)
        self.assertEqual(md5_source, md5_output)


class UtilsHashJoinFilesUnitTests(DaServerUnitTest):

    def test_md5_bytes(self):
        # Verify hash
        self.assertEqual('5d41402abc4b2a76b9719d911017c592', utils.hash.md5_bytes('hello'))
        self.assertEqual('d41d8cd98f00b204e9800998ecf8427e', utils.hash.md5_bytes(''))
        self.assertEqual('900150983cd24fb0d6963f7d28e17f72', utils.hash.md5_bytes('abc'))
        self.assertEqual('827ccb0eea8a706c4c34a16891f84e7b', utils.hash.md5_bytes('12345'))

    def test_md5_file(self):
        # Create temp file
        _, tmpfile_path = tempfile.mkstemp()

        # Write data to file
        with open(tmpfile_path, 'wb') as out_file:
            out_file.write('hello')

        # Verify hash
        self.assertEqual('5d41402abc4b2a76b9719d911017c592', utils.hash.md5_file(tmpfile_path))
