import pytest
import shapely
import geopandas
import os
import tempfile
import GeoAnalyze


@pytest.fixture(scope='class')
def shape():

    yield GeoAnalyze.Shape()


@pytest.fixture
def message():

    output = {
        'error_driver': 'Could not retrieve driver from the file path.'
    }

    return output


def test_columns(
    shape
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        # saving a GeoDataFrame
        file_path = os.path.join(tmp_dir, 'temporary.shp')
        gdf = geopandas.GeoDataFrame(
            data={'C1': [1], 'C2': [2], 'C3': [3]},
            geometry=[shapely.Point(1, 3)],
            crs='EPSG:4326'
        )
        gdf.to_file(file_path)
        # pass test for retaining columns
        retain_gdf = shape.columns_retain(
            input_file=file_path,
            retain_cols=['C1', 'C2'],
            output_file=file_path
        )
        assert list(retain_gdf.columns) == ['C1', 'C2', 'geometry']
        # pass test for deleting columns
        delete_gdf = shape.columns_delete(
            input_file=file_path,
            delete_cols=['C2'],
            output_file=file_path
        )
        assert list(delete_gdf.columns) == ['C1', 'geometry']
        # pass test for adding ID column
        id_gdf = shape.adding_id_column(
            input_file=file_path,
            column_name='ID',
            output_file=file_path
        )
        assert list(id_gdf.columns) == ['ID', 'C1', 'geometry']


def test_error_shapefile_driver(
    shape,
    message
):

    with pytest.raises(Exception) as exc_info:
        shape.columns_retain(
            input_file='input.shp',
            retain_cols=['C1'],
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']

    with pytest.raises(Exception) as exc_info:
        shape.columns_delete(
            input_file='input.shp',
            delete_cols=['C1'],
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']

    with pytest.raises(Exception) as exc_info:
        shape.adding_id_column(
            input_file='input.shp',
            column_name=['C1'],
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
