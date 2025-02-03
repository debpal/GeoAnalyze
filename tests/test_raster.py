import os
import tempfile
import GeoAnalyze
import pytest


@pytest.fixture(scope='class')
def packagedata():

    yield GeoAnalyze.PackageData()


@pytest.fixture(scope='class')
def raster():

    yield GeoAnalyze.Raster()


@pytest.fixture
def message():

    output = {
        'error_driver': 'Could not retrieve driver from the file path.'
    }

    return output


def test_count_cells(
    packagedata,
    raster
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        # accessing DEM raster file
        dem_file = os.path.join(tmp_dir, 'dem.tif')
        raster_profile = packagedata.get_dem(
            dem_file=dem_file
        )
        assert raster_profile['count'] == 1
        # pass test for counting raster data cells
        data_cells = raster.count_data_cells(
            raster_file=dem_file
        )
        assert data_cells == 7758954
        # pass test for counting raster NoData cells
        nodata_cells = raster.count_nodata_cells(
            raster_file=dem_file
        )
        assert nodata_cells == 6305736
        # pass test for counting unique raster values
        count_df = raster.counting_unique_values(
            raster_file=dem_file,
            csv_file=os.path.join(tmp_dir, 'dem_count.csv'),
        )
        assert len(count_df) == 401
        # pass test for raster boundary polygon GeoDataFrame
        boundary_df = raster.boundary_polygon(
            raster_file=dem_file,
            shape_file=os.path.join(tmp_dir, 'dem_boundary.shp')
        )
        assert len(boundary_df) == 1


def test_error_raster_file_driver(
    packagedata,
    raster,
    message
):

    # error test for invalid file path for accessing DEM raster file
    with pytest.raises(Exception) as exc_info:
        packagedata.get_dem(
            dem_file='dem.tifff',
        )
    assert exc_info.value.args[0] == message['error_driver']
    # error test for invalid file path  for raster boundary polygon GeoDataFrame
    with pytest.raises(Exception) as exc_info:
        raster.boundary_polygon(
            raster_file='dem.tif',
            shape_file='dem_boundary.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
