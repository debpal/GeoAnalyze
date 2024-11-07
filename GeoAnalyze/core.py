# import os
# import typing
# import string
# import fiona
import pyogrio
# import rasterio.drivers


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
