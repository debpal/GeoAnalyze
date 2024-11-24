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
        file_path: str
    ) -> bool:

        '''
        Returns whether the given file path is valid to write a GeoDataFrame.

        Parameters
        ----------
        file_path : str
            File path to save the GeoDataFrame.

        Returns
        -------
        bool
            True if the file path is valid, False otherwise.
        '''

        try:
            pyogrio.detect_write_driver(file_path)
            output = True
        except Exception:
            output = False

        return output

    def is_valid_raster_driver(
        self,
        file_path: str
    ) -> bool:

        '''
        Returns whether the given file path is a valid raster file.

        Parameters
        ----------
        file_path : str
            File path to save the raster.

        Returns
        -------
        bool
            True if the file path is valid, False otherwise.
        '''

        try:
            rasterio.drivers.driver_from_extension(file_path)
            output = True
        except Exception:
            output = False

        return output

    def shapefile_geometry_type(
        self,
        file_path: str
    ) -> str:

        '''
        Return the geometry type of the shapefile.

        Parameters
        ----------
        file_path : str
            Path of the shapefile.

        Returns
        -------
        str
            Geometry type of the shapefile.
        '''

        with fiona.open(file_path) as input_shape:
            output = str(input_shape.schema['geometry'])

        return output

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
