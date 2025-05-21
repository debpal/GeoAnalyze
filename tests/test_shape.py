import os
import tempfile
import geopandas
import GeoAnalyze
import pytest


@pytest.fixture(scope='class')
def shape():

    yield GeoAnalyze.Shape()


@pytest.fixture
def point_gdf():

    gdf = GeoAnalyze.core.Core()._geodataframe_point

    return gdf


@pytest.fixture
def message():

    output = {
        'error_driver': 'Could not retrieve driver from the file path.',
        'error_geometry': 'Input shapefile must have geometries of type Polygon.'
    }

    return output


def test_functions(
    shape
):

    # data folder
    data_folder = os.path.join(os.path.dirname(__file__), 'data')

    with tempfile.TemporaryDirectory() as tmp_dir:
        # saving lake shapefile in temporary directory
        transfer_list = GeoAnalyze.File().transfer_by_name(
            src_folder=data_folder,
            dst_folder=tmp_dir,
            file_names=['lake']
        )
        assert 'lake.shp' in transfer_list
        # read lake GeoDataFrame
        lake_file = os.path.join(tmp_dir, 'lake.shp')
        lake_gdf = geopandas.read_file(lake_file)
        # non-decimal whole value float columns to integer columns
        int_gdf = shape.column_nondecimal_float_to_int_type(
            input_file=lake_file,
            output_file=os.path.join(tmp_dir, 'lake.shp')
        )
        assert 'int' in str(int_gdf.dtypes.iloc[-4])
        # adding ID column
        assert 'lid' not in lake_gdf.columns
        id_gdf = shape.column_add_for_id(
            input_file=lake_file,
            column_name='lid',
            output_file=lake_file
        )
        assert 'lid' in id_gdf.columns
        # deleting columns
        assert 'nimi' in lake_gdf.columns
        delete_gdf = shape.column_delete(
            input_file=lake_file,
            delete_cols=['nimi'],
            output_file=lake_file
        )
        assert 'nimi' not in delete_gdf.columns
        # retaining columns
        retain_gdf = shape.column_retain(
            input_file=lake_file,
            retain_cols=['lid'],
            output_file=lake_file
        )
        assert list(retain_gdf.columns) == ['lid', 'geometry']
        # Coordinate Reference System reprojection
        reproject_gdf = shape.crs_reprojection(
            input_file=lake_file,
            target_crs='EPSG:4326',
            output_file=os.path.join(tmp_dir, 'crs_reproject.shp')
        )
        assert str(reproject_gdf.crs) == 'EPSG:4326'
        # rectangular bounding box
        box_gdf = shape.boundary_box(
            input_file=lake_file,
            output_file=os.path.join(tmp_dir, 'box_lake.shp')
        )
        assert len(box_gdf) == 1
        # converting polygons to boundary lines
        shape.polygons_to_boundary_lines(
            input_file=lake_file,
            output_file=os.path.join(tmp_dir, 'line.shp')
        )
        geometry_type = GeoAnalyze.core.Core().shapefile_geometry_type(
            shape_file=os.path.join(tmp_dir, 'line.shp')
        )
        assert geometry_type == 'LineString'
        # polygon filling
        lake_hole = all(lake_gdf.geometry.apply(lambda x: len(list(x.interiors)) == 0))
        assert lake_hole is False
        lakeunion_gdf = geopandas.GeoDataFrame(
            data={'luid': [1], 'geometry': [lake_gdf.union_all()]},
            crs=lake_gdf.crs
        )
        lakeunion_gdf.to_file(os.path.join(tmp_dir, 'lake_union.shp'))
        lakefill_gdf = shape.polygon_fill(
            input_file=os.path.join(tmp_dir, 'lake_union.shp'),
            output_file=os.path.join(tmp_dir, 'lake_union_fill.shp'),
            explode=True
        )
        lake_hole = all(lakefill_gdf.geometry.apply(lambda x: len(list(x.interiors)) == 0))
        assert lake_hole
        # polygon filling after merging
        lake_hole = all(lake_gdf.geometry.apply(lambda x: len(list(x.interiors)) == 0))
        assert lake_hole is False
        lakefill_gdf = shape.polygon_fill_after_merge(
            input_file=lake_file,
            column_name='lid',
            output_file=os.path.join(tmp_dir, 'lake_fill.shp')
        )
        lake_hole = all(lakefill_gdf.geometry.apply(lambda x: len(list(x.interiors)) == 0))
        assert lake_hole
        assert len(lake_gdf) > len(lakefill_gdf)
        # polygon count by cumulative sum percentages of areas
        cumarea_count = shape.polygon_count_by_cumsum_area(
            shape_file=lake_file
        )
        assert len(cumarea_count) == 20
        # removing polygons by cumulative area percentage cutoff
        lakecutoff_gdf = shape.polygons_remove_by_cumsum_area_percent(
            input_file=lake_file,
            percent_cutoff=90,
            output_file=os.path.join(tmp_dir, 'lake_cutoff_90.shp'),
            index_sort=True
        )
        assert len(lakecutoff_gdf) == 10
        # pass test for extracting spatial join geometries
        # stream_gdf = packagedata.geodataframe_stream
        # stream_gdf.to_file(os.path.join(tmp_dir, 'stream.shp'))
        # stre_file = os.path.join(data_folder, 'lake_Oulanka.shp')
        extract_gdf = shape.extract_spatial_join_geometries(
            input_file=lake_file,
            overlay_file=os.path.join(data_folder, 'stream.shp'),
            output_file=os.path.join(tmp_dir, 'lake_extracted.shp')
        )
        assert len(extract_gdf) == 6
        # aggregating geometries from shapefile
        with tempfile.TemporaryDirectory() as tmp2_dir:
            lake1_gdf = lake_gdf.iloc[:50, :]
            lake1_gdf.to_file(os.path.join(tmp2_dir, 'lake_1.shp'))
            lake2_gdf = lake_gdf.iloc[-50:, :]
            lake2_gdf.to_file(os.path.join(tmp2_dir, 'lake_2.shp'))
            aggregate_gdf = shape.aggregate_geometries(
                folder_path=tmp2_dir,
                geometry_type='Polygon',
                column_name='aid',
                output_file=os.path.join(tmp_dir, 'aggregate.shp')
            )
            assert len(aggregate_gdf) == 100
            # error test for missing Coordinate Reference System
            lake2_gdf = lake2_gdf.set_crs('EPSG:4326', allow_override=True)
            lake2_gdf.to_file(os.path.join(tmp2_dir, 'lake_2.shp'))
            with pytest.raises(Exception) as exc_info:
                shape.aggregate_geometries(
                    folder_path=tmp2_dir,
                    geometry_type='Polygon',
                    column_name='aid',
                    output_file=os.path.join(tmp_dir, 'aggregate.shp')
                )
            assert exc_info.value.args[0] == 'Not all shapefiles have the same Coordinate Reference System.'


