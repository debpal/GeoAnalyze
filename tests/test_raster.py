import os
import tempfile
import geopandas
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
        # accessing polygon GeoDataFrame
        polygon_gdf = packagedata.get_polygon_gdf
        assert isinstance(polygon_gdf, geopandas.GeoDataFrame)
        polygon_gdf.to_file(os.path.join(tmp_dir, 'polygon.shp'))
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
        # pass test for raster resolution rescaling
        output_profile = raster.resolution_rescaling(
            input_file=dem_file,
            target_resolution=32,
            resampling_method='bilinear',
            output_file=os.path.join(tmp_dir, 'dem_32m.tif')
        )
        assert output_profile['width'] == 1856
        # pass test for raster resolution rescaling with mask
        output_profile = raster.resolution_rescaling_with_mask(
            input_file=os.path.join(tmp_dir, 'dem_32m.tif'),
            mask_file=os.path.join(tmp_dir, 'dem.tif'),
            resampling_method='bilinear',
            output_file=os.path.join(tmp_dir, 'dem_16m.tif')
        )
        assert output_profile['height'] == 3790
        # pass test for raster Coordinate Reference System reprojectoion
        output_profile = raster.crs_reprojection(
            input_file=os.path.join(tmp_dir, 'dem_32m.tif'),
            resampling_method='bilinear',
            target_crs='EPSG:4326',
            output_file=os.path.join(tmp_dir, 'dem_32m_EPSG4326.tif')
        )
        assert output_profile['height'] == 1056
        # pass test for raster NoData value change
        output_profile = raster.nodata_value_change(
            input_file=os.path.join(tmp_dir, 'dem_32m.tif'),
            nodata=0,
            output_file=os.path.join(tmp_dir, 'dem_32m_NoData_0.tif'),
            dtype='float32'
        )
        assert output_profile['nodata'] == 0
        # pass test for raster clipping by shapes
        output_profile = raster.clipping_by_shapes(
            input_file=os.path.join(tmp_dir, 'dem_32m.tif'),
            shape_file=os.path.join(tmp_dir, 'polygon.shp'),
            output_file=os.path.join(tmp_dir, 'dem_32m_clipped.tif')
        )
        assert output_profile['width'] == 979


def test_error_raster_file_driver(
    packagedata,
    raster,
    message
):

    # error test of invalid file path for accessing DEM raster file
    with pytest.raises(Exception) as exc_info:
        packagedata.get_dem(
            dem_file='dem.tifff',
        )
    assert exc_info.value.args[0] == message['error_driver']
    # error test of invalid file path for raster boundary polygon GeoDataFrame
    with pytest.raises(Exception) as exc_info:
        raster.boundary_polygon(
            raster_file='dem.tif',
            shape_file='dem_boundary.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # error test of invalid file path for raster resolution rescaling
    with pytest.raises(Exception) as exc_info:
        raster.resolution_rescaling(
            input_file='dem.tif',
            target_resolution=32,
            resampling_method='bilinear',
            output_file='dem_32m.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # error test of invalid file path for raster resolution rescaling with mask
    with pytest.raises(Exception) as exc_info:
        raster.resolution_rescaling_with_mask(
            input_file='dem_32m.tif',
            mask_file='dem.tif',
            resampling_method='bilinear',
            output_file='dem_16m.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # error test of invalid file path for raster Coordinate Reference System reprojectoion
    with pytest.raises(Exception) as exc_info:
        raster.crs_reprojection(
            input_file='dem.tif',
            resampling_method='bilinear',
            target_crs='EPSG:4326',
            output_file='dem_EPSG4326.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # error test of invalid file path for raster NoData value change
    with pytest.raises(Exception) as exc_info:
        raster.nodata_value_change(
            input_file='dem.tif',
            nodata=0,
            output_file='dem_NoData_0.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # error test of invalid file path for raster array from geometries
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
    # error test of invalid file path for raster NoData conversion from value
    with pytest.raises(Exception) as exc_info:
        raster.nodata_conversion_from_value(
            input_file='stream.tif',
            target_value=[1, 9],
            output_file='stream_NoData.tifff',
        )
    assert exc_info.value.args[0] == message['error_driver']
    # error test of invalid file path for raster clipping by shapes
    with pytest.raises(Exception) as exc_info:
        raster.clipping_by_shapes(
            input_file='dem.tif',
            shape_file='polygon.shp',
            output_file='dem_clipped.tifff'
        )
    assert exc_info.value.args[0] == message['error_driver']


def test_error_resampling_method(
    raster,
    message
):

    # error test of resampling method for raster resolution rescaling
    with pytest.raises(Exception) as exc_info:
        raster.resolution_rescaling(
            input_file='dem.tif',
            target_resolution=32,
            resampling_method='bilinearr',
            output_file='dem_32m.tif'
        )
    assert exc_info.value.args[0] == message['error_resampling']
    # error test of resampling method for raster resolution rescaling with mask
    with pytest.raises(Exception) as exc_info:
        raster.resolution_rescaling_with_mask(
            input_file='dem_32m.tif',
            mask_file='dem.tif',
            resampling_method='bilinearr',
            output_file='dem_16m.tif'
        )
    assert exc_info.value.args[0] == message['error_resampling']
    # error test of resampling method for raster Coordinate Reference System reprojectoion
    with pytest.raises(Exception) as exc_info:
        raster.crs_reprojection(
            input_file='dem.tif',
            resampling_method='bilinearr',
            target_crs='EPSG:4326',
            output_file='dem_EPSG4326.tif'
        )
    assert exc_info.value.args[0] == message['error_resampling']
