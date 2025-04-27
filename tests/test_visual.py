import os
import tempfile
import GeoAnalyze
import matplotlib.pyplot
import pytest


@pytest.fixture(scope='class')
def packagedata():

    yield GeoAnalyze.PackageData()


@pytest.fixture(scope='class')
def visual():

    yield GeoAnalyze.Visual()


@pytest.fixture
def message():

    output = {
        'error_figure': 'Input figure file extension is not supported.'
    }

    return output


def test_functions(
    packagedata,
    visual
):

    with tempfile.TemporaryDirectory() as tmp_dir:
        # accessing stream shaepfile from GeoAanlyze package
        packagedata.raster_dem(
            dem_file=os.path.join(tmp_dir, 'dem_extended.tif')
        )
        # accessing stream shaepfile from GeoAanlyze package
        stream_gdf = packagedata.geodataframe_stream
        stream_gdf.to_file(
            os.path.join(tmp_dir, 'stream.shp')
        )
        # raster quick view
        output_figure = visual.quickview_raster(
            raster_file=os.path.join(tmp_dir, 'dem_extended.tif'),
            figure_file=os.path.join(tmp_dir, 'dem_extended.png'),
            gui_window=False
        )
        assert isinstance(output_figure, matplotlib.pyplot.Figure) is True
        assert os.path.exists(os.path.join(tmp_dir, 'dem_extended.png')) is True
        assert sum([file.endswith('.png') for file in os.listdir(tmp_dir)]) == 1
        # shapefile quick view
        output_figure = visual.quickview_geometry(
            shape_file=os.path.join(tmp_dir, 'stream.shp'),
            column_name='flw_id',
            figure_file=os.path.join(tmp_dir, 'stream.png'),
            gui_window=False
        )
        assert isinstance(output_figure, matplotlib.pyplot.Figure) is True
        assert os.path.exists(os.path.join(tmp_dir, 'stream.png')) is True
        assert sum([file.endswith('.png') for file in os.listdir(tmp_dir)]) == 2


def test_error_figure(
    visual,
    message
):

    # raster quick view
    with pytest.raises(Exception) as exc_info:
        visual.quickview_raster(
            raster_file='dem_extended.tif',
            figure_file='dem_extended.pn'
        )
    assert exc_info.value.args[0] == message['error_figure']
    # shapefile quick view
    with pytest.raises(Exception) as exc_info:
        visual.quickview_geometry(
            shape_file='stream.shp',
            column_name='flw_id',
            figure_file='stream.pn'
        )
    assert exc_info.value.args[0] == message['error_figure']
