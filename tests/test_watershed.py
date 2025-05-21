import os
import tempfile
import GeoAnalyze
import pytest


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
    # packagedata,
    raster,
    watershed,
    message
):

    # data folder
    data_folder = os.path.join(os.path.dirname(__file__), 'data')

    with tempfile.TemporaryDirectory() as tmp_dir:
        # saving extended DEM raster in temporary directory
        transfer_list = GeoAnalyze.File().transfer_by_name(
            src_folder=data_folder,
            dst_folder=tmp_dir,
            file_names=['dem_extended']
        )
        assert 'dem_extended.tif' in transfer_list
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
        # dem stattistics
        dem_stats = GeoAnalyze.Raster().statistics_summary(
            raster_file=os.path.join(tmp_dir, 'dem.tif')
        )
        assert dem_stats['Minimum'].round(1) == 136.0
        assert dem_stats['Maximum'].round(1) == 590.4
        assert dem_stats['Mean'].round(1) == 281.5
        assert dem_stats['Standard deviation'].round(1) == 43.7
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
        # saving stream shapefile in temporary directory
        transfer_list = GeoAnalyze.File().transfer_by_name(
            src_folder=data_folder,
            dst_folder=tmp_dir,
            file_names=['stream']
        )
        assert 'stream.shp' in transfer_list
        # raster array from geometries without filling mask region
        raster.array_from_geometries(
            shape_file=os.path.join(tmp_dir, 'stream.shp'),
            value_column='flw_id',
            mask_file=os.path.join(tmp_dir, 'dem.tif'),
            output_file=os.path.join(tmp_dir, 'stream.tif'),
            nodata=-9999,
            dtype='int32',
        )
        assert raster.count_data_cells(raster_file=os.path.join(tmp_dir, 'stream.tif')) == 12454
        raster.array_from_geometries(
            shape_file=os.path.join(tmp_dir, 'stream.shp'),
            value_column='flw_id',
            mask_file=os.path.join(tmp_dir, 'dem.tif'),
            output_file=os.path.join(tmp_dir, 'stream_1234.tif'),
            select_values=[1, 2, 3, 4],
            fill_value=0,
            dtype='int16'
        )
        output_gdf = raster.count_unique_values(
            raster_file=os.path.join(tmp_dir, 'stream_1234.tif'),
            csv_file=os.path.join(tmp_dir, 'stream_1234.csv'),
            remove_values=(0,)
        )
        assert output_gdf['Count'].sum() == 7436
        # statistics summary by reference zone
        stats_df = raster.statistics_summary_by_reference_zone(
            value_file=os.path.join(tmp_dir, 'dem.tif'),
            zone_file=os.path.join(tmp_dir, 'stream.tif'),
            csv_file=os.path.join(tmp_dir, 'statistics_dem_by_stream.csv')
        )
        assert stats_df.shape == (11, 8)
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
            select_values=[5, 6],
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
        # raster NoData to valid value change
        output_profile = raster.nodata_to_valid_value(
            input_file=os.path.join(tmp_dir, 'stream_nodata_0.tif'),
            valid_value=0,
            output_file=os.path.join(tmp_dir, 'stream_nodata_to_valid.tif')
        )
        assert output_profile['nodata'] is None
        # raster file merging
        with tempfile.TemporaryDirectory() as tmp1_dir:
            # shape of subbasin 8 to raster
            raster.array_from_geometries(
                shape_file=os.path.join(tmp_dir, 'subbasins.shp'),
                value_column='flw_id',
                mask_file=os.path.join(tmp_dir, 'dem.tif'),
                output_file=os.path.join(tmp_dir, tmp1_dir, 'subbasin_8.tif'),
                select_values=[8]
            )
            assert raster.count_data_cells(raster_file=os.path.join(tmp_dir, tmp1_dir, 'subbasin_8.tif')) == 214006
            # shape of subbasin 10 to raster
            raster.array_from_geometries(
                shape_file=os.path.join(tmp_dir, 'subbasins.shp'),
                value_column='flw_id',
                mask_file=os.path.join(tmp_dir, 'dem.tif'),
                output_file=os.path.join(tmp_dir, tmp1_dir, 'subbasin_10.tif'),
                select_values=[10]
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
            output_file=os.path.join(tmp_dir, 'subbasins_outside_area_6.tif')
        )
        assert len(output_list) == 3
        assert 6 in output_list
        assert 8 in output_list
        assert 5 not in output_list
        # raster extension to mask area
        raster.extension_to_mask_with_fill_value(
            input_file=os.path.join(tmp_dir, 'subbasin_merge.tif'),
            mask_file=os.path.join(tmp_dir, 'dem.tif'),
            fill_value=1,
            output_file=os.path.join(tmp_dir, 'subbasin_merge_extended.tif')
        )
        assert raster.count_data_cells(raster_file=os.path.join(tmp_dir, 'subbasin_merge_extended.tif')) == 8308974
        # raster value extraction by mask
        output_list = raster.extract_value_by_mask(
            input_file=os.path.join(tmp_dir, 'flwdir.tif'),
            mask_file=os.path.join(tmp_dir, 'stream.tif'),
            output_file=os.path.join(tmp_dir, 'flwdir_extract.tif'),
            fill_value=0
        )
        assert all([i in output_list for i in [0, 1, 2, 4, 8, 16, 32, 64, 128]])
        # raster driver conversion
        output_profile = raster.driver_convert(
            input_file=os.path.join(tmp_dir, 'flwdir.tif'),
            target_driver='RST',
            output_file=os.path.join(tmp_dir, 'flwdir.rst')
        )
        assert output_profile['driver'] == 'RST'


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
