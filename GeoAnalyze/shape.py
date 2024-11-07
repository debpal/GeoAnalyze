# import os
import geopandas
# import shapely
from .core import Core
# from .file import File


class Shape:

    '''
    Provides functionality for shapefile operations.
    '''

    def columns_retain(
        self,
        input_file: str,
        retain_cols: list[str],
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Return a GeoDataFrame with geometry and specified columns.
        Useful when the user wants to remove unnecessary columns
        while retaining a few required ones.

        Parameters
        ----------
        input_file : str
            Path to the input shapefile.

        retain_cols : list
            List of columns, apart from 'geometry', to include in the output shapefile.

        output_file : str
            Shapefile path to save the output GeoDataFrame.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the speificed columns.
        '''

        # check output file
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is True:
            pass
        else:
            raise Exception('Could not retrieve driver from the file path.')

        # input GeoDataFrame
        gdf = geopandas.read_file(input_file)

        # list of columns to drop
        retain_cols = retain_cols + ['geometry']
        drop_cols = [col for col in gdf.columns if col not in retain_cols]
        gdf = gdf.drop(columns=drop_cols)

        # saving output GeoDataFrame
        gdf.to_file(output_file)

        return gdf

    def columns_delete(
        self,
        input_file: str,
        delete_cols: list[str],
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Delete specified columns from a GeoDataFrame.
        Useful when the user wants to delete specific columns.

        Parameters
        ----------
        input_file : str
            Path to the input shapefile.

        delete_cols : list
            List of columns, apart from 'geometry', to delete in the output shapefile.

        output_file : str
            Shapefile path to save the output GeoDataFrame.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame with trhe deletion of speificed columns.
        '''

        # check output file
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is True:
            pass
        else:
            raise Exception('Could not retrieve driver from the file path.')

        # input GeoDataFrame
        gdf = geopandas.read_file(input_file)

        # list of columns to drop
        delete_cols.remove('geometry') if 'geometry' in delete_cols else delete_cols
        gdf = gdf.drop(columns=delete_cols)

        # saving output GeoDataFrame
        gdf.to_file(output_file)

        return gdf

    def adding_id_column(
        self,
        input_file: str,
        column_name: str,
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Adds an ID column to the geometries,
        starting from 1 and incrementing by 1.

        Parameters
        ----------
        input_file : str
            Path to the input shapefile

        colums_name : str
            Name of the ID column to be added.

        output_file : str
            Shapefile path to save the output GeoDataFrame.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame with an added ID column,
            where values start from 1 and increase by 1.
        '''

        # check output file
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is True:
            pass
        else:
            raise Exception('Could not retrieve driver from the file path.')

        # input GeoDataFrame
        gdf = geopandas.read_file(input_file)

        # insert ID column
        gdf.insert(0, column_name, list(range(1, gdf.shape[0] + 1)))

        # saving output GeoDataFrame
        gdf.to_file(output_file)

        return gdf
