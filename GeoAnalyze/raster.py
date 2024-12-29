import rasterio
import pandas
import numpy


class Raster:

    '''
    Provides functionality for raster file operations.
    '''

    def count_non_nodata_cells(
        self,
        input_file: str
    ) -> int:

        '''
        Counts the number of cells in the raster file that have valid data.

        Parameters
        ----------
        input_file : str
            Path of the input raster file.

        Returns
        -------
        int
            The numer of cells with valid data in the raster file.
        '''

        with rasterio.open(input_file) as input_raster:
            raster_nodata = input_raster.nodata
            raster_array = input_raster.read(1)
            output = int((raster_array != raster_nodata).sum())

        return output

    def count_nodata_cells(
        self,
        input_file: str
    ) -> int:

        '''
        Counts the number of NoData cells in the raster file.

        Parameters
        ----------
        input_file : str
            Path of the input raster file.

        Returns
        -------
        int
            The numer of NoData cells in the raster file.
        '''

        with rasterio.open(input_file) as input_raster:
            raster_nodata = input_raster.nodata
            raster_array = input_raster.read(1)
            output = int((raster_array == raster_nodata).sum())

        return output

    def percentage_unique_integers(
        self,
        input_file: str
    ) -> pandas.DataFrame:

        '''
        Computes the percentage of unique integer values in the raster array.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        Returns
        -------
        DataFrame
            A DataFrame containing the unique integer values in the raster,
            their counts, and their counts as a percentage of the total.
        '''

        with rasterio.open(input_file) as input_raster:
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

    def rescaling_resolution(
        self,
        input_file: str,
        target_resolution: int,
        resampling_method: str,
        output_file: str
    ) -> float:

        '''
        Rescales the raster array from the existing resolution to a new target resolution.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        target_resolution : int
            Desired resolution of the output raster file.

        resampling_method : str
            Method used for raster resampling. Supported options are:
            - 'nearest': Nearest-neighbor interpolation.
            - 'bilinear': Bilinear interpolation.
            - 'cubic': Cubic convolution interpolation.

        output_file : str
            Path to the output raster file.

        Returns
        -------
        float
            The resolution of the rescaled raster array.
        '''

        # mapping of resampling methods
        resampling_function = {
            'nearest': rasterio.enums.Resampling.nearest,
            'bilinear': rasterio.enums.Resampling.bilinear,
            'cubic': rasterio.enums.Resampling.cubic
        }

        # check resampling method
        if resampling_method in resampling_function.keys():
            pass
        else:
            raise Exception('Input resampling method is not supported.')

        # rescaling resolution
        with rasterio.open(input_file) as input_raster:
            raster_profile = input_raster.profile
            # output raster parameters
            output_transform, output_width, output_height = rasterio.warp.calculate_default_transform(
                src_crs=input_raster.crs,
                dst_crs=input_raster.crs,
                width=input_raster.width,
                height=input_raster.height,
                left=input_raster.bounds.left,
                bottom=input_raster.bounds.bottom,
                right=input_raster.bounds.right,
                top=input_raster.bounds.top,
                resolution=(target_resolution,) * 2
            )
            # output raster profile
            raster_profile.update(
                {
                    'transform': output_transform,
                    'width': output_width,
                    'height': output_height
                }
            )
            # saving output raster
            with rasterio.open(output_file, 'w', **raster_profile) as output_raster:
                rescaled_raster = rasterio.warp.reproject(
                    source=rasterio.band(input_raster, 1),
                    destination=rasterio.band(output_raster, 1),
                    src_transform=input_raster.transform,
                    src_crs=input_raster.crs,
                    dst_transform=output_transform,
                    dst_crs=input_raster.crs,
                    resampling=resampling_function[resampling_method]
                )
                output_resolution = float(rescaled_raster[1][0])

        return output_resolution

    def rescaling_resolution_with_mask(
        self,
        input_file: str,
        mask_file: str,
        resampling_method: str,
        output_file: str
    ) -> float:

        '''
        Rescales the raster array from its existing resolution
        to match the resolution of a mask raster file.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        mask_file : str
            Path to the mask raster file.

        resampling_method : str
            Method used for raster resampling. Supported options are:
            - 'nearest': Nearest-neighbor interpolation.
            - 'bilinear': Bilinear interpolation.
            - 'cubic': Cubic convolution interpolation.

        output_file : str
            Path to the output raster file.

        Returns
        -------
        float
            The resolution of the rescaled raster array.
        '''

        # mapping of resampling methods
        resampling_function = {
            'nearest': rasterio.enums.Resampling.nearest,
            'bilinear': rasterio.enums.Resampling.bilinear,
            'cubic': rasterio.enums.Resampling.cubic
        }

        # check resampling method
        if resampling_method in resampling_function.keys():
            pass
        else:
            raise Exception('Input resampling method is not supported.')

        # rescaling resolution
        with rasterio.open(mask_file) as mask_raster:
            mask_profile = mask_raster.profile
            mask_resolution = mask_profile['transform'][0]
            # output raster parameters
            output_transform, output_width, output_height = rasterio.warp.calculate_default_transform(
                src_crs=mask_raster.crs,
                dst_crs=mask_raster.crs,
                width=mask_raster.width,
                height=mask_raster.height,
                left=mask_raster.bounds.left,
                bottom=mask_raster.bounds.bottom,
                right=mask_raster.bounds.right,
                top=mask_raster.bounds.top,
                resolution=(mask_resolution,) * 2
            )
            with rasterio.open(input_file) as input_raster:
                input_profile = input_raster.profile
                # output raster profile
                mask_profile.update(
                    {
                        'transform': output_transform,
                        'width': output_width,
                        'height': output_height,
                        'dtype': input_profile['dtype'],
                        'nodata': input_profile['nodata']
                    }
                )
                # saving output raster
                with rasterio.open(output_file, 'w', **mask_profile) as output_raster:
                    rescaled_raster = rasterio.warp.reproject(
                        source=rasterio.band(input_raster, 1),
                        destination=rasterio.band(output_raster, 1),
                        src_transform=mask_raster.transform,
                        src_crs=mask_raster.crs,
                        dst_transform=output_transform,
                        dst_crs=mask_raster.crs,
                        resampling=resampling_function[resampling_method]
                    )
                    output_resolution = float(rescaled_raster[1][0])

        return output_resolution
