import GeoAnalyze
import pytest
import tempfile
import os


@pytest.fixture(scope='class')
def raster():

    yield GeoAnalyze.Raster()


@pytest.fixture
def message():

    output = {
        'error_driver': 'Could not retrieve driver from the file path.',
        'error_resampling': f'Input resampling method must be one of {list(GeoAnalyze.core.Core().raster_resampling_method.keys())}.'
    }

    return output


def test_functions(
    raster
):

    # data folder
    data_folder = os.path.join(os.path.dirname(__file__), 'data')

    with tempfile.TemporaryDirectory() as tmp_dir:
        # saving stream shapefile in temporary directory
        transfer_list = GeoAnalyze.File().transfer_by_name(
            src_folder=data_folder,
            dst_folder=tmp_dir,
            file_names=['stream', 'dem_mask']
        )
        assert 'stream.shp' in transfer_list
        # raster array from geometries without filling mask region
        output_profile = raster.array_from_geometries(
            shape_file=os.path.join(tmp_dir, 'stream.shp'),
            value_column='flw_id',
            mask_file=os.path.join(tmp_dir, 'dem_mask.tif'),
            output_file=os.path.join(tmp_dir, 'stream.tif'),
            nodata=-9999,
            dtype='int32',
        )
        assert output_profile['height'] == 3923
        # count data cells
        data_cell = raster.count_data_cells(
            raster_file=os.path.join(tmp_dir, 'stream.tif')
        )
        assert data_cell == 12454
        # count unique values
        output_gdf = raster.count_unique_values(
            raster_file=os.path.join(tmp_dir, 'stream.tif'),
            csv_file=os.path.join(tmp_dir, 'stream_count_unique_values.csv')
        )
        assert output_gdf['Count'].sum() == 12454
        # stattistics summary
        raster_stats = GeoAnalyze.Raster().statistics_summary(
            raster_file=os.path.join(tmp_dir, 'stream.tif')
        )
        assert raster_stats['Minimum'] == 1
        assert raster_stats['Maximum'] == 11
        # statistics summary by reference zone
        stats_df = raster.statistics_summary_by_reference_zone(
            value_file=os.path.join(tmp_dir, 'dem_mask.tif'),
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
            input_file=os.path.join(tmp_dir, 'dem_mask.tif'),
            constant_value=60,
            output_file=os.path.join(tmp_dir, 'dem_mask_reclass_60.tif')
        )
        assert 60 in output_list
        assert 282 not in output_list
        # raster overlaid with geometries
        output_list = raster.overlaid_with_geometries(
            input_file=os.path.join(tmp_dir, 'dem_mask.tif'),
            shape_file=os.path.join(tmp_dir, 'stream.shp'),
            value_column='flw_id',
            output_file=os.path.join(tmp_dir, 'stream_in_dem_mask.tif')
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
            output_file=os.path.join(tmp_dir, 'stream_value_to_NoData.tif')
        )
        nodata_cell = raster.count_nodata_cells(
            raster_file=os.path.join(tmp_dir, 'stream_value_to_NoData.tif')
        )
        assert nodata_cell == 13921390
        # raster NoData value change
        output_profile = raster.nodata_value_change(
            input_file=os.path.join(tmp_dir, 'stream.tif'),
            nodata=0,
            output_file=os.path.join(tmp_dir, 'stream_nodata_to_0.tif'),
            dtype='float32'
        )
        assert output_profile['nodata'] == 0
        # raster NoData to valid value change
        output_profile = raster.nodata_to_valid_value(
            input_file=os.path.join(tmp_dir, 'stream_nodata_to_0.tif'),
            valid_value=0,
            output_file=os.path.join(tmp_dir, 'stream_nodata_to_valid.tif')
        )
        assert output_profile['nodata'] is None
        # raster NoData extent trimming
        output_profile = raster.nodata_extent_trimming(
            input_file=os.path.join(tmp_dir, 'stream.tif'),
            output_file=os.path.join(tmp_dir, 'stream_nodata_trim.tif')
        )
        assert output_profile['width'] == 3155
        assert output_profile['height'] == 3348
        # raster value scale and offet
        output_array = GeoAnalyze.Raster().value_scale_and_offset(
            input_file=os.path.join(tmp_dir, 'dem_mask.tif'),
            output_file=os.path.join(tmp_dir, 'dem_mask_scale_10.tif'),
            scale=10
        )
        assert 2820 in output_array
        # removing Coordinate Reference System
        output_profile = raster.crs_removal(
            input_file=os.path.join(tmp_dir, 'stream.tif'),
            output_file=os.path.join(tmp_dir, 'stream_no_crs.tif')
        )
        assert output_profile['crs'] is None
        # assigning Coordinate Reference System
        output_profile = raster.crs_assign(
            input_file=os.path.join(tmp_dir, 'stream_no_crs.tif'),
            crs_code=3067,
            output_file=os.path.join(tmp_dir, 'stream_EPSG3067.tif')
        )
        assert str(output_profile['crs']) == 'EPSG:3067'
        # raster driver conversion
        output_profile = raster.driver_convert(
            input_file=os.path.join(tmp_dir, 'stream.tif'),
            target_driver='RST',
            output_file=os.path.join(tmp_dir, 'stream.rst')
        )
        assert output_profile['driver'] == 'RST'
        # raster value extraction by mask
        output_list = raster.extract_value_by_mask(
            input_file=os.path.join(tmp_dir, 'dem_mask_reclass_60.tif'),
            mask_file=os.path.join(tmp_dir, 'stream.tif'),
            output_file=os.path.join(tmp_dir, 'dem_mask_reclass_extract.tif'),
            fill_value=0
        )
        assert output_list == [0, 60]
        # raster value extraction by range
        output_list = raster.extract_value_by_range(
            input_file=os.path.join(tmp_dir, 'stream.tif'),
            output_file=os.path.join(tmp_dir, 'stream_value_extract_by_range.tif'),
            lower_bound=3,
            upper_bound=6
        )
        assert output_list[0] >= 3
        assert output_list[1] <= 6


