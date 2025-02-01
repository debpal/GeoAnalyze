import os
import tempfile
import geopandas
import shapely
import GeoAnalyze
import pytest


@pytest.fixture(scope='class')
def shape():

    yield GeoAnalyze.Shape()


@pytest.fixture
def message():

    output = {
        'error_driver': 'Could not retrieve driver from the file path.'
    }

    return output


@pytest.fixture
def example_gdf():

    gdf = geopandas.GeoDataFrame(
        data={'C1': [1], 'C2': [2], 'C3': [3]},
        geometry=[shapely.box(0, 0, 1, 1)],
        crs='EPSG:4326'
    )

    return gdf


def test_columns(
    shape,
    example_gdf
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        # saving example GeoDataFrame
        shape_file = os.path.join(tmp_dir, 'temporary.shp')
        example_gdf.to_file(shape_file)
        # pass test for retaining columns
        retain_gdf = shape.column_retain(
            input_file=shape_file,
            retain_cols=['C1', 'C2'],
            output_file=shape_file
        )
        assert list(retain_gdf.columns) == ['C1', 'C2', 'geometry']
        # pass test for deleting columns
        delete_gdf = shape.column_delete(
            input_file=shape_file,
            delete_cols=['C2'],
            output_file=shape_file
        )
        assert list(delete_gdf.columns) == ['C1', 'geometry']
        # pass test for adding ID column
        id_gdf = shape.column_add_for_id(
            input_file=shape_file,
            column_name='ID',
            output_file=shape_file
        )
        assert list(id_gdf.columns) == ['ID', 'C1', 'geometry']


def test_crs(
    shape,
    example_gdf
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        # saving example GeoDataFrame
        shape_file = os.path.join(tmp_dir, 'temporary.shp')
        example_gdf.to_file(shape_file)
        # pass test for Coordinate Reference System reprojection
        reproject_crs = shape.crs_reprojection(
            input_file=shape_file,
            target_crs='EPSG:3067',
            output_file=shape_file
        )
        assert reproject_crs == 'EPSG:3067'


def test_error_shapefile_driver(
    shape,
    message
):

    with pytest.raises(Exception) as exc_info:
        shape.column_retain(
            input_file='input.shp',
            retain_cols=['C1'],
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']

    with pytest.raises(Exception) as exc_info:
        shape.column_delete(
            input_file='input.shp',
            delete_cols=['C1'],
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']

    with pytest.raises(Exception) as exc_info:
        shape.column_add_for_id(
            input_file='input.shp',
            column_name=['C1'],
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']

    with pytest.raises(Exception) as exc_info:
        shape.crs_reprojection(
            input_file='input.shp',
            target_crs='EPSG:3067',
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
