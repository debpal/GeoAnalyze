import pytest
import os
import tempfile
import GeoAnalyze


@pytest.fixture(scope='class')
def file():

    yield GeoAnalyze.File()


def test_file_delete_by_name(
    file
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        assert len(os.listdir(tmp_dir)) == 0
        file_path = os.path.join(tmp_dir, 'temporary.txt')
        with open(file_path, 'w') as write_file:
            write_file.write('temporary')
        assert len(os.listdir(tmp_dir)) == 1
        output = file.delete_by_name(
            folder_path=tmp_dir,
            file_names=['temporary']
        )
        assert output == "List of deleted files: ['temporary.txt']."
        assert len(os.listdir(tmp_dir)) == 0
