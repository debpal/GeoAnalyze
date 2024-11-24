import rasterio
import pandas
import numpy


class Raster:

    '''
    Provides functionality for raster file operations.
    '''

    def count_non_nodata_cells(
        self,
        raster_file: str
    ) -> int:

        '''
        Count the number of cells in the raster file that have valid data.

        Parameters
        ----------
        raster_file : str
            Path of the input raster file.

        Returns
        -------
        int
            The numer of cells with valid data in the raster file.
        '''

        with rasterio.open(raster_file) as input_raster:
            raster_nodata = input_raster.nodata
            raster_array = input_raster.read(1)
            output = int((raster_array != raster_nodata).sum())

        return output

    def count_nodata_cells(
        self,
        raster_file: str
    ) -> int:

        '''
        Count the number of NoData cells in the raster file.

        Parameters
        ----------
        raster_file : str
            Path of the input raster file.

        Returns
        -------
        int
            The numer of NoData cells in the raster file.
        '''

        with rasterio.open(raster_file) as input_raster:
            raster_nodata = input_raster.nodata
            raster_array = input_raster.read(1)
            output = int((raster_array == raster_nodata).sum())

        return output

    def percentage_unique_integers(
        self,
        raster_file: str
    ) -> pandas.DataFrame:

        '''
        Compute the percentage of unique integer values in the raster array.

        Parameters
        ----------
        raster_file : str
            Path to the input raster file.

        Returns
        -------
        DataFrame
            A DataFrame containing the unique integer values in the raster,
            their counts, and their counts as a percentage of the total.
        '''

        with rasterio.open(raster_file) as input_raster:
            raster_profile = input_raster.profile
            if 'int' not in raster_profile['dtype']:
                raise Exception('Input raster data must be integer type.')
            else:
                # DataFrame
                raster_array = input_raster.read(1)
                valid_array = raster_array[raster_array != raster_profile['nodata']]
                value, count = numpy.unique(
                    valid_array,
                    return_counts=True
                )
                df = pandas.DataFrame({'Value': value, 'Count': count})
                df['Percent(%)'] = 100 * df['Count'] / df['Count'].sum()

        return df
