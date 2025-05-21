import GeoAnalyze
import pytest


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


def test_error_raster_file_driver(
    raster,
    message
):

    # raster boundary polygon GeoDataFrame
    with pytest.raises(Exception) as exc_info:
        raster.boundary_polygon(
            raster_file='dem.tif',
            shape_file='dem_boundary.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster resolution rescaling
    with pytest.raises(Exception) as exc_info:
        raster.resolution_rescaling(
            input_file='dem.tif',
            target_resolution=32,
            resampling_method='bilinear',
            output_file='dem_32m.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster resolution rescaling with mask
    with pytest.raises(Exception) as exc_info:
        raster.resolution_rescaling_with_mask(
            input_file='dem_32m.tif',
            mask_file='dem.tif',
            resampling_method='bilinear',
            output_file='dem_16m.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster Coordinate Reference System reprojectoion
    with pytest.raises(Exception) as exc_info:
        raster.crs_reprojection(
            input_file='dem.tif',
            resampling_method='bilinear',
            target_crs='EPSG:4326',
            output_file='dem_EPSG4326.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster NoData conversion from value
    with pytest.raises(Exception) as exc_info:
        raster.nodata_conversion_from_value(
            input_file='stream.tif',
            target_value=[1, 9],
            output_file='stream_NoData.tifff',
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster NoData value change
    with pytest.raises(Exception) as exc_info:
        raster.nodata_value_change(
            input_file='dem.tif',
            nodata=0,
            output_file='dem_NoData_0.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster NoData to valid value
    with pytest.raises(Exception) as exc_info:
        raster.nodata_to_valid_value(
            input_file='dem.tif',
            valid_value=0,
            output_file='dem_NoData_0.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # raster NoData extent trimming
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
    # raster array from geometries
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