def test_error_shapefile_driver(
    shape,
    message
):

    # non-decimal whole value float columns to integer columns
    with pytest.raises(Exception) as exc_info:
        shape.column_nondecimal_float_to_int_type(
            input_file='input.shp',
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # retaining columns
    with pytest.raises(Exception) as exc_info:
        shape.column_retain(
            input_file='input.shp',
            retain_cols=['C1'],
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # deleting columns
    with pytest.raises(Exception) as exc_info:
        shape.column_delete(
            input_file='input.shp',
            delete_cols=['C1'],
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # adding ID column
    with pytest.raises(Exception) as exc_info:
        shape.column_add_for_id(
            input_file='input.shp',
            column_name=['C1'],
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # Coordinate Reference System reprojection
    with pytest.raises(Exception) as exc_info:
        shape.crs_reprojection(
            input_file='input.shp',
            target_crs='EPSG:3067',
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # rectangular bounding box
    with pytest.raises(Exception) as exc_info:
        shape.boundary_box(
            input_file='input.shp',
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # converting polygons to boundary lines
    with pytest.raises(Exception) as exc_info:
        shape.polygons_to_boundary_lines(
            input_file='input.shp',
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # polygon filling
    with pytest.raises(Exception) as exc_info:
        shape.polygon_fill(
            input_file='input.shp',
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # polygon filling after merge
    with pytest.raises(Exception) as exc_info:
        shape.polygon_fill_after_merge(
            input_file='input.shp',
            column_name='lid',
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # removing polygons by cumulative area percentage cutoff
    with pytest.raises(Exception) as exc_info:
        shape.polygons_remove_by_cumsum_area_percent(
            input_file='input.shp',
            percent_cutoff=90,
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # extracting spatial join geometries
    with pytest.raises(Exception) as exc_info:
        shape.extract_spatial_join_geometries(
            input_file='input.shp',
            overlay_file='overlay.shp',
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']
    # aggregating geometries
    with pytest.raises(Exception) as exc_info:
        shape.aggregate_geometries(
            folder_path='input_folder',
            geometry_type='Polygon',
            column_name='aid',
            output_file='output.sh'
        )
    assert exc_info.value.args[0] == message['error_driver']


def test_error_geometry(
    shape,
    point_gdf,
    message
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        # saving point GeoDataFrame
        point_file = os.path.join(tmp_dir, 'point.shp')
        point_gdf.to_file(point_file)
        # polygon filling
        with pytest.raises(Exception) as exc_info:
            shape.polygon_fill(
                input_file=point_file,
                output_file='polygon_fill.shp'
            )
        assert exc_info.value.args[0] == message['error_geometry']
        # polygon filling after merge
        with pytest.raises(Exception) as exc_info:
            shape.polygon_fill_after_merge(
                input_file=point_file,
                column_name='lid',
                output_file='polygon_fill.shp'
            )
        assert exc_info.value.args[0] == message['error_geometry']
        # polygon count by cumulative sum percentages of areas
        with pytest.raises(Exception) as exc_info:
            shape.polygon_count_by_cumsum_area(
                shape_file=point_file
            )
        assert exc_info.value.args[0] == message['error_geometry']
        # removing polygons by cumulative area percentage cutoff
        with pytest.raises(Exception) as exc_info:
            shape.polygons_remove_by_cumsum_area_percent(
                input_file=point_file,
                percent_cutoff=90,
                output_file='output.shp'
            )
        assert exc_info.value.args[0] == message['error_geometry']
