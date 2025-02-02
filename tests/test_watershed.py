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


@pytest.fixture
def message():

    output = {
        'error_driver': 'Could not retrieve driver from the file path.',
        'type_outlet': 'Outlet type must be one of [single, multiple].',
        'type_flwacc': 'Threshold accumulation type must be one of [percentage, absolute].'
    }

    return output


def test_delineation_files(
    packagedata,
    watershed,
    message
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        # saving DEM raster file
        dem_file = os.path.join(tmp_dir, 'dem.tif')
        packagedata.get_dem(
            dem_file=dem_file
        )
        ##############################################
        # pass test for computing flow direction after pit filling of the DEM
        output = watershed.flow_direction_after_filling_pits(
            dem_file=dem_file,
            outlet_type='single',
            pitfill_file=os.path.join(tmp_dir, 'pitfill_dem.tif'),
            flwdir_file=os.path.join(tmp_dir, 'flwdir.tif')
        )
        assert isinstance(output, str)
        # pass test for computing flow accumulation
        output = watershed.flow_accumulation(
            pitfill_file=os.path.join(tmp_dir, 'pitfill_dem.tif'),
            flwdir_file=os.path.join(tmp_dir, 'flwdir.tif'),
            flwacc_file=os.path.join(tmp_dir, 'flwacc.tif'),
        )
        assert isinstance(output, str)
        # pass test for computing stream network and main outlets
        output = watershed.stream_network_and_main_outlets(
            flwdir_file=os.path.join(tmp_dir, 'flwdir.tif'),
            flwacc_file=os.path.join(tmp_dir, 'flwacc.tif'),
            tacc_type='percentage',
            tacc_value=5,
            stream_file=os.path.join(tmp_dir, 'stream.shp'),
            outlet_file=os.path.join(tmp_dir, 'outlet.shp')
        )
        assert isinstance(output, str)
        # pass test for computing subbasins and their pour points
        output = watershed.subbasin_and_pourpoints(
            flwdir_file=os.path.join(tmp_dir, 'flwdir.tif'),
            stream_file=os.path.join(tmp_dir, 'stream.shp'),
            outlet_file=os.path.join(tmp_dir, 'outlet.shp'),
            subbasin_file=os.path.join(tmp_dir, 'subbasin.shp'),
            pour_file=os.path.join(tmp_dir, 'pour.shp')
        )
        assert isinstance(output, str)
        # pass test for computing slope from DEM without pit filling
        output = watershed.slope_from_dem_without_pit_filling(
            dem_file=dem_file,
            slope_file=os.path.join(tmp_dir, 'slope.tif')
        )
        assert isinstance(output, str)
        # pass test for slope reclassingfication
        output = watershed.slope_classification(
            slope_file=os.path.join(tmp_dir, 'slope.tif'),
            reclass_lb=[0, 2, 8, 20, 40],
            reclass_values=[2, 8, 20, 40, 50],
            reclass_file=os.path.join(tmp_dir, 'slope_reclass.tif')
        )
        assert isinstance(output, str)
        # pass test for computing delineation files by single function
        output = watershed.delineation_files_by_single_function(
            dem_file=dem_file,
            outlet_type='single',
            tacc_type='percentage',
            tacc_value=5,
            folder_path=tmp_dir
        )
        assert output == 'All geoprocessing has been completed.'
        ##############################################
        # error test of invalid file path for computing flow direction pit filling of the DEM
        with pytest.raises(Exception) as exc_info:
            watershed.flow_direction_after_filling_pits(
                dem_file=dem_file,
                outlet_type='singleee',
                pitfill_file=os.path.join(tmp_dir, 'pitfill_dem.tif'),
                flwdir_file=os.path.join(tmp_dir, 'flwdir.tifff')
            )
        assert exc_info.value.args[0] == message['error_driver']
        # error test of invalid file path for computing flow accumulation
        with pytest.raises(Exception) as exc_info:
            watershed.flow_accumulation(
                pitfill_file=os.path.join(tmp_dir, 'pitfill_dem.tif'),
                flwdir_file=os.path.join(tmp_dir, 'flwdir.tif'),
                flwacc_file=os.path.join(tmp_dir, 'flwacc.tifff'),
            )
        assert exc_info.value.args[0] == message['error_driver']
        # error test of invalid file path for computing stream network and main outlets
        with pytest.raises(Exception) as exc_info:
            watershed.stream_network_and_main_outlets(
                flwdir_file=os.path.join(tmp_dir, 'flwdir.tif'),
                flwacc_file=os.path.join(tmp_dir, 'flwacc.tif'),
                tacc_type='percentage',
                tacc_value=5,
                stream_file=os.path.join(tmp_dir, 'stream.sh'),
                outlet_file=os.path.join(tmp_dir, 'outlet.shp')
            )
        assert exc_info.value.args[0] == message['error_driver']
        # error test of invalid file path for computing subbasins and their pour points
        with pytest.raises(Exception) as exc_info:
            watershed.subbasin_and_pourpoints(
                flwdir_file=os.path.join(tmp_dir, 'flwdir.tif'),
                stream_file=os.path.join(tmp_dir, 'stream.shp'),
                outlet_file=os.path.join(tmp_dir, 'outlet.shp'),
                subbasin_file=os.path.join(tmp_dir, 'subbasin.sh'),
                pour_file=os.path.join(tmp_dir, 'pour.shp')
            )
        assert exc_info.value.args[0] == message['error_driver']
        # error test of invalid file path for computing slope from DEM without pit filling
        with pytest.raises(Exception) as exc_info:
            watershed.slope_from_dem_without_pit_filling(
                dem_file=dem_file,
                slope_file=os.path.join(tmp_dir, 'slope.tifff')
            )
        assert exc_info.value.args[0] == message['error_driver']
        # error test of invalid file path for slope reclassification
        with pytest.raises(Exception) as exc_info:
            watershed.slope_classification(
                slope_file=os.path.join(tmp_dir, 'slope.tif'),
                reclass_lb=[0, 2, 8, 20, 40],
                reclass_values=[2, 8, 20, 40, 50],
                reclass_file=os.path.join(tmp_dir, 'slope_reclass.tifff')
            )
        assert exc_info.value.args[0] == message['error_driver']
        ##############################################
        # error test of invalid outlet type for computing flow direction and pit filling of the DEM
        with pytest.raises(Exception) as exc_info:
            watershed.flow_direction_after_filling_pits(
                dem_file=dem_file,
                outlet_type='singleee',
                pitfill_file=os.path.join(tmp_dir, 'pitfill_dem.tif'),
                flwdir_file=os.path.join(tmp_dir, 'flwdir.tif')
            )
        assert exc_info.value.args[0] == message['type_outlet']
        # error test of invalid outlet type for delineation files by single function
        with pytest.raises(Exception) as exc_info:
            watershed.delineation_files_by_single_function(
                dem_file=dem_file,
                outlet_type='singleee',
                tacc_type='percentage',
                tacc_value=5,
                folder_path=tmp_dir
            )
        assert exc_info.value.args[0] == message['type_outlet']
        # error test of invalid threshold flow accumalation type for computing stream network and main outlets
        with pytest.raises(Exception) as exc_info:
            watershed.stream_network_and_main_outlets(
                flwdir_file=os.path.join(tmp_dir, 'flwdir.tif'),
                flwacc_file=os.path.join(tmp_dir, 'flwacc.tif'),
                tacc_type='percentagee',
                tacc_value=5,
                stream_file=os.path.join(tmp_dir, 'stream.shp'),
                outlet_file=os.path.join(tmp_dir, 'outlet.shp')
            )
        assert exc_info.value.args[0] == message['type_flwacc']
        # error test of invalid threshold flow accumalation type for computing delineation files by single function
        with pytest.raises(Exception) as exc_info:
            watershed.delineation_files_by_single_function(
                dem_file=dem_file,
                outlet_type='single',
                tacc_type='percentagee',
                tacc_value=5,
                folder_path=tmp_dir
            )
        assert exc_info.value.args[0] == message['type_flwacc']
        ##############################################
        # error test of input list lengths for slope reclassification
        with pytest.raises(Exception) as exc_info:
            watershed.slope_classification(
                slope_file=os.path.join(tmp_dir, 'slope.tif'),
                reclass_lb=[0, 2, 8, 20, 40],
                reclass_values=[2, 8, 20, 40],
                reclass_file=os.path.join(tmp_dir, 'slope_reclass.tif')
            )
        assert exc_info.value.args[0] == 'Both input lists must have the same length.'
        ##############################################
        # error test of invalid folder path for computing delineation files by single function
        with pytest.raises(Exception) as exc_info:
            watershed.delineation_files_by_single_function(
                dem_file=dem_file,
                outlet_type='single',
                tacc_type='percentage',
                tacc_value=5,
                folder_path='folder_path'
            )
        assert exc_info.value.args[0] == 'Input folder path does not exsit.'
