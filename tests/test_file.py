import os
import tempfile
import GeoAnalyze
import pytest


@pytest.fixture(scope='class')
def file():

    yield GeoAnalyze.File()


@pytest.fixture(scope='class')
def core():

    yield GeoAnalyze.core.Core()


def test_delete_by_name(
    file
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        assert len(os.listdir(tmp_dir)) == 0
        file_path = os.path.join(tmp_dir, 'temporary.txt')
        with open(file_path, 'w') as write_file:
            write_file.write('GeoAnalyze')
        assert len(os.listdir(tmp_dir)) == 1
        output = file.delete_by_name(
            folder_path=tmp_dir,
            file_names=['temporary']
        )
        assert output == ['temporary.txt']
        assert len(os.listdir(tmp_dir)) == 0


def test_transfer_by_name(
    file
):

    # pass test
    with tempfile.TemporaryDirectory() as tmp1_dir:
        file_path = os.path.join(tmp1_dir, 'temporary.txt')
        with open(file_path, 'w') as write_file:
            write_file.write('GeoAnalyze')
        assert len(os.listdir(tmp1_dir)) == 1
        with tempfile.TemporaryDirectory() as tmp2_dir:
            assert len(os.listdir(tmp2_dir)) == 0
            output = file.transfer_by_name(
                src_folder=tmp1_dir,
                dst_folder=tmp2_dir,
                file_names=['temporary']
            )
            assert len(os.listdir(tmp2_dir)) == 1
            assert output == ['temporary.txt']

    # error test
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(Exception) as exc_info:
            file.transfer_by_name(
                src_folder=tmp_dir,
                dst_folder=tmp_dir,
                file_names=['temporary']
            )
        assert exc_info.value.args[0] == 'Source and destination folders must be different.'


def test_name_change(
    file
):

    # pass test
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, 'tmp_old.txt')
        with open(file_path, 'w') as write_file:
            write_file.write('GeoAnalyze')
        os.path.isfile(file_path) is True
        assert file.name_change(
            folder_path=tmp_dir,
            rename_map={'tmp_old': 'tmp_new'}
        ) == {'tmp_old.txt': 'tmp_new.txt'}
        os.path.isfile(file_path) is False


def test_copy_rename_and_paste(
    file
):

    # pass test
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, 'tmp_old.txt')
        with open(file_path, 'w') as write_file:
            write_file.write('GeoAnalyze')
        os.path.isfile(file_path) is True
        assert file.copy_rename_and_paste(
            src_folder=tmp_dir,
            dst_folder=tmp_dir,
            rename_map={'tmp_old': 'tmp_new'}
        ) == ['tmp_new.txt']
        os.path.isfile(os.path.join(tmp_dir, 'tmp_new.txt')) is True


def test_extract_specific_extension(
    file
):

    # pass test
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, 'teomporary.txt')
        with open(file_path, 'w') as write_file:
            write_file.write('GeoAnalyze')
        os.path.isfile(file_path) is True
        assert file.extract_specific_extension(
            folder_path=tmp_dir,
            extension='.txt'
        ) == ['teomporary.txt']


def test_github_action(
    core
):

    assert core._github_action(
        integer=2
    ) == '2'
