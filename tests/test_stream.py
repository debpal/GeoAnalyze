import os
import tempfile
import shapely
import GeoAnalyze
import pytest


@pytest.fixture(scope='class')
def packagedata():

    yield GeoAnalyze.PackageData()


@pytest.fixture(scope='class')
def stream():

    yield GeoAnalyze.Stream()


@pytest.fixture
def message():

    output = {
        'error_driver': 'Could not retrieve driver from the file path.',
        'error_geometry': 'Input shapefile must have geometries of type LineString.'
    }

    return output


@pytest.fixture
def point_gdf():

    gdf = GeoAnalyze.core.Core()._geodataframe_point

    return gdf


def test_functions(
    packagedata,
    stream
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        # accessing stream GeoDataFrame
        stream_file = os.path.join(tmp_dir, 'stream.shp')
        stream_gdf = packagedata.geodataframe_stream
        stream_gdf.to_file(stream_file)
        # checking flow path direction from upstream to downstream
        check_flwpath = stream.is_flw_path_us_to_ds(
            stream_file=stream_file
        )
        assert check_flwpath
        # reversing flow path direction
        stream.flw_path_reverse(
            input_file=stream_file,
            output_file=os.path.join(tmp_dir, 'stream_reverse.shp')
        )
        assert stream.is_flw_path_us_to_ds(os.path.join(tmp_dir, 'stream_reverse.shp')) is False
        # connected downstream segement identifiers
        cds_gdf = stream.connectivity_to_downstream_segment(
            input_file=stream_file,
            stream_col='flw_id',
            output_file=os.path.join(tmp_dir, 'stream_ds_id.shp')
        )
        assert cds_gdf['ds_id'].iloc[0] == 4
        assert cds_gdf['ds_id'].iloc[-2] == 11
        # junction points
        junction_gdf = stream.point_junctions(
            input_file=stream_file,
            stream_col='flw_id',
            output_file=os.path.join(tmp_dir, 'junction_points.shp')
        )
        assert junction_gdf['flw_id'].iloc[0] == [1, 3]
        assert junction_gdf['flw_id'].iloc[-1] == [9, 10]
        # segment's subbasin drainage points
        drainage_gdf = stream.point_segment_subbasin_drainage(
            input_file=stream_file,
            output_file=os.path.join(tmp_dir, 'subbasin_drainage_points.shp')
        )
        assert stream_gdf['geometry'].iloc[0].coords[-2] == drainage_gdf['geometry'].iloc[0].coords[0]
        assert stream_gdf['geometry'].iloc[-1].coords[-1] == drainage_gdf['geometry'].iloc[-1].coords[0]
        # main outlet points
        outlet_gdf = stream.point_main_outlets(
            input_file=stream_file,
            output_file=os.path.join(tmp_dir, 'main_outlet_points.shp')
        )
        assert stream_gdf['geometry'].iloc[-1].coords[-1] == outlet_gdf['geometry'].iloc[-1].coords[0]
        # ox touching the selected segment in a stream path
        selected_line = stream_gdf[stream_gdf['flw_id'] == 3]['geometry'].iloc[0]
        box_gdf = stream.box_touch_selected_segment(
            input_file=stream_file,
            column_name='flw_id',
            column_value=3,
            box_length=500,
            output_file=os.path.join(tmp_dir, 'box.shp')
        )
        polygon = box_gdf.geometry.iloc[0]
        assert selected_line.touches(polygon)
        # box touching the selected segment at endpoint in a stream path
        box_gdf = stream.box_touch_selected_segment_at_endpoint(
            input_file=stream_file,
            column_name='flw_id',
            column_value=3,
            box_length=500,
            output_file=os.path.join(tmp_dir, 'box.shp')
        )
        polygon = box_gdf.geometry.iloc[0]
        assert selected_line.touches(polygon)
        # box crossing the selected segment at endpoint in a stream path
        box_gdf = stream.box_cross_selected_segment_at_endpoint(
            input_file=stream_file,
            column_name='flw_id',
            column_value=3,
            box_length=500,
            output_file=os.path.join(tmp_dir, 'box.shp')
        )
        polygon = box_gdf.geometry.iloc[0]
        intersection = selected_line.intersection(polygon)
        assert isinstance(intersection, shapely.MultiLineString) or len(intersection.coords[:]) > 1


def test_error_geometry(
    stream,
    point_gdf,
    message
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        # saving point GeoDataFrame
        point_file = os.path.join(tmp_dir, 'point.shp')
        point_gdf.to_file(point_file)
        # checking flow path direction
        with pytest.raises(Exception) as exc_info:
            stream.is_flw_path_us_to_ds(
                stream_file=point_file
            )
        assert exc_info.value.args[0] == message['error_geometry']
        # reversing flow path direction
        with pytest.raises(Exception) as exc_info:
            stream.flw_path_reverse(
                input_file=point_file,
                output_file=os.path.join(tmp_dir, 'stream_reverse.shp')
            )
        assert exc_info.value.args[0] == message['error_geometry']
        # connected downstream segement identifiers
        with pytest.raises(Exception) as exc_info:
            stream.connectivity_to_downstream_segment(
                input_file=point_file,
                stream_col='flw_id',
                output_file='stream_ds_id.shp'
            )
        assert exc_info.value.args[0] == message['error_geometry']
        # junction points
        with pytest.raises(Exception) as exc_info:
            stream.point_junctions(
                input_file=point_file,
                stream_col='flw_id',
                output_file='junction_points.shp'
            )
        assert exc_info.value.args[0] == message['error_geometry']
        # segment's subbasin drainage points
        with pytest.raises(Exception) as exc_info:
            stream.point_segment_subbasin_drainage(
                input_file=point_file,
                output_file=os.path.join(tmp_dir, 'subbasin_drainage_points.shp')
            )
        assert exc_info.value.args[0] == message['error_geometry']
        # main outlet points
        with pytest.raises(Exception) as exc_info:
            stream.point_main_outlets(
                input_file=point_file,
                output_file=os.path.join(tmp_dir, 'main_outlet_points.shp')
            )
        assert exc_info.value.args[0] == message['error_geometry']


def test_error_shapefile_driver(
    stream,
    message
):

    # reversing flow path direction
    with pytest.raises(Exception) as exc_info:
        stream.flw_path_reverse(
            input_file='stream_shp',
            output_file='stream_reverse.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # connected downstream segement identifiers
    with pytest.raises(Exception) as exc_info:
        stream.connectivity_to_downstream_segment(
            input_file='stream.shp',
            stream_col='flw_id',
            output_file='stream_ds_id.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # junction points
    with pytest.raises(Exception) as exc_info:
        stream.point_junctions(
            input_file='stream.shp',
            stream_col='flw_id',
            output_file='junction_points.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # segment's subbasin drainage points
    with pytest.raises(Exception) as exc_info:
        stream.point_segment_subbasin_drainage(
            input_file='stream.shp',
            output_file='subbasin_drainage_points.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # main outlet points
    with pytest.raises(Exception) as exc_info:
        stream.point_main_outlets(
            input_file='stream.shp',
            output_file='main_outlet_points.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # box touching the selected segment in a stream path
    with pytest.raises(Exception) as exc_info:
        stream.box_touch_selected_segment(
            input_file='stream.shp',
            column_name='flw_id',
            column_value=3,
            box_length=500,
            output_file='box.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # box touching the selected segment at endpoint in a stream path
    with pytest.raises(Exception) as exc_info:
        stream.box_touch_selected_segment_at_endpoint(
            input_file='stream.shp',
            column_name='flw_id',
            column_value=3,
            box_length=500,
            output_file='box.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # box crossing the selected segment at endpoint in a stream path
    with pytest.raises(Exception) as exc_info:
        stream.box_cross_selected_segment_at_endpoint(
            input_file='stream.shp',
            column_name='flw_id',
            column_value=3,
            box_length=500,
            output_file='box.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
