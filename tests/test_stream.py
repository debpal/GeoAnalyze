import os
import tempfile
import shapely
import geopandas
import GeoAnalyze
import pytest


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
    stream
):

    # data folder
    data_folder = os.path.join(os.path.dirname(__file__), 'data')

    with tempfile.TemporaryDirectory() as tmp_dir:
        # saving stream shapefile in temporary directory
        transfer_list = GeoAnalyze.File().transfer_by_name(
            src_folder=data_folder,
            dst_folder=tmp_dir,
            file_names=['stream']
        )
        assert 'stream.shp' in transfer_list
        # read stream GeoDataFrame
        stream_file = os.path.join(tmp_dir, 'stream.shp')
        stream_gdf = geopandas.read_file(stream_file)
        # checking flow path direction from upstream to downstream
        check_flwpath = stream.flw_path_us2ds_check(
            stream_file=stream_file
        )
        assert check_flwpath
        # reversing flow path direction
        stream.flw_path_reverse(
            input_file=stream_file,
            output_file=os.path.join(tmp_dir, 'stream_reverse.shp')
        )
        assert stream.flw_path_us2ds_check(os.path.join(tmp_dir, 'stream_reverse.shp')) is False
        # connected adjacent downstream segement identifier
        cds_gdf = stream.connectivity_adjacent_downstream_segment(
            input_file=stream_file,
            stream_col='flw_id',
            output_file=os.path.join(tmp_dir, 'stream_adjacent_ds_id.shp')
        )
        assert cds_gdf['ds_id'].iloc[0] == 4
        assert cds_gdf['ds_id'].iloc[-2] == 11
        # connected adjacent upstream segement identifiers
        aul_df = stream.connectivity_adjacent_upstream_segment(
            stream_file=stream_file,
            stream_col='flw_id',
            csv_file=os.path.join(tmp_dir, 'stream_adjacent_us_id.csv')
        )
        assert len(aul_df) == 16
        # connectivity from upstream to downstream
        us2ds_dict = stream.connectivity_upstream_to_downstream(
            stream_file=stream_file,
            stream_col='flw_id',
            json_file=os.path.join(tmp_dir, 'stream_us2ds.json')
        )
        assert us2ds_dict[1] == [4, 7, 8, 10, 11]
        assert us2ds_dict[5] == [7, 8, 10, 11]
        assert us2ds_dict[6] == [8, 10, 11]
        # connectivity from downstream to upstream
        ds2us_dict = stream.connectivity_downstream_to_upstream(
            stream_file=stream_file,
            stream_col='flw_id',
            json_file=os.path.join(tmp_dir, 'stream_ds2us.json')
        )
        assert ds2us_dict[1] == []
        assert ds2us_dict[4] == [[1, 3]]
        assert ds2us_dict[7] == [[4, 5], [1, 3]]
        # connectivity DataFrame from downstream to upstream
        ul_df = stream.connectivity_to_all_upstream_segments(
            stream_file=stream_file,
            stream_col='flw_id',
            csv_file=os.path.join(tmp_dir, 'stream_ul.csv')
        )
        assert len(ul_df) == 36
        # connectivity remove of targeted segments and their upstream paths
        remove1_gdf = stream.connectivity_remove_to_headwater(
            input_file=stream_file,
            stream_col='flw_id',
            remove_segments=[],
            output_file=os.path.join(tmp_dir, 'stream_connectivity_cut.shp')
        )
        assert len(remove1_gdf) == 11
        remove2_gdf = stream.connectivity_remove_to_headwater(
            input_file=stream_file,
            stream_col='flw_id',
            remove_segments=[4, 1],
            output_file=os.path.join(tmp_dir, 'stream_connectivity_cut.shp')
        )
        assert 4 not in remove2_gdf['flw_id'].tolist()
        assert 1 not in remove2_gdf['flw_id'].tolist()
        assert 3 not in remove2_gdf['flw_id'].tolist()
        # merge split segments in a stream network
        merged_gdf = stream.connectivity_merge_of_split_segments(
            input_file=os.path.join(tmp_dir, 'stream_connectivity_cut.shp'),
            stream_col='flw_id',
            output_file=os.path.join(tmp_dir, 'stream_connectivity_cut_merged.shp'),
            json_file=os.path.join(tmp_dir, 'stream_connectivity_cut_merged_information.json')
        )
        assert len(merged_gdf) == 7
        assert 5 not in merged_gdf['flw_id'].tolist()
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
        # headwater points
        hw_gdf = stream.point_headwaters(
            input_file=stream_file,
            stream_col='flw_id',
            output_file=os.path.join(tmp_dir, 'headwater_points.shp')
        )
        assert len(hw_gdf) == 6
        assert all(hw_gdf.geometry.geom_type == 'Point')
        assert 4 not in hw_gdf['flw_id'].tolist()
        assert 10 not in hw_gdf['flw_id'].tolist()
        # Strahler stream order
        strahler_gdf = stream.order_strahler(
            input_file=stream_file,
            stream_col='flw_id',
            output_file=os.path.join(tmp_dir, 'strahler.shp')
        )
        assert strahler_gdf['strahler'].max() == 2
        # Shreve stream order
        shreve_gdf = stream.order_shreve(
            input_file=stream_file,
            stream_col='flw_id',
            output_file=os.path.join(tmp_dir, 'shreve.shp')
        )
        assert shreve_gdf['shreve'].max() == 6
        # box touching the selected segment in a stream path
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
            stream.flw_path_us2ds_check(
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
        # connected adjacent downstream segement identifier
        with pytest.raises(Exception) as exc_info:
            stream.connectivity_adjacent_downstream_segment(
                input_file=point_file,
                stream_col='flw_id',
                output_file='stream_ds_id.shp'
            )
        assert exc_info.value.args[0] == message['error_geometry']
        # connected adjacent uptream segement identifier
        with pytest.raises(Exception) as exc_info:
            stream.connectivity_adjacent_upstream_segment(
                stream_file=point_file,
                stream_col='flw_id',
                csv_file='stream_adjacent_us_id.csv'
            )
        assert exc_info.value.args[0] == message['error_geometry']
        # connectivity from upstream to downstream
        with pytest.raises(Exception) as exc_info:
            stream.connectivity_upstream_to_downstream(
                stream_file=point_file,
                stream_col='flw_id',
                json_file='stream_us2ds.json'
            )
        assert exc_info.value.args[0] == message['error_geometry']
        # connectivity from downstream to upstream
        with pytest.raises(Exception) as exc_info:
            stream.connectivity_downstream_to_upstream(
                stream_file=point_file,
                stream_col='flw_id',
                json_file='stream_ds2us.json'
            )
        assert exc_info.value.args[0] == message['error_geometry']
        # connectivity DataFrame from downstream to upstream
        with pytest.raises(Exception) as exc_info:
            stream.connectivity_to_all_upstream_segments(
                stream_file=point_file,
                stream_col='flw_id',
                csv_file='stream_ul.csv'
            )
        assert exc_info.value.args[0] == message['error_geometry']
        # connectivity remove of targeted segments and their upstream paths
        with pytest.raises(Exception) as exc_info:
            stream.connectivity_remove_to_headwater(
                input_file=point_file,
                stream_col='flw_id',
                remove_segments=[4],
                output_file='stream_connectivity_cut.shp'
            )
        assert exc_info.value.args[0] == message['error_geometry']
        # merge split segments in a stream network
        with pytest.raises(Exception) as exc_info:
            stream.connectivity_merge_of_split_segments(
                input_file=point_file,
                stream_col='flw_id',
                output_file='stream_connectivity_cut_merged.shp',
                json_file='stream_connectivity_cut_merged_information.json'
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
        # headwater points
        with pytest.raises(Exception) as exc_info:
            stream.point_headwaters(
                input_file=point_file,
                stream_col='flw_id',
                output_file=os.path.join(tmp_dir, 'headwater_points.shp')
            )
        assert exc_info.value.args[0] == message['error_geometry']
        # Strahler stream order
        with pytest.raises(Exception) as exc_info:
            stream.order_strahler(
                input_file=point_file,
                stream_col='flw_id',
                output_file=os.path.join(tmp_dir, 'strahler.shp')
            )
        assert exc_info.value.args[0] == message['error_geometry']
        # Shreve stream order
        with pytest.raises(Exception) as exc_info:
            stream.order_shreve(
                input_file=point_file,
                stream_col='flw_id',
                output_file=os.path.join(tmp_dir, 'shreve.shp')
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
        stream.connectivity_adjacent_downstream_segment(
            input_file='stream.shp',
            stream_col='flw_id',
            output_file='stream_ds_id.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # connectivity remove of targeted segments and their upstream paths
    with pytest.raises(Exception) as exc_info:
        stream.connectivity_remove_to_headwater(
            input_file='stream.shp',
            stream_col='flw_id',
            remove_segments=[4],
            output_file='stream_connectivity_cut.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # merge split segments in a stream network
    with pytest.raises(Exception) as exc_info:
        stream.connectivity_merge_of_split_segments(
            input_file='stream.shp',
            stream_col='flw_id',
            output_file='stream_connectivity_cut_merged.sh',
            json_file='stream_connectivity_cut_merged_information.json'
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
    # headwater points
    with pytest.raises(Exception) as exc_info:
        stream.point_headwaters(
            input_file='stream.shp',
            stream_col='flw_id',
            output_file='headwater_points.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # Strahler stream order
    with pytest.raises(Exception) as exc_info:
        stream.order_strahler(
            input_file='stream.shp',
            stream_col='flw_id',
            output_file='strahler.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # Shreve stream order
    with pytest.raises(Exception) as exc_info:
        stream.order_shreve(
            input_file='stream.shp',
            stream_col='flw_id',
            output_file='shreve.sh'
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