def test_error_raster_file_driver(
    raster,
    message
):

    # boundary polygon GeoDataFrame
    with pytest.raises(Exception) as exc_info:
        raster.boundary_polygon(
            raster_file='dem.tif',
            shape_file='dem_boundary.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # resolution rescaling
    with pytest.raises(Exception) as exc_info:
        raster.resolution_rescaling(
            input_file='dem.tif',
            target_resolution=32,
            resampling_method='bilinear',
            output_file='dem_32m.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # resolution rescaling with mask
    with pytest.raises(Exception) as exc_info:
        raster.resolution_rescaling_with_mask(
            input_file='dem_32m.tif',
            mask_file='dem.tif',
            resampling_method='bilinear',
            output_file='dem_16m.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster value scale and offet
    with pytest.raises(Exception) as exc_info:
        raster.value_scale_and_offset(
            input_file='dem_mask.tif',
            output_file='dem_mask_scale_10.tifff',
            scale=10
        )
    assert exc_info.value.args[0] == message['error_driver']
    # removing Coordinate Reference System
    with pytest.raises(Exception) as exc_info:
        raster.crs_removal(
            input_file='stream.tif',
            output_file='stream_no_crs.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # assigning Coordinate Reference System
    with pytest.raises(Exception) as exc_info:
        raster.crs_assign(
            input_file='stream_no_crs.tif',
            crs_code=3067,
            output_file='stream_EPSG3067.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # reprojecting Coordinate Reference System
    with pytest.raises(Exception) as exc_info:
        raster.crs_reprojection(
            input_file='dem.tif',
            resampling_method='bilinear',
            target_crs='EPSG:4326',
            output_file='dem_EPSG4326.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # NoData conversion from value
    with pytest.raises(Exception) as exc_info:
        raster.nodata_conversion_from_value(
            input_file='stream.tif',
            target_value=[1, 9],
            output_file='stream_NoData.tifff',
        )
    assert exc_info.value.args[0] == message['error_driver']
    # NoData value change
    with pytest.raises(Exception) as exc_info:
        raster.nodata_value_change(
            input_file='dem.tif',
            nodata=0,
            output_file='dem_NoData_0.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # NoData to valid value
    with pytest.raises(Exception) as exc_info:
        raster.nodata_to_valid_value(
            input_file='dem.tif',
            valid_value=0,
            output_file='dem_NoData_0.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # NoData extent trimming
    with pytest.raises(Exception) as exc_info:
        raster.nodata_extent_trimming(
            input_file='subbasin_merge.tif',
            output_file='subbasin_merge_remove_nodata.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster clipping by shapes
    with pytest.raises(Exception) as exc_info:
        raster.clipping_by_shapes(
            input_file='dem.tif',
            shape_file='mask.shp',
            output_file='dem_clipped.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # array from geometries
    with pytest.raises(Exception) as exc_info:
        raster.array_from_geometries(
            shape_file='stream.shp',
            value_column='flw_id',
            mask_file='dem.tif',
            nodata=-9999,
            dtype='int32',
            output_file='stream.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # array from geometries without mask
    with pytest.raises(Exception) as exc_info:
        raster.array_from_geometries_without_mask(
            shape_file='dem_mask_boundary.shp',
            value_column='bid',
            resolution=16,
            output_file='dem_mask_boundary.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster overlaid with geometries
    with pytest.raises(Exception) as exc_info:
        raster.overlaid_with_geometries(
            input_file='dem_reclass.tif',
            shape_file='stream_lines.shp',
            value_column='flw_id',
            output_file='pasting_stream_in_dem_reclass.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster reclassification by value mapping
    with pytest.raises(Exception) as exc_info:
        raster.reclassify_by_value_mapping(
            input_file='stream.tif',
            reclass_map={(3, 4): 1},
            output_file='stream_reclass.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster reclassification by constant value
    with pytest.raises(Exception) as exc_info:
        raster.reclassify_by_constant_value(
            input_file='dem.tif',
            constant_value=60,
            output_file='dem_reclass.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster reclassification outside boundary area
    with pytest.raises(Exception) as exc_info:
        raster.reclassify_value_outside_boundary(
            input_file='subbasins.tif',
            area_file='subbasin_merge.tif',
            outside_value=6,
            output_file='subbasins_outside_area_0.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster array to geometries
    with pytest.raises(Exception) as exc_info:
        raster.array_to_geometries(
            raster_file='stream.tif',
            select_values=[5, 6],
            shape_file='stream_polygon.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster files merging
    with pytest.raises(Exception) as exc_info:
        raster.merging_files(
            folder_path='folder_path',
            raster_file='subbasin_merge.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster extension to mask area
    with pytest.raises(Exception) as exc_info:
        raster.extension_to_mask_with_fill_value(
            input_file='subbasin_merge.tif',
            mask_file='dem.tif',
            fill_value=1,
            output_file='subbasin_merge_extended.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster value extraction by mask
    with pytest.raises(Exception) as exc_info:
        raster.extract_value_by_mask(
            input_file='flwdir.tif',
            mask_file='stream.tif',
            output_file='flwdir_extract.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster value extraction by range
    with pytest.raises(Exception) as exc_info:
        raster.extract_value_by_range(
            input_file='stream.tif',
            output_file='stream_value_extract_by_range.tifff',
            lower_bound=3,
            upper_bound=6
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster driver conversion
    with pytest.raises(Exception) as exc_info:
        raster.driver_convert(
            input_file='flwdir.tif',
            target_driver='RST',
            output_file='flwdir.rsttt'
        )
    assert exc_info.value.args[0] == message['error_driver']


def test_error_resampling_method(
    raster,
    message
):

    # raster resolution rescaling
    with pytest.raises(Exception) as exc_info:
        raster.resolution_rescaling(
            input_file='dem.tif',
            target_resolution=32,
            resampling_method='bilinearr',
            output_file='dem_32m.tif'
        )
    assert exc_info.value.args[0] == message['error_resampling']
    # raster resolution rescaling with mask
    with pytest.raises(Exception) as exc_info:
        raster.resolution_rescaling_with_mask(
            input_file='dem_32m.tif',
            mask_file='dem.tif',
            resampling_method='bilinearr',
            output_file='dem_16m.tif'
        )
    assert exc_info.value.args[0] == message['error_resampling']
    # raster Coordinate Reference System reprojectoion
    with pytest.raises(Exception) as exc_info:
        raster.crs_reprojection(
            input_file='dem.tif',
            resampling_method='bilinearr',
            target_crs='EPSG:4326',
            output_file='dem_EPSG4326.tif'
        )
    assert exc_info.value.args[0] == message['error_resampling']


def test_error_others(
    raster
):

    # raster value extraction by range
    with pytest.raises(Exception) as exc_info:
        raster.extract_value_by_range(
            input_file='stream.tif',
            output_file='stream_value_extract_by_range.tif'
        )
    assert exc_info.value.args[0] == 'At least one of the lower or upper bounds must be specified.'
