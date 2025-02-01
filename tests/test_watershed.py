import os
import tempfile
import GeoAnalyze
import pytest


@pytest.fixture(scope='class')
def packagedata():

    yield GeoAnalyze.PackageData()


@pytest.fixture(scope='class')
def watershed():

    yield GeoAnalyze.Watershed()


def test_delineation_files_by_single_function(
    packagedata,
    watershed
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        # saving DEM raster file
        dem_file = os.path.join(tmp_dir, 'dem.tif')
        packagedata.get_dem(
            dem_file=dem_file
        )
        # pass test of delineation files by single function
        output = watershed.delineation_files_by_single_function(
            dem_file=dem_file,
            outlet_type='single',
            tacc_type='percentage',
            tacc_value=5,
            folder_path=tmp_dir
        )
        assert output == 'All geoprocessing has been completed.'
        # error test for invalid folder path
        with pytest.raises(Exception) as exc_info:
            watershed.delineation_files_by_single_function(
                dem_file=dem_file,
                outlet_type='single',
                tacc_type='percentage',
                tacc_value=5,
                folder_path='folder_path'
            )
        assert exc_info.value.args[0] == 'Input folder path does not exsit.'
        # error test for invalid outlet type
        with pytest.raises(Exception) as exc_info:
            watershed.delineation_files_by_single_function(
                dem_file=dem_file,
                outlet_type='singleee',
                tacc_type='percentage',
                tacc_value=5,
                folder_path=tmp_dir
            )
        assert exc_info.value.args[0] == 'Outlet type must be one of [single, multiple].'
        # error test for invalid threshold flow accumalation type
        with pytest.raises(Exception) as exc_info:
            watershed.delineation_files_by_single_function(
                dem_file=dem_file,
                outlet_type='single',
                tacc_type='percentagee',
                tacc_value=5,
                folder_path=tmp_dir
            )
        assert exc_info.value.args[0] == 'Threshold accumulation type must be one of [percentage, absolute].'
