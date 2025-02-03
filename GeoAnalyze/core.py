import string
import fiona
import pyogrio
import rasterio.drivers


class Core:

    '''
    Provides common functionality used throughout
    the :mod:`GeoAnalyze` package.
    '''

    def is_valid_ogr_driver(
        self,
        shape_file: str
    ) -> bool:

        '''
        Checks whether the given shapefile path is valid and supported.

        Parameters
        ----------
        shape_file : str
            Path to the shapefile to be validated.

        Returns
        -------
        bool
            True if the shapefile path is valid and supported, False otherwise.
        '''

        try:
            pyogrio.detect_write_driver(shape_file)
            output = True
        except Exception:
            output = False

        return output

    def is_valid_raster_driver(
        self,
        raster_file: str
    ) -> bool:

        '''
        Checks whether the given raster file path is valid and supported.

        Parameters
        ----------
        raster_file : str
            Path to the raster file to be validated.

        Returns
        -------
        bool
            True if the raster file path is valid and supported, False otherwise.
        '''

        try:
            rasterio.drivers.driver_from_extension(raster_file)
            output = True
        except Exception:
            output = False

        return output

    # pytest pending
    def shapefile_geometry_type(
        self,
        shape_file: str
    ) -> str:

        '''
        Return the geometry type of the shapefile.

        Parameters
        ----------
        shape_file : str
            Path of the shapefile.

        Returns
        -------
        str
            Geometry type of the shapefile.
        '''

        with fiona.open(shape_file) as input_shape:
            output = str(input_shape.schema['geometry'])

        return output

    # pytest pending
    def _tmp_df_column_name(
        self,
        df_columns: list[str]
    ) -> str:

        '''
        Parameters
        ----------
        df_columns : list
            Input list of DataFrame columns.

        Returns
        -------
        str
            Temporary column name that does not belong to the
            list of existing column names of the DataFrame.
        '''

        max_length = max(
            [len(col) for col in df_columns]
        )

        output = string.ascii_lowercase[:(max_length + 1)]

        return output

    def _github_action(
        self,
        integer: int
    ) -> str:

        '''
        A simple function that converts an integer to a string,
        which can trigger a GitHub action due to the modification of a '.py' file.
        '''

        output = str(integer)

        return output
