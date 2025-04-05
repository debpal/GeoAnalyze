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


def test_functions(
    packagedata,
    raster,
    watershed,
    message
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        # saving DEM raster file fo packaged data
        output_profile = packagedata.raster_dem(
            dem_file=os.path.join(tmp_dir, 'dem_extended.tif')
        )
        assert output_profile['nodata'] is None
        # raster Coordinate Reference System reprojectoion
        output_profile = raster.crs_reprojection(
            input_file=os.path.join(tmp_dir, 'dem_extended.tif'),
            resampling_method='bilinear',
            target_crs='EPSG:3067',
            output_file=os.path.join(tmp_dir, 'dem_extended_EPSG3067.tif'),
            nodata=-9999
        )
        assert output_profile['height'] == 3956
        # raster resolution rescaling
        output_profile = raster.resolution_rescaling(
            input_file=os.path.join(tmp_dir, 'dem_extended_EPSG3067.tif'),
            target_resolution=16,
            resampling_method='bilinear',
            output_file=os.path.join(tmp_dir, 'dem_extended_EPSG3067_16m.tif')
        )
        assert output_profile['height'] == 4093
        # raster resolution rescaling with mask
        output_profile = raster.resolution_rescaling_with_mask(
            input_file=os.path.join(tmp_dir, 'dem_extended_EPSG3067_16m.tif'),
            mask_file=os.path.join(tmp_dir, 'dem_extended_EPSG3067.tif'),
            resampling_method='bilinear',
            output_file=os.path.join(tmp_dir, 'dem_extended_rescale.tif')
        )
        assert output_profile['height'] == 3957
        # dem extended area to basin
        output_gdf = watershed.dem_extended_area_to_basin(
            input_file=os.path.join(tmp_dir, 'dem_extended_EPSG3067_16m.tif'),
            basin_file=os.path.join(tmp_dir, 'basin.shp'),
            output_file=os.path.join(tmp_dir, 'dem.tif')
        )
        assert int(output_gdf['flwacc'].iloc[0]) == 8308974
        # raster boundary polygon GeoDataFrame
        output_gdf = raster.boundary_polygon(
            raster_file=os.path.join(tmp_dir, 'dem.tif'),
            shape_file=os.path.join(tmp_dir, 'dem_boundary.shp')
        )
        assert len(output_gdf) == 1
        # dem delineation by single function
        output = watershed.dem_delineation(
            dem_file=os.path.join(tmp_dir, 'dem.tif'),
            outlet_type='single',
            tacc_type='percentage',
            tacc_value=5,
            folder_path=tmp_dir
        )
        assert output == 'All geoprocessing has been completed.'
        # flow direction
        output = watershed.get_flwdir(
            dem_file=os.path.join(tmp_dir, 'dem.tif'),
            outlet_type='single',
            pitfill_file=os.path.join(tmp_dir, 'dem_pitfill.tif'),
            flwdir_file=os.path.join(tmp_dir, 'flwdir.tif')
        )
        assert isinstance(output, str)
        # flow accumulation
        output = watershed.get_flwacc(
            flwdir_file=os.path.join(tmp_dir, 'flwdir.tif'),
            flwacc_file=os.path.join(tmp_dir, 'flwacc.tif'),
        )
        assert isinstance(output, str)
        # stream and main outlets
        output = watershed.get_stream(
            flwdir_file=os.path.join(tmp_dir, 'flwdir.tif'),
            flwacc_file=os.path.join(tmp_dir, 'flwacc.tif'),
            tacc_type='percentage',
            tacc_value=5,
            stream_file=os.path.join(tmp_dir, 'stream.shp'),
            outlet_file=os.path.join(tmp_dir, 'outlet.shp')
        )
        assert isinstance(output, str)
        # subbasins and their pour points
        output = watershed.get_subbasins(
            flwdir_file=os.path.join(tmp_dir, 'flwdir.tif'),
            stream_file=os.path.join(tmp_dir, 'stream.shp'),
            outlet_file=os.path.join(tmp_dir, 'outlet.shp'),
            subbasin_file=os.path.join(tmp_dir, 'subbasin.shp'),
            pour_file=os.path.join(tmp_dir, 'pour.shp')
        )
        assert isinstance(output, str)
        # slope
        output = watershed.get_slope(
            dem_file=os.path.join(tmp_dir, 'dem.tif'),
            slope_file=os.path.join(tmp_dir, 'slope.tif')
        )
        assert isinstance(output, str)
        # aspect
        output = watershed.get_aspect(
            dem_file=os.path.join(tmp_dir, 'dem.tif'),
            aspect_file=os.path.join(tmp_dir, 'aspect.tif')
        )
        assert isinstance(output, str)
        # slope reclassification
        output = watershed.slope_classification(
            slope_file=os.path.join(tmp_dir, 'slope.tif'),
            reclass_lb=[0, 2, 8, 20, 40],
            reclass_values=[2, 8, 20, 40, 50],
            reclass_file=os.path.join(tmp_dir, 'slope_reclass.tif')
        )
        assert isinstance(output, str)
        # raster unique values
        count_df = raster.count_unique_values(
            raster_file=os.path.join(tmp_dir, 'slope_reclass.tif'),
            csv_file=os.path.join(tmp_dir, 'slope_reclass.csv'),
        )
        assert len(count_df) == 5
        # accessing stream GeoDataFrame
        output_gdf = packagedata.geodataframe_stream
        output_gdf.to_file(os.path.join(tmp_dir, 'stream.shp'))
        assert len(output_gdf) == 11
        # raster array from geometries
        raster.array_from_geometries(
            shape_file=os.path.join(tmp_dir, 'stream.shp'),
            value_column='flw_id',
            mask_file=os.path.join(tmp_dir, 'dem.tif'),
            output_file=os.path.join(tmp_dir, 'stream.tif'),
            nodata=-9999,
            dtype='int32',
        )
        assert raster.count_data_cells(raster_file=os.path.join(tmp_dir, 'stream.tif')) == 12454
        # raster reclassification by value mapping
        output_list = raster.reclassify_by_value_mapping(
            input_file=os.path.join(tmp_dir, 'stream.tif'),
            reclass_map={(3, 4): 1},
            output_file=os.path.join(tmp_dir, 'stream_reclass.tif')
        )
        assert 3 not in output_list
        assert 4 not in output_list
        # raster reclassification by constant value
        output_list = raster.reclassify_by_constant_value(
            input_file=os.path.join(tmp_dir, 'dem.tif'),
            constant_value=60,
            output_file=os.path.join(tmp_dir, 'dem_reclass.tif')
        )
        assert 60 in output_list
        assert 100 not in output_list
        # raster overlaid with geometries
        output_list = raster.overlaid_with_geometries(
            input_file=os.path.join(tmp_dir, 'dem_reclass.tif'),
            shape_file=os.path.join(tmp_dir, 'stream_lines.shp'),
            value_column='flw_id',
            output_file=os.path.join(tmp_dir, 'pasting_stream_in_dem_reclass.tif')
        )
        assert 1 in output_list
        assert 5 in output_list
        assert 6 in output_list
        # raster array to geometries
        output_gdf = raster.array_to_geometries(
            raster_file=os.path.join(tmp_dir, 'stream.tif'),
            select_value=[5, 6],
            shape_file=os.path.join(tmp_dir, 'stream_polygon.shp')
        )
        len(output_gdf) == 2
        # raster NoData conversion from value
        raster.nodata_conversion_from_value(
            input_file=os.path.join(tmp_dir, 'stream.tif'),
            target_value=[1, 9],
            output_file=os.path.join(tmp_dir, 'stream_NoData.tif')
        )
        assert raster.count_nodata_cells(raster_file=os.path.join(tmp_dir, 'stream_NoData.tif')) == 13921390
        # raster NoData value change
        output_profile = raster.nodata_value_change(
            input_file=os.path.join(tmp_dir, 'stream.tif'),
            nodata=0,
            output_file=os.path.join(tmp_dir, 'stream_nodata_0.tif'),
            dtype='float32'
        )
        assert output_profile['nodata'] == 0
        # raster file merging
        with tempfile.TemporaryDirectory() as tmp1_dir:
            # shape of subbasin 8 to raster
            raster.array_from_geometries(
                shape_file=os.path.join(tmp_dir, 'subbasins.shp'),
                value_column='flw_id',
                mask_file=os.path.join(tmp_dir, 'dem.tif'),
                output_file=os.path.join(tmp_dir, tmp1_dir, 'subbasin_8.tif'),
                select_value=[8]
            )
            assert raster.count_data_cells(raster_file=os.path.join(tmp_dir, tmp1_dir, 'subbasin_8.tif')) == 214006
            # shape of subbasin 10 to raster
            raster.array_from_geometries(
                shape_file=os.path.join(tmp_dir, 'subbasins.shp'),
                value_column='flw_id',
                mask_file=os.path.join(tmp_dir, 'dem.tif'),
                output_file=os.path.join(tmp_dir, tmp1_dir, 'subbasin_10.tif'),
                select_value=[10]
            )
            assert raster.count_data_cells(raster_file=os.path.join(tmp_dir, tmp1_dir, 'subbasin_10.tif')) == 305596
            # merging files
            raster.merging_files(
                folder_path=os.path.join(tmp_dir, tmp1_dir),
                raster_file=os.path.join(tmp_dir, 'subbasin_merge.tif')
            )
            assert raster.count_data_cells(raster_file=os.path.join(tmp_dir, 'subbasin_merge.tif')) == 519602
        # raster NoData extent trimming
        output_profile = raster.nodata_extent_trimming(
            input_file=os.path.join(tmp_dir, 'subbasin_merge.tif'),
            output_file=os.path.join(tmp_dir, 'subbasin_merge_remove_nodata.tif')
        )
        assert output_profile['width'] == 1173
        assert output_profile['height'] == 844
        # raster value reclassification outside boundary area
        raster.array_from_geometries(
            shape_file=os.path.join(tmp_dir, 'subbasins.shp'),
            value_column='flw_id',
            mask_file=os.path.join(tmp_dir, 'dem.tif'),
            output_file=os.path.join(tmp_dir, 'subbasins.tif')
        )
        output_list = raster.reclassify_value_outside_boundary(
            input_file=os.path.join(tmp_dir, 'subbasins.tif'),
            area_file=os.path.join(tmp_dir, 'subbasin_merge.tif'),
            outside_value=6,
            output_file=os.path.join(tmp_dir, 'subbasins_outside_area_0.tif')
        )
        assert len(output_list) == 3
        assert 6 in output_list
        assert 8 in output_list
        assert 5 not in output_list


def test_error_invalid_folder_path(
    watershed
):

    # dem delineation
    with pytest.raises(Exception) as exc_info:
        watershed.dem_delineation(
            dem_file='dem.tif',
            outlet_type='single',
            tacc_type='percentage',
            tacc_value=5,
            folder_path='folder_path'
        )
    assert exc_info.value.args[0] == 'Input folder path does not exsit.'


def test_error_invalid_file_path(
    watershed,
    message
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        # dem extended area to basin
        with pytest.raises(Exception) as exc_info:
            watershed.dem_extended_area_to_basin(
                input_file=os.path.join(tmp_dir, 'dem_extended.tif'),
                basin_file=os.path.join(tmp_dir, 'basin.sh'),
                output_file=os.path.join(tmp_dir, 'dem.tif')
            )
        assert exc_info.value.args[0] == message['error_driver']
        with pytest.raises(Exception) as exc_info:
            watershed.dem_extended_area_to_basin(
                input_file=os.path.join(tmp_dir, 'dem_extended.tif'),
                basin_file=os.path.join(tmp_dir, 'basin.shp'),
                output_file=os.path.join(tmp_dir, 'dem.tifff')
            )
        assert exc_info.value.args[0] == message['error_driver']
        # flow direction
        with pytest.raises(Exception) as exc_info:
            watershed.get_flwdir(
                dem_file=os.path.join(tmp_dir, 'dem.tif'),
                outlet_type='single',
                pitfill_file=os.path.join(tmp_dir, 'dem_pitfill.tif'),
                flwdir_file=os.path.join(tmp_dir, 'flwdir.tifff')
            )
        assert exc_info.value.args[0] == message['error_driver']
        # flow accumulation
        with pytest.raises(Exception) as exc_info:
            watershed.get_flwacc(
                flwdir_file=os.path.join(tmp_dir, 'flwdir.tif'),
                flwacc_file=os.path.join(tmp_dir, 'flwacc.tifff')
            )
        assert exc_info.value.args[0] == message['error_driver']
        # stream and main outlets
        with pytest.raises(Exception) as exc_info:
            watershed.get_stream(
                flwdir_file=os.path.join(tmp_dir, 'flwdir.tif'),
                flwacc_file=os.path.join(tmp_dir, 'flwacc.tif'),
                tacc_type='percentage',
                tacc_value=5,
                stream_file=os.path.join(tmp_dir, 'stream.sh'),
                outlet_file=os.path.join(tmp_dir, 'outlet.shp')
            )
        assert exc_info.value.args[0] == message['error_driver']
        # subbasins and their pour points
        with pytest.raises(Exception) as exc_info:
            watershed.get_subbasins(
                flwdir_file=os.path.join(tmp_dir, 'flwdir.tif'),
                stream_file=os.path.join(tmp_dir, 'stream.shp'),
                outlet_file=os.path.join(tmp_dir, 'outlet.shp'),
                subbasin_file=os.path.join(tmp_dir, 'subbasin.sh'),
                pour_file=os.path.join(tmp_dir, 'pour.shp')
            )
        assert exc_info.value.args[0] == message['error_driver']
        # slope
        with pytest.raises(Exception) as exc_info:
            watershed.get_slope(
                dem_file=os.path.join(tmp_dir, 'dem.tif'),
                slope_file=os.path.join(tmp_dir, 'slope.tifff')
            )
        assert exc_info.value.args[0] == message['error_driver']
        # aspect
        with pytest.raises(Exception) as exc_info:
            watershed.get_aspect(
                dem_file=os.path.join(tmp_dir, 'dem.tif'),
                aspect_file=os.path.join(tmp_dir, 'aspect.tifff')
            )
        assert exc_info.value.args[0] == message['error_driver']
        # slope reclassification
        with pytest.raises(Exception) as exc_info:
            watershed.slope_classification(
                slope_file=os.path.join(tmp_dir, 'slope.tif'),
                reclass_lb=[0, 2, 8, 20, 40],
                reclass_values=[2, 8, 20, 40, 50],
                reclass_file=os.path.join(tmp_dir, 'slope_reclass.tifff')
            )
        assert exc_info.value.args[0] == message['error_driver']


def test_error_type_outlet(
    watershed,
    message
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        # dem delineation
        with pytest.raises(Exception) as exc_info:
            watershed.dem_delineation(
                dem_file=os.path.join(tmp_dir, 'dem.tif'),
                outlet_type='singleee',
                tacc_type='percentage',
                tacc_value=5,
                folder_path=tmp_dir
            )
        assert exc_info.value.args[0] == message['type_outlet']
        # flow direction after pit filling of DEM
        with pytest.raises(Exception) as exc_info:
            watershed.get_flwdir(
                dem_file=os.path.join(tmp_dir, 'dem.tif'),
                outlet_type='singleee',
                pitfill_file=os.path.join(tmp_dir, 'dem_pitfill.tif'),
                flwdir_file=os.path.join(tmp_dir, 'flwdir.tif')
            )
        assert exc_info.value.args[0] == message['type_outlet']


def test_error_type_flwacc(
    watershed,
    message
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        # dem delineation
        with pytest.raises(Exception) as exc_info:
            watershed.dem_delineation(
                dem_file=os.path.join(tmp_dir, 'dem.tif'),
                outlet_type='single',
                tacc_type='percentagee',
                tacc_value=5,
                folder_path=tmp_dir
            )
        assert exc_info.value.args[0] == message['type_flwacc']
        # stream and main outlets
        with pytest.raises(Exception) as exc_info:
            watershed.get_stream(
                flwdir_file=os.path.join(tmp_dir, 'flwdir.tif'),
                flwacc_file=os.path.join(tmp_dir, 'flwacc.tif'),
                tacc_type='percentagee',
                tacc_value=5,
                stream_file=os.path.join(tmp_dir, 'stream.shp'),
                outlet_file=os.path.join(tmp_dir, 'outlet.shp')
            )
        assert exc_info.value.args[0] == message['type_flwacc']


def test_error_list_length_slope(
    watershed
):

    # slope reclassification
    with pytest.raises(Exception) as exc_info:
        watershed.slope_classification(
            slope_file='slope.tif',
            reclass_lb=[0, 2, 8, 20, 40],
            reclass_values=[2, 8, 20, 40],
            reclass_file='slope_reclass.tif'
        )
    assert exc_info.value.args[0] == 'Both input lists must have the same length.'
