import os
import rasterio
import geopandas
from .core import Core


class PackageData:

    '''
    Provides access to datasets included in the :mod:`GeoAnalyze` package.
    '''

    def raster_dem(
        self,
        dem_file: str
    ) -> rasterio.profiles.Profile:

        '''
        Retrieves the Digital Elevation Model (DEM) raster data.

        Parameters
        ----------
        dem_file : str
            Path to save the DEM raster file.

        Returns
        -------
        profile
            A profile containing metadata about the output raster.
        '''

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(dem_file)
        if check_file is True:
            pass
        else:
            raise Exception('Could not retrieve driver from the file path.')

        # data file path
        data_file = os.path.join(
            os.path.dirname(__file__), 'data', 'dem_extended_Oulanka_Finland.tif'
        )

        # saving output raster
        with rasterio.open(data_file) as data_raster:
            raster_profile = data_raster.profile
            raster_array = data_raster.read(1)
            with rasterio.open(fp=dem_file, mode='w', **raster_profile) as dem_raster:
                dem_raster.write(raster_array, 1)

        return raster_profile

    @property
    def geodataframe_stream(
        self,
    ) -> geopandas.GeoDataFrame:

        '''
        Retrieves the GeoDataFrame of stream lines.
        '''

        # data file path
        data_file = os.path.join(
            os.path.dirname(__file__), 'data', 'stream_Oulanka.shp'
        )

        # polygon GeoDataFrame
        gdf = geopandas.read_file(data_file)

        return gdf

    @property
    def geodataframe_lake(
        self,
    ) -> geopandas.GeoDataFrame:

        '''
        Retrieves the GeoDataFrame of lake polygons.
        '''

        # data file path
        data_file = os.path.join(
            os.path.dirname(__file__), 'data', 'lake.shp'
        )

        # polygon GeoDataFrame
        gdf = geopandas.read_file(data_file)

        return gdf
