import rasterio
import rasterio.features
import rasterio.mask
import geopandas
import pandas
import numpy
import typing


class Raster:

    '''
    Provides functionality for raster file operations.
    '''

    def count_data_cells(
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

    def counting_unique_values(
        self,
        input_file: str,
        csv_file: str,
        multiplier: float = 1
    ) -> pandas.DataFrame:

        '''
        Computes the count of unique data values in a raster array. If the data contains decimal values,
        the input multiplier is used to scale the decimal values to integers for counting purposes.
        The data are then scaled back to the decimal values by dividing by the multiplier.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        csv_file : str
            Path to save the output csv file.

        multiplier : float, optional
            A factor to multiply raster values to handle decimal values by rounding.
            Default is 1, which implies no scaling.

        Returns
        -------
        DataFrame
            A DataFrame containing the raster values, their counts,
            and their counts as a percentage of the total.
        '''

        with rasterio.open(input_file) as input_raster:
            raster_profile = input_raster.profile
            raster_array = input_raster.read(1)
            value_array = (multiplier * raster_array[raster_array != raster_profile['nodata']]).round()
            value, count = numpy.unique(
                value_array,
                return_counts=True
            )
            df = pandas.DataFrame({'Value': value, 'Count': count})
            df['Value'] = df['Value'] / multiplier
            df['Count(%)'] = 100 * df['Count'] / df['Count'].sum()
            df['Cumulative_Count(%)'] = df['Count(%)'].cumsum()
            df.to_csv(
                path_or_buf=csv_file,
                index_label='Index',
                float_format='%.2f'
            )

        return df

    def boundary_polygon(
        self,
        input_file: str,
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Extracts boundary polygons from a raster array.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        output_file : str
            Path to save the output shapefile.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the boundary polygons extracted from the raster.
        '''

        with rasterio.open(input_file) as input_raster:
            raster_array = input_raster.read(1)
            raster_array[raster_array != input_raster.nodata] = 1
            mask = raster_array == 1
            boundary_shapes = rasterio.features.shapes(
                source=raster_array,
                mask=mask,
                transform=input_raster.transform
            )
            boundary_features = [
                {'geometry': geom, 'properties': {'value': val}} for geom, val in boundary_shapes
            ]
            gdf = geopandas.GeoDataFrame.from_features(
                features=boundary_features,
                crs=input_raster.crs
            )
            gdf = gdf[gdf.is_valid].reset_index(drop=True)
            gdf['bid'] = range(1, gdf.shape[0] + 1)
            gdf = gdf[['bid', 'geometry']]
            gdf.to_file(output_file)

        return gdf

    def rescaling_resolution(
        self,
        input_file: str,
        target_resolution: int,
        resampling_method: str,
        output_file: str
    ) -> list[list[float]]:

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
        list
            A nested list representation of the 3x3 affine transformation matrix
            of the reprojected raster array. Each sublist represents a row of the matrix.
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
                affine_matrix = [
                    list(rescaled_raster[1])[i:i + 3] for i in [0, 3, 6]
                ]

        return affine_matrix

    def rescaling_resolution_with_mask(
        self,
        input_file: str,
        mask_file: str,
        resampling_method: str,
        output_file: str
    ) -> list[list[float]]:

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
        list
            A nested list representation of the 3x3 affine transformation matrix
            of the reprojected raster array. Each sublist represents a row of the matrix.
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
                    affine_matrix = [
                        list(rescaled_raster[1])[i:i + 3] for i in [0, 3, 6]
                    ]

        return affine_matrix

    def reproject_crs(
        self,
        input_file: str,
        resampling_method: str,
        target_crs: str,
        output_file: str
    ) -> list[list[float]]:

        '''
        Reprojects a raster array to a new Coordinate Reference System.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        resampling_method : str
            Method used for raster resampling. Supported options are:
            - 'nearest': Nearest-neighbor interpolation.
            - 'bilinear': Bilinear interpolation.
            - 'cubic': Cubic convolution interpolation.

        target_crs : str
            Target Coordinate Reference System for the output raster (e.g., 'EPSG:4326').

        output_file : str
            Path to save the reprojected raster file.

        Returns
        -------
        list
            A nested list representation of the 3x3 affine transformation matrix
            of the reprojected raster array. Each sublist represents a row of the matrix.
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

        # reproject Coordinate Reference System
        with rasterio.open(input_file) as input_raster:
            raster_profile = input_raster.profile
            # output raster parameters
            output_transform, output_width, output_height = rasterio.warp.calculate_default_transform(
                src_crs=input_raster.crs,
                dst_crs=target_crs,
                width=input_raster.width,
                height=input_raster.height,
                left=input_raster.bounds.left,
                bottom=input_raster.bounds.bottom,
                right=input_raster.bounds.right,
                top=input_raster.bounds.top
            )
            # output raster profile
            raster_profile.update(
                {
                    'transform': output_transform,
                    'width': output_width,
                    'height': output_height,
                    'crs': target_crs
                }
            )
            # saving output raster
            with rasterio.open(output_file, 'w', **raster_profile) as output_raster:
                reproject_raster = rasterio.warp.reproject(
                    source=rasterio.band(input_raster, 1),
                    destination=rasterio.band(output_raster, 1),
                    src_transform=input_raster.transform,
                    src_crs=input_raster.crs,
                    dst_transform=output_transform,
                    dst_crs=target_crs,
                    resampling=resampling_function[resampling_method]
                )
                affine_matrix = [
                    list(reproject_raster[1])[i:i + 3] for i in [0, 3, 6]
                ]

        return affine_matrix

    def set_value_to_nodata(
        self,
        input_file: str,
        target_value: list[float],
        nodata: float,
        output_file: str
    ) -> dict[str, typing.Any]:

        '''
        Converts specified values in a raster array to nodata.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        target_value : list
            List of values in the input raster array to convert to nodata.

        nodata : float
            The nodata value to assign in the output raster.

        output_file : str
            Path to save the output raster file.

        Returns
        -------
        dict
            A profile dictionary containing metadata about the output raster.
        '''

        with rasterio.open(input_file) as input_raster:
            raster_profile = input_raster.profile
            input_array = input_raster.read(1)
            output_array = numpy.where(
                numpy.isin(input_array, target_value),
                nodata,
                input_array
            )
            raster_profile.update(
                {
                    'nodata': nodata
                }
            )
            with rasterio.open(output_file, 'w', **raster_profile) as output_raster:
                output_raster.write(output_array, 1)
                output_profile = dict(output_raster.profile)

        return output_profile

    def clipping_by_shapes(
        self,
        input_file: str,
        shape_file: str,
        output_file: str
    ) -> dict[str, typing.Any]:

        '''
        Clips a raster file using a given shape file.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        shape_file : str
            Path to the input shape file used for clipping.

        output_file : str
            Path to save the output raster file.

        Returns
        -------
        dict
            A profile dictionary containing metadata about the output raster.
        '''

        with rasterio.open(input_file) as input_raster:
            raster_profile = input_raster.profile.copy()
            gdf = geopandas.read_file(shape_file)
            gdf = gdf.to_crs(str(raster_profile['crs']))
            output_array, output_transform = rasterio.mask.mask(
                dataset=input_raster,
                shapes=gdf.geometry.tolist(),
                all_touched=True,
                crop=True
            )
            raster_profile.update(
                {
                    'height': output_array.shape[1],
                    'width': output_array.shape[2],
                    'transform': output_transform
                }
            )
            with rasterio.open(output_file, 'w', **raster_profile) as output_raster:
                output_raster.write(output_array)
                output_profile = dict(output_raster.profile)

        return output_profile
