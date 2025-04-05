import typing
import rasterio
import rasterio.features
import rasterio.merge
import rasterio.mask
import geopandas
import pandas
import numpy
import os
from .core import Core
from .file import File


class Raster:

    '''
    Provides functionality for raster file operations.
    '''

    def count_data_cells(
        self,
        raster_file: str
    ) -> int:

        '''
        Counts the number of cells in the raster file that have valid data.

        Parameters
        ----------
        raster_file : str
            Path to the input raster file.

        Returns
        -------
        int
            The numer of cells with valid data in the raster file.
        '''

        with rasterio.open(raster_file) as input_raster:
            raster_array = input_raster.read(1)
            output = int((raster_array != input_raster.nodata).sum())

        return output

    def count_nodata_cells(
        self,
        raster_file: str
    ) -> int:

        '''
        Counts the number of NoData cells in the raster file.

        Parameters
        ----------
        raster_file : str
            Path to the input raster file.

        Returns
        -------
        int
            The numer of NoData cells in the raster file.
        '''

        with rasterio.open(raster_file) as input_raster:
            raster_array = input_raster.read(1)
            output = int((raster_array == input_raster.nodata).sum())

        return output

    def count_unique_values(
        self,
        raster_file: str,
        csv_file: str,
        multiplier: float = 1,
        remove_values: tuple[int, ...] = (),
        ascending_values: bool = True
    ) -> pandas.DataFrame:

        '''
        Returns a DataFrame containing the unique values and their counts in a raster array.
        If the raster contains decimal values, the specified multiplier scales them to integers
        for counting purposes. The values are then scaled back to their original decimal form
        by dividing by the multiplier.

        Parameters
        ----------
        raster_file : str
            Path to the input raster file.

        csv_file : str
            Path to save the output csv file.

        multiplier : float, optional
            A factor to multiply raster values to handle decimal values by rounding.
            Default is 1, which implies no scaling.

        remove_values : tuple, optional
            A tuple of integer values to exclude from counting. These values must match
            the result of multiplying raster values by the multiplier. Default is an empty tuple.

        ascending_values : bool, optional
            If False, unique values are sorted in descending order. Defaults to True.

        Returns
        -------
        DataFrame
            A DataFrame containing the raster values, their counts,
            and their counts as a percentage of the total.
        '''

        with rasterio.open(raster_file) as input_raster:
            raster_profile = input_raster.profile
            raster_array = input_raster.read(1)
            value_array = (multiplier * raster_array[raster_array != raster_profile['nodata']]).round()
            value, count = numpy.unique(
                value_array,
                return_counts=True
            )
            df = pandas.DataFrame({'Value': value, 'Count': count})
            df = df[~df['Value'].isin(remove_values)].reset_index(drop=True)
            df['Value'] = df['Value'] / multiplier
            df = df if ascending_values else df.sort_values(by='Value', ascending=False, ignore_index=True)
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
        raster_file: str,
        shape_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Extracts boundary polygons from a raster array.

        Parameters
        ----------
        raster_file : str
            Path to the input raster file.

        shape_file : str
            Path to save the output shapefile.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the boundary polygons extracted from the raster.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(shape_file)
        if check_file is True:
            pass
        else:
            raise Exception('Could not retrieve driver from the file path.')

        # saving raster boundary GeoDataFrame
        with rasterio.open(raster_file) as input_raster:
            raster_array = input_raster.read(1)
            raster_array[raster_array != input_raster.nodata] = 1
            mask = raster_array == 1
            boundary_shapes = rasterio.features.shapes(
                source=raster_array,
                mask=mask,
                transform=input_raster.transform,
                connectivity=8
            )
            boundary_features = [
                {'geometry': geom, 'properties': {'value': val}} for geom, val in boundary_shapes
            ]
            gdf = geopandas.GeoDataFrame.from_features(
                features=boundary_features,
                crs=input_raster.crs
            )
            gdf['bid'] = range(1, gdf.shape[0] + 1)
            gdf = gdf[['bid', 'geometry']]
            gdf.to_file(shape_file)

        return gdf

    def resolution_rescaling(
        self,
        input_file: str,
        target_resolution: int,
        resampling_method: str,
        output_file: str
    ) -> rasterio.profiles.Profile:

        '''
        Rescales the raster array from the existing resolution to a new target resolution.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        target_resolution : int
            Desired resolution of the output raster file.

        resampling_method : str
            Raster resampling method with supported options from
            :attr:`GeoAnalyze.core.Core.raster_resampling_method`.

        output_file : str
            Path to the output raster file.

        Returns
        -------
        profile
            A profile containing metadata about the output raster.
        '''

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(output_file)
        if check_file is True:
            pass
        else:
            raise Exception('Could not retrieve driver from the file path.')

        # check resampling method
        resampling_dict = Core().raster_resampling_method
        if resampling_method in resampling_dict.keys():
            pass
        else:
            raise Exception(f'Input resampling method must be one of {list(resampling_dict.keys())}.')

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
                rasterio.warp.reproject(
                    source=rasterio.band(input_raster, 1),
                    destination=rasterio.band(output_raster, 1),
                    src_transform=input_raster.transform,
                    src_crs=input_raster.crs,
                    dst_transform=output_transform,
                    dst_crs=input_raster.crs,
                    resampling=resampling_dict[resampling_method]
                )
                output_profile = output_raster.profile

        return output_profile

    def resolution_rescaling_with_mask(
        self,
        input_file: str,
        mask_file: str,
        resampling_method: str,
        output_file: str
    ) -> rasterio.profiles.Profile:

        '''
        Rescales the raster array from its existing resolution
        to match the resolution of a mask raster file.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        mask_file : str
            Path to the mask raster file, defining the spatial extent and resolution.

        resampling_method : str
            Raster resampling method with supported options from
            :attr:`GeoAnalyze.core.Core.raster_resampling_method`.

        output_file : str
            Path to the output raster file.

        Returns
        -------
        profile
            A profile containing metadata about the output raster.
        '''

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(output_file)
        if check_file is True:
            pass
        else:
            raise Exception('Could not retrieve driver from the file path.')

        # check resampling method
        resampling_dict = Core().raster_resampling_method
        if resampling_method in resampling_dict.keys():
            pass
        else:
            raise Exception(f'Input resampling method must be one of {list(resampling_dict.keys())}.')

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
                    rasterio.warp.reproject(
                        source=rasterio.band(input_raster, 1),
                        destination=rasterio.band(output_raster, 1),
                        src_transform=mask_raster.transform,
                        src_crs=mask_raster.crs,
                        dst_transform=output_transform,
                        dst_crs=mask_raster.crs,
                        resampling=resampling_dict[resampling_method]
                    )
                    output_profile = output_raster.profile

        return output_profile

    def crs_reprojection(
        self,
        input_file: str,
        resampling_method: str,
        target_crs: str,
        output_file: str,
        nodata: typing.Optional[int] = None
    ) -> rasterio.profiles.Profile:

        '''
        Reprojects a raster array to a new Coordinate Reference System.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        resampling_method : str
            Raster resampling method with supported options from
            :attr:`GeoAnalyze.core.Core.raster_resampling_method`.

        target_crs : str
            Target Coordinate Reference System for the output raster (e.g., 'EPSG:4326').

        output_file : str
            Path to save the reprojected raster file.

        nodata : int, optional
            NoData value to assign in the output raster.
            If None, the NoData value of the input raster is retained.

        Returns
        -------
        profile
            A profile containing metadata about the output raster.
        '''

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(output_file)
        if check_file is True:
            pass
        else:
            raise Exception('Could not retrieve driver from the file path.')

        # check resampling method
        resampling_dict = Core().raster_resampling_method
        if resampling_method in resampling_dict.keys():
            pass
        else:
            raise Exception(f'Input resampling method must be one of {list(resampling_dict.keys())}.')

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
            nodata = raster_profile['nodata'] if nodata is None else nodata
            raster_profile.update(
                {
                    'transform': output_transform,
                    'width': output_width,
                    'height': output_height,
                    'crs': target_crs,
                    'nodata': nodata
                }
            )
            # saving output raster
            with rasterio.open(output_file, 'w', **raster_profile) as output_raster:
                rasterio.warp.reproject(
                    source=rasterio.band(input_raster, 1),
                    destination=rasterio.band(output_raster, 1),
                    src_transform=input_raster.transform,
                    src_crs=input_raster.crs,
                    dst_transform=output_transform,
                    dst_crs=target_crs,
                    dst_nodata=nodata,
                    resampling=resampling_dict[resampling_method]
                )
                output_profile = output_raster.profile

        return output_profile

    def nodata_conversion_from_value(
        self,
        input_file: str,
        target_value: list[float],
        output_file: str,
    ) -> rasterio.profiles.Profile:

        '''
        Converts specified values in a raster array to NoData.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        target_value : list
            List of values in the input raster array to convert to nodata.

        output_file : str
            Path to save the output raster file.

        Returns
        -------
        profile
            A profile containing metadata about the output raster.
        '''

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(output_file)
        if check_file is True:
            pass
        else:
            raise Exception('Could not retrieve driver from the file path.')

        # saving raster after converting raster value to NoData
        with rasterio.open(input_file) as input_raster:
            raster_profile = input_raster.profile
            input_array = input_raster.read(1)
            output_array = numpy.where(
                numpy.isin(input_array, target_value),
                raster_profile['nodata'],
                input_array
            )
            with rasterio.open(output_file, 'w', **raster_profile) as output_raster:
                output_raster.write(output_array, 1)
                output_profile = output_raster.profile

        return output_profile

    def nodata_value_change(
        self,
        input_file: str,
        nodata: int,
        output_file: str,
        dtype: typing.Optional[str] = None
    ) -> rasterio.profiles.Profile:

        '''
        Modifies the NoData value of a raster array.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        nodata : int
            New NoData value to be assigned to the output raster.

        output_file : str
            Path to save the output raster file.

        dtype : str, optional
            Data type of the output raster.
            If None, the data type of the input raster is retained.

        Returns
        -------
        profile
            A profile containing metadata about the output raster.
        '''

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(output_file)
        if check_file is True:
            pass
        else:
            raise Exception('Could not retrieve driver from the file path.')

        # saving raster after changing NoData value
        with rasterio.open(input_file) as input_raster:
            raster_profile = input_raster.profile
            raster_profile['dtype'] = raster_profile['dtype'] if dtype is None else dtype
            raster_array = input_raster.read(1).astype(dtype)
            raster_array[raster_array == raster_profile['nodata']] = nodata
            raster_profile['nodata'] = nodata
            with rasterio.open(output_file, mode='w', **raster_profile) as output_raster:
                output_raster.write(raster_array, 1)
                output_profile = output_raster.profile

        return output_profile

    def nodata_extent_trimming(
        self,
        input_file: str,
        output_file: str
    ) -> rasterio.profiles.Profile:

        '''
        Trims rows and columns that contain only NoData values in the raster array.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        output_file : str
            Path to save the output raster file.

        Returns
        -------
        profile
            A profile containing metadata about the output raster.
        '''

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(output_file)
        if check_file is True:
            pass
        else:
            raise Exception('Could not retrieve driver from the file path.')

        # trimming NoData rows and columns
        with rasterio.open(input_file) as input_raster:
            raster_profile = input_raster.profile
            input_array = input_raster.read(1)
            mask_array = input_array != raster_profile['nodata']
            # rows and columns with at least one valid value
            valid_rows = numpy.any(mask_array, axis=1)
            valid_cols = numpy.any(mask_array, axis=0)
            # trimmed NoData rows and columns
            trim_array = input_array[numpy.ix_(valid_rows, valid_cols)]
            # trimmed transform
            row_start, row_end = numpy.where(valid_rows)[0][[0, -1]]
            col_start, col_end = numpy.where(valid_cols)[0][[0, -1]]
            trim_transform = raster_profile['transform'] * rasterio.transform.Affine.translation(col_start, row_start)
            # saving output raster array
            raster_profile.update(
                {
                    'height': trim_array.shape[0],
                    'width': trim_array.shape[1],
                    'transform': trim_transform
                }
            )
            with rasterio.open(output_file, 'w', **raster_profile) as output_raster:
                output_raster.write(trim_array, 1)
                output_profile = output_raster.profile

        return output_profile

    def clipping_by_shapes(
        self,
        input_file: str,
        shape_file: str,
        output_file: str
    ) -> rasterio.profiles.Profile:

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
        profile
            A profile containing metadata about the output raster.
        '''

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(output_file)
        if check_file is True:
            pass
        else:
            raise Exception('Could not retrieve driver from the file path.')

        # saving clipped raster
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
                output_profile = output_raster.profile

        return output_profile

    def array_from_geometries(
        self,
        shape_file: str,
        value_column: str,
        mask_file: str,
        output_file: str,
        select_value: typing.Optional[list[float]] = None,
        dtype: typing.Optional[str] = None,
        nodata: typing.Optional[int] = None
    ) -> rasterio.profiles.Profile:

        '''
        Converts geometries from a shapefile to a raster array.

        Parameters
        ----------
        shape_file : str
            Path to the input shapefile containing the geometries.

        value_column : str
            Column name that contains integer or float values
            to be inserted into the raster array.

        mask_file : str
            Path to the mask raster file, defining the spatial extent and resolution.

        output_file : str
            Path to save the output raster file.

        select_value : list of float, optional
            A list of specific values from the selected column to include.
            If None, all values from the selected column are used.

        dtype : str, optional
            Data type of the output raster.
            If None, the data type of the input raster is retained.

        nodata : int, optional
            NoData value to assign in the output raster.
            If None, the NoData value of the input raster is retained.

        Returns
        -------
        profile
            A profile containing metadata about the output raster.
        '''

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(output_file)
        if check_file is True:
            pass
        else:
            raise Exception('Could not retrieve driver from the file path.')

        # input shapes
        gdf = geopandas.read_file(shape_file)
        gdf = gdf if select_value is None else gdf[gdf[value_column].isin(select_value)].reset_index(drop=True)

        # saving output raster
        with rasterio.open(mask_file) as mask_raster:
            mask_profile = mask_raster.profile
            mask_profile['dtype'] = mask_profile['dtype'] if dtype is None else dtype
            mask_profile['nodata'] = mask_profile['nodata'] if nodata is None else nodata
            output_array = rasterio.features.rasterize(
                shapes=zip(gdf.geometry, gdf[value_column]),
                out_shape=mask_raster.shape,
                transform=mask_raster.transform,
                all_touched=True,
                fill=mask_profile['nodata'],
                dtype=mask_profile['dtype']
            )
            with rasterio.open(output_file, mode='w', **mask_profile) as output_raster:
                output_raster.write(output_array, 1)

        return mask_profile

    def overlaid_with_geometries(
        self,
        input_file: str,
        shape_file: str,
        value_column: str,
        output_file: str,
        all_pixels: bool = True,
        dtype: typing.Optional[str] = None,
        nodata: typing.Optional[int] = None
    ) -> list[float]:

        '''
        Overlays geometries from a shapefile onto the input raster.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        shape_file : str
            Path to the shapefile containing geometries to overlay on the raster.

        value_column : str
            Column name that contains integer or float values
            to be inserted into the raster array.

        output_file : str
            Path to save the output raster file.

        all_pixels : bool, optional
            If True, all pixels touched by geometries will be considered;
            otherwise, only pixels whose center is within the geometries will be considered.
            Default is True.

        dtype : str, optional
            Data type of the output raster.
            If None, the data type of the input raster is retained.

        nodata : int, optional
            NoData value to assign in the output raster.
            If None, the NoData value of the input raster is retained.

        Returns
        -------
        list
            A list containing the unique values from the output raster,
            confirming that the geometries have been successfully overlaid.
        '''

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')
        else:
            pass

        # input GeoDataFrame
        gdf = geopandas.read_file(shape_file)
        paste_value = gdf[value_column].unique().tolist()

        # pasting geometries to input raster
        with rasterio.open(input_file) as input_raster:
            raster_profile = input_raster.profile
            input_array = input_raster.read(1)
            nodata_array = input_array == raster_profile['nodata']
            raster_profile['dtype'] = raster_profile['dtype'] if dtype is None else dtype
            raster_profile['nodata'] = raster_profile['nodata'] if nodata is None else nodata
            shape_array = rasterio.features.rasterize(
                shapes=zip(gdf.geometry, gdf[value_column]),
                out_shape=input_raster.shape,
                transform=raster_profile['transform'],
                all_touched=all_pixels,
                fill=raster_profile['nodata'],
                dtype=raster_profile['dtype']
            )
            output_array = numpy.where(
                numpy.isin(shape_array, paste_value),
                shape_array,
                input_array
            )
            output_array[nodata_array] = raster_profile['nodata']
            # saving output raster
            with rasterio.open(output_file, mode='w', **raster_profile) as output_raster:
                output_raster.write(output_array, 1)
                output = list(numpy.unique(output_array[output_array != output_raster.nodata]))

        return output

    def reclassify_by_value_mapping(
        self,
        input_file: str,
        reclass_map: dict[tuple[float, ...], float],
        output_file: str,
        dtype: typing.Optional[str] = None
    ) -> list[float]:

        '''
        Reclassifies raster values based on a specified mapping.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        reclass_map : dict
            Dictionary mapping raster values to reclassified values.
            The keys are tuples of raster values, and the corresponding values
            are the reclassified values.

        output_file : str
            Path to save the output raster file.

        dtype : str, optional
            Data type of the output raster.
            If None, the data type of the input raster is retained.

        Returns
        -------
        list
            A list containing the unique values from the output raster,
            confirming that the raster has been successfully reclassified.
        '''

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')
        else:
            pass

        # reclassify raster array
        with rasterio.open(input_file) as input_raster:
            raster_profile = input_raster.profile
            raster_array = input_raster.read(1)
            reclass_array = raster_array.copy() if dtype is None else raster_array.copy().astype(dtype)
            for raster_val, reclass_val in reclass_map.items():
                reclass_array[numpy.isin(raster_array, raster_val)] = reclass_val
            # saving reclassified raster
            raster_profile['dtype'] = raster_profile['dtype'] if dtype is None else dtype
            with rasterio.open(output_file, 'w', **raster_profile) as output_raster:
                output_raster.write(reclass_array, 1)
                output = list(numpy.unique(reclass_array[reclass_array != output_raster.nodata]))

        return output

    def reclassify_by_constant_value(
        self,
        input_file: str,
        constant_value: float,
        output_file: str,
        dtype: typing.Optional[str] = None
    ) -> list[float]:

        '''
        Reclassifies raster by assigning a constant value to all pixels.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        constant_value : float
            Constant value to be assigned to all pixels in the output raster.

        output_file : str
            Path to save the output raster file.

        dtype : str, optional
            Data type of the output raster.
            If None, the data type of the input raster is retained.

        Returns
        -------
        list
            A list containing the unique values from the output raster,
            confirming that the raster has been successfully reclassified.
        '''

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')
        else:
            pass

        # constant raster array
        with rasterio.open(input_file) as input_raster:
            raster_profile = input_raster.profile
            raster_array = input_raster.read(1)
            constant_array = raster_array.copy() if dtype is None else raster_array.copy().astype(dtype)
            constant_array[constant_array != raster_profile['nodata']] = constant_value
            # saving constant raster
            raster_profile['dtype'] = raster_profile['dtype'] if dtype is None else dtype
            with rasterio.open(output_file, 'w', **raster_profile) as output_raster:
                output_raster.write(constant_array, 1)
                output = list(numpy.unique(constant_array[constant_array != output_raster.nodata]))

        return output

    def reclassify_value_outside_boundary(
        self,
        input_file: str,
        area_file: str,
        outside_value: float,
        output_file: str
    ) -> list[float]:

        '''
        Reclassifies values outside a specified area in the input raster,
        based on the corresponding area raster. Both rasters must share the same
        cell alignment, coordinate reference system (CRS), and pixel resolution.

        Parameters
        ----------
        input_file : str
            Path to the input raster file.

        area_file : str
            Path to the area raster file.

        outside_value : float
            The value to assign to cells outside the specified area.

        output_file : str
            Path to save the modified output raster file.

        Returns
        -------
        list
            A list containing the unique values from the output raster,
            verifying the successful insertion of the buffer value.
        '''

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(output_file)
        if check_file is True:
            pass
        else:
            raise Exception('Could not retrieve driver from the file path.')

        # input array
        with rasterio.open(input_file) as input_raster:
            raster_profile = input_raster.profile
            raster_array = input_raster.read(1)
            raster_left = input_raster.bounds.left
            raster_top = input_raster.bounds.top
            # area array
            with rasterio.open(area_file) as area_raster:
                area_array = area_raster.read(1)
                area_left = area_raster.bounds.left
                area_top = area_raster.bounds.top
                # resized area array
                row_offset = round((raster_top - area_top) / - raster_profile['transform'].e)
                col_offset = round((area_left - raster_left) / raster_profile['transform'].a)
                resized_array = numpy.full(
                    shape=raster_array.shape,
                    fill_value=area_raster.nodata,
                    dtype=area_array.dtype
                )
                resized_array[row_offset:row_offset + area_array.shape[0], col_offset:col_offset + area_array.shape[1]] = area_array
                # saving output raster
                output_array = numpy.full(
                    shape=raster_array.shape,
                    fill_value=outside_value,
                    dtype=raster_profile['dtype']
                )
                mask_array = resized_array != area_raster.nodata
                output_array[mask_array] = raster_array[mask_array]
                output_array[raster_array == raster_profile['nodata']] = raster_profile['nodata']
                with rasterio.open(output_file, 'w', **raster_profile) as output_raster:
                    output_raster.write(output_array, 1)
                    output = list(numpy.unique(output_array[output_array != output_raster.nodata]))

        return output

    def array_to_geometries(
        self,
        raster_file: str,
        select_value: tuple[float, ...],
        shape_file: str,
    ) -> geopandas.GeoDataFrame:

        '''
        Extract geometries from a raster array for the selected values.

        Parameters
        ----------
        raster_file : str
            Path to the input raster file.

        select_value : tuple
            A tuple of selected raster values. All raster values
            will be selected if the input list is empty.

        shape_file : str
            Path to save the output shapefile.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the extracted geometries
            and their corresponding raster values.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(shape_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')
        else:
            pass

        # geometries from raster array
        with rasterio.open(raster_file) as input_raster:
            raster_profile = input_raster.profile
            nodata = raster_profile['nodata']
            raster_array = input_raster.read(1)
            select_value = select_value if len(select_value) > 0 else tuple(numpy.unique(raster_array[raster_array != nodata]))
            shapes = rasterio.features.shapes(
                source=raster_array,
                mask=numpy.isin(raster_array, select_value),
                transform=raster_profile['transform'],
                connectivity=8
            )
            shapes = [
                {'geometry': geom, 'properties': {'rst_val': val}} for geom, val in shapes
            ]
            gdf = geopandas.GeoDataFrame.from_features(
                features=shapes,
                crs=raster_profile['crs']
            )
            gdf.to_file(shape_file)

        return gdf

    def merging_files(
        self,
        folder_path: str,
        raster_file: str,
        raster_extension: str = '.tif',
        dtype: typing.Optional[str] = None,
        nodata: typing.Optional[float] = None
    ) -> rasterio.profiles.Profile:

        '''
        Merges raster files with the same Coordinate Reference System and data type.

        Parameters
        ----------
        folder_path : str
            Path to the folder containing the raster files to be merged.
            The folder must contain only the rasters intended for merging.

        raster_file : str
            Path to save the merged output raster file.

        raster_extension : str, optional
            File extension of the input raster files. Default is '.tif'.

        dtype : str, optional
            Data type of the output raster.
            If None, the data type of the input rasters is retained.

        nodata : float, optional
            NoData value to assign in the output raster.
            If None, the NoData value of the input rasters is retained.

        Returns
        -------
        profile
            A metadata profile containing information about the output raster.
        '''

        # check output file
        check_file = Core().is_valid_raster_driver(raster_file)
        if check_file is True:
            pass
        else:
            raise Exception('Could not retrieve driver from the file path.')

        # raster files
        split_files = File().extract_specific_extension(
            folder_path=folder_path,
            extension=raster_extension
        )

        # merge the split rasters
        split_rasters = [
            rasterio.open(os.path.join(folder_path, file)) for file in split_files
        ]
        raster_profile = split_rasters[0].profile
        output_array, output_transform = rasterio.merge.merge(
            sources=split_rasters
        )
        raster_profile.update(
            {
                'height': output_array.shape[1],
                'width': output_array.shape[2],
                'transform': output_transform
            }
        )
        raster_profile['dtype'] = raster_profile['dtype'] if dtype is None else dtype
        raster_profile['nodata'] = raster_profile['nodata'] if nodata is None else nodata
        # saving the merged raster
        with rasterio.open(raster_file, 'w', **raster_profile) as output_raster:
            output_raster.write(output_array)
        # close the split rasters
        for raster in split_rasters:
            raster.close()

        return raster_profile
