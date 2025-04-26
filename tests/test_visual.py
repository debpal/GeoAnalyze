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
        # saving DEM raster file fo packaged data
        packagedata.raster_dem(
            dem_file=os.path.join(tmp_dir, 'dem_extended.tif')
        )
        # raster quick view test
        output_figure = visual.quickview_raster(
            raster_file=os.path.join(tmp_dir, 'dem_extended.tif'),
            figure_file=os.path.join(tmp_dir, 'dem_extended.png'),
            gui_window=False
        )
        assert isinstance(output_figure, matplotlib.pyplot.Figure) is True
        assert os.path.exists(os.path.join(tmp_dir, 'dem_extended.png')) is True
        assert sum([file.endswith('.png') for file in os.listdir(tmp_dir)]) == 1


def test_error_figure(
    visual,
    message
):

    with pytest.raises(Exception) as exc_info:
        visual.quickview_raster(
            raster_file='dem_extended.tif',
            figure_file='dem_extended.pn'
        )
    assert exc_info.value.args[0] == message['error_figure']
