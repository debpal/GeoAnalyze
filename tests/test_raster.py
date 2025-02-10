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
        'error_driver': 'Could not retrieve driver from the file path.',
        'error_resampling': f'Input resampling method must be one of {list(GeoAnalyze.core.Core().raster_resampling_method.keys())}.'
    }

    return output


def test_error_raster_file_driver(
    packagedata,
    raster,
    message
):

    # accessing DEM raster file
    with pytest.raises(Exception) as exc_info:
        packagedata.raster_dem(
            dem_file='dem.tifff',
        )
    assert exc_info.value.args[0] == message['error_driver']
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
    # raster NoData value change
    with pytest.raises(Exception) as exc_info:
        raster.nodata_value_change(
            input_file='dem.tif',
            nodata=0,
            output_file='dem_NoData_0.tifff'
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
    # raster NoData conversion from value
    with pytest.raises(Exception) as exc_info:
        raster.nodata_conversion_from_value(
            input_file='stream.tif',
            target_value=[1, 9],
            output_file='stream_NoData.tifff',
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
