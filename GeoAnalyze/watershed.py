import pyflwdir
import rasterio
import rasterio.features
import geopandas
import shapely
import pandas
import numpy
import os
import sys
import typing
import tempfile
import io
import time
from .core import Core


class Watershed:

    '''
    Provides functionality for watershed delineation from Digital Elevation Model (DEM).
    '''

    def pit_fill_and_flow_direction(
        self,
        dem_file: str,
        outlet_type: str,
        pitfill_file: str,
        flwdir_file: str
    ) -> str:

        '''
        Fill pits of the DEM and use it to calculate the flow direction.
        Save the pit-filled DEM and flow direction arrays to the specified raster file paths.

        Parameters
        ----------
        dem_file : str
            Ratser file path of the input DEM.

        outlet_type : str
            Type of outlet from one of [single, multiple]. The 'single' option forces all flow directions
            toward a single outlet at the lowest pit, while 'multiple' allows for multiple outlets.

        pitfill_file : str
            Raster file path to save the ouput pit-filled DEM.

        flwdir_file : str
            Raster file path to save the output flow direction.

        Returns
        -------
        str
            A confirmation message indicating that all geoprocessing is complete.
        '''

        # start time
        start_time = time.time()

        # check validity of output file path
        for file in [pitfill_file, flwdir_file]:
            check_file = Core().is_valid_raster_driver(file)
            if check_file is False:
                raise Exception(
                    f'Could not retrieve driver from the file path: {file}.'
                )
            else:
                pass

        # pit filling and flow direction from the DEM
        with rasterio.open(dem_file) as input_dem:
            raster_profile = input_dem.profile
            if outlet_type not in ['single', 'multiple']:
                raise Exception('Outlet type must be one of [single, multiple].')
            elif outlet_type == 'multiple':
                pitfill_array, flwdir_array = pyflwdir.dem.fill_depressions(
                    elevtn=input_dem.read(1).astype('float32'),
                    outlets='edge',
                    nodata=input_dem.nodata
                )
            else:
                pitfill_array, flwdir_array = pyflwdir.dem.fill_depressions(
                    elevtn=input_dem.read(1).astype('float32'),
                    outlets='min',
                    nodata=input_dem.nodata
                )
            # saving pit filling raster
            raster_profile.update(
                {'dtype': 'float32'}
            )
            with rasterio.open(pitfill_file, 'w', **raster_profile) as output_pitfill:
                output_pitfill.write(pitfill_array, 1)
            # saving flow direction raster
            raster_profile.update(
                dtype=flwdir_array.dtype,
                nodata=247
            )
            with rasterio.open(flwdir_file, 'w', **raster_profile) as output_flwdir:
                output_flwdir.write(flwdir_array, 1)

        required_time = time.time() - start_time
        print(f'Required time: {required_time:.2f} seconds.')

        return 'All geoprocessing has been completed.'

    def flow_accumulation(
        self,
        pitfill_file: str,
        flwdir_file: str,
        flwacc_file: str
    ) -> str:

        '''
        Compute flow accumulation from the pit-filled DEM and flow direction.
        Save the flow accumulation array to the specified raster file path.

        Parameters
        ----------
        pitfill_file : str
            Raster file path of the input pit-filled DEM.

        flwdir_file : str
            Raster file path of the input flow direction.

        flwacc_file : str
            Raster file path to save the output flow accumulation.

        Returns
        -------
        str
            A confirmation message indicating that all geoprocessing is complete.
        '''

        # start time
        start_time = time.time()

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(flwacc_file)
        if check_file is False:
            raise Exception(
                f'Could not retrieve driver from the file path: {flwacc_file}.'
            )
        else:
            pass

        # masking pit filled DEM
        with rasterio.open(pitfill_file) as input_dem:
            raster_profile = input_dem.profile
            mask_array = (input_dem.read(1) != input_dem.nodata).astype('int32')
            # flow direction object
            with rasterio.open(flwdir_file) as input_flwdir:
                flwdir_object = pyflwdir.from_array(
                    data=input_flwdir.read(1),
                    transform=input_dem.transform
                )
                # flow accumulation array
                flwacc_array = flwdir_object.accuflux(
                    data=mask_array
                )
            max_flwacc = flwacc_array[mask_array != 0].max()
            print(f'Maximum flow accumulation: {max_flwacc}.')
            # saving flow accumulation raster
            flwacc_array[mask_array == 0] = input_dem.nodata
            raster_profile.update(
                {'dtype': 'float32'}
            )
            with rasterio.open(flwacc_file, 'w', **raster_profile) as output_flwacc:
                output_flwacc.write(flwacc_array, 1)

        required_time = time.time() - start_time
        print(f'Required time: {required_time:.2f} seconds.')

        return 'All geoprocessing has been completed.'

    def stream_and_outlets(
        self,
        flwdir_file: str,
        flwacc_file: str,
        tacc_type: str,
        tacc_value: str,
        stream_file: str,
        outlet_file: str
    ) -> str:

        '''
        Generate streamlines and outlet GeoDataFrames from flow direction and accumulation.
        Save the streamlines and outlet as GeoDataFrames to the specified shapefile paths.

        Parameters
        ----------
        flwdir_file : str
            Raster file path of the input flow direction.

        flwacc_file : str
            Raster file path of the input flow accumulation.

        tacc_type : str
            Type of threshold for flow accumulation, chosen from ['percentage', 'absolute'].
            The 'percentage' option takes the percent value of the maximum flow accumulation, while
            'absolute' specifies a direct accumulation value.

        tacc_value : float
            If 'percentage' is selected, this value must be between 0 and 100, representing the
            percentage of maximum flow accumulation.

        stream_file : str
            Shapefile path to save the output streamlines as a LineString GeoDataFrame.

        outlet_file : str
            Shapefile path to save the output stream outlets as a Point GeoDataFrame.

        Returns
        -------
        str
            A confirmation message indicating that all geoprocessing is complete.
        '''

        # start time
        start_time = time.time()

        # check validity of output file path
        for file in [stream_file, outlet_file]:
            check_file = Core().is_valid_ogr_driver(file)
            if check_file is False:
                raise Exception(
                    f'Could not retrieve driver from the file path: {file}.'
                )
            else:
                pass

        # flow direction object
        with rasterio.open(flwdir_file) as input_flwdir:
            flwdir_object = pyflwdir.from_array(
                data=input_flwdir.read(1),
                transform=input_flwdir.transform
            )

        # flow accumulation array
        with rasterio.open(flwacc_file) as input_flwacc:
            raster_profile = input_flwacc.profile
            flwacc_array = input_flwacc.read(1)
            max_flwacc = flwacc_array[flwacc_array != input_flwacc.nodata].max()
            print(f'Maximum flow accumulation: {max_flwacc}.')

        # flow path and main outlets
        if tacc_type not in ['percentage', 'absolute']:
            raise Exception('Threshold accumulation type must be one of [percentage, absolute].')
        elif tacc_type == 'absolute':
            acc_threshold = tacc_value
        else:
            acc_threshold = round(max_flwacc * tacc_value / 100)
        print(f'Threshold flow accumulation: {acc_threshold}.')

        # flow accumulation to stream path
        features = flwdir_object.streams(
            mask=flwacc_array >= acc_threshold
        )
        gdf = geopandas.GeoDataFrame.from_features(
            features=features,
            crs=raster_profile['crs']
        )

        # saving stream GeoDataFrame
        stream_gdf = gdf[gdf['pit'] == 0].reset_index(drop=True)
        stream_gdf['SID'] = list(range(1, stream_gdf.shape[0] + 1))
        stream_gdf.to_file(stream_file)

        # saving outlet GeoDataFrame
        outlet_gdf = gdf[gdf['pit'] == 1].reset_index(drop=True)
        outlet_gdf['geometry'] = outlet_gdf['geometry'].apply(
            lambda x: shapely.Point(*x.coords[-1])
        )
        outlet_gdf['OID'] = list(range(1, outlet_gdf.shape[0] + 1))
        outlet_gdf.to_file(outlet_file)

        required_time = time.time() - start_time
        print(f'Required time: {required_time:.2f} seconds.')

        return 'All geoprocessing has been completed.'

    def subcatchment_and_pourpoints(
        self,
        flwdir_file: str,
        stream_file: str,
        outlet_file: str,
        subcatchment_file: str,
        pour_file: str
    ) -> str:

        '''
        Generate subcatchments and their pour points from flow direction raster, and streamline and outlet shapefiles.
        Save the subcatchments and their pour points as GeoDataFrames to the specified shapefile paths.

        Parameters
        ----------
        flwdir_file : str
            Raster file path of the input flow direction.

        stream_file : str
            Shapefile path of the input streamlines.

        outlet_file : str
            Shapefile path of the input stream outlets.

        subcatchment_file : str
            Shapefile path to save the output subcatchments as a Polygon GeoDataFrame.

        pour_file : str
            Shapefile path to save the output stream subcatchment pour points as a Point GeoDataFrame.

        Returns
        -------
        str
            A confirmation message indicating that all geoprocessing is complete.
        '''

        # start time
        start_time = time.time()

        # flow direction object
        with rasterio.open(flwdir_file) as input_flwdir:
            raster_profile = input_flwdir.profile
            flowdir_object = pyflwdir.from_array(
                data=input_flwdir.read(1),
                transform=input_flwdir.transform
            )

        # stream GeoDataFrame
        stream_gdf = geopandas.read_file(stream_file)

        # Subcatchment pour points
        pits = geopandas.read_file(outlet_file)['idx_ds'].values
        pour_coords = stream_gdf.apply(
            lambda row: row.geometry.coords[-1] if row['idx_ds'] in pits else row.geometry.coords[-2],
            axis=1
        )
        pour_gdf = stream_gdf.copy()
        pour_points = list(map(lambda x: shapely.Point(*x), pour_coords))
        pour_gdf['geometry'] = pour_points

        # saving subcatchment pour points GeoDataFrame
        pour_gdf.to_file(pour_file)

        # subcatchments
        subcatchment_array = flowdir_object.basins(
            xy=(pour_gdf.geometry.x, pour_gdf.geometry.y),
            ids=pour_gdf['SID'].astype('uint32')
        )
        subcatchment_shapes = rasterio.features.shapes(
            source=subcatchment_array.astype('int32'),
            mask=subcatchment_array != 0,
            transform=raster_profile['transform'],
            connectivity=8
        )
        subcatchment_features = [
            {'geometry': geometry, 'properties': {'SID': value}} for geometry, value in subcatchment_shapes
        ]
        subcatchment_gdf = geopandas.GeoDataFrame.from_features(
            features=subcatchment_features,
            crs=raster_profile['crs']
        )

        # saving subbasins GeoDataFrame
        subcatchment_gdf.to_file(subcatchment_file)

        required_time = time.time() - start_time
        print(f'Required time: {required_time:.2f} seconds.')

        return 'All geoprocessing has been completed.'

    def slope_from_dem(
        self,
        dem_file: str,
        outlet_type: str,
        slope_file: str
    ) -> str:

        '''
        Compute slope array from the input DEM and save it to the specified raster path.

        Parameters
        ----------
        dem_file : str
            Ratser file path of the input DEM.

        outlet_type : str
            Type of outlet from one of [single, multiple]. The 'single' option forces all flow directions
            toward a single outlet at the lowest pit, while 'multiple' allows for multiple outlets.

        slope_file : str
            Raster file path to save the output slope.

        Returns
        -------
        str
            A confirmation message indicating that all geoprocessing is complete.
        '''

        # start time
        start_time = time.time()

        # raster profile
        with rasterio.open(dem_file) as input_dem:
            raster_profile = input_dem.profile

        # temporarily suppress print of other function
        temp_stdout = sys.stdout
        sys.stdout = io.StringIO()

        # slope array
        with tempfile.TemporaryDirectory() as tmp_dir:
            pitfill_file = os.path.join(tmp_dir, 'pitfill.tif')
            flwdir_file = os.path.join(tmp_dir, 'flwdir.tif')
            self.pit_fill_and_flow_direction(
                dem_file=dem_file,
                outlet_type=outlet_type,
                pitfill_file=pitfill_file,
                flwdir_file=flwdir_file
            )
            with rasterio.open(pitfill_file) as input_pitfill:
                slope_array = pyflwdir.dem.slope(
                    elevtn=input_pitfill.read(1).astype('float32'),
                    nodata=raster_profile['nodata'],
                    transform=raster_profile['transform']
                )

        # Restore print
        sys.stdout = temp_stdout

        # saving slope raster
        raster_profile.update(
            {'dtype': 'float32'}
        )
        with rasterio.open(slope_file, 'w', **raster_profile) as output_slope:
            output_slope.write(slope_array, 1)

        required_time = time.time() - start_time
        print(f'Required time: {required_time:.2f} seconds.')

        return 'All geoprocessing has been completed.'

    def slope_from_pitfilled_dem(
        self,
        pfdem_file: str,
        slope_file: str
    ) -> str:

        '''
        Compute slope array from the input pit-filled DEM
        and save it to the specified raster path.

        Parameters
        ----------
        pfdem_file : str
            Ratser file path of the input DEM.

        slope_file : str
            Raster file path to save the output slope.

        Returns
        -------
        str
            A confirmation message indicating that all geoprocessing is complete.
        '''

        # start time
        start_time = time.time()

        # slope array
        with rasterio.open(pfdem_file) as input_pfdem:
            raster_profile = input_pfdem.profile
            slope_array = pyflwdir.dem.slope(
                elevtn=input_pfdem.read(1).astype('float32'),
                nodata=raster_profile['nodata'],
                transform=raster_profile['transform']
            )

        # saving slope raster
        raster_profile.update(
            {'dtype': 'float32'}
        )
        with rasterio.open(slope_file, 'w', **raster_profile) as output_slope:
            output_slope.write(slope_array, 1)

        required_time = time.time() - start_time
        print(f'Required time: {required_time:.2f} seconds.')

        return 'All geoprocessing has been completed.'

    def slope_percent_count(
        self,
        slope_file: str,
        cumsum_ul: typing.Optional[float] = None
    ) -> pandas.DataFrame:

        '''
        Multiply the slope array by 100 and round it to one decimal place.
        Return the unique slope percentage values, their count,
        count as a percentage, and the cumulative sum of the count percentage.

        Parameters
        ----------
        slope_file : str
            Raster file path of the input slope.

        cumsum_ul : float, optional
            Upper limit of the cumulative sum of the count percentage.
            If provided, only slope percentage unique values up to the upper limit will be returned.

        Returns
        -------
        DataFrame
            A DataFrame containing the unique slope percentage values, their count,
            count as a percentage, and the cumulative sum of the count percentage.
        '''

        # count of slope array
        with rasterio.open(slope_file) as input_slope:
            raster_profile = input_slope.profile
            slope_array = input_slope.read(1)
            valid_array = (100 * slope_array[slope_array != raster_profile['nodata']]).round(1)
            value, count = numpy.unique(
                valid_array,
                return_counts=True
            )

        # DataFrame
        df = pandas.DataFrame({'Value': value, 'Count': count})
        df['%'] = 100 * df['Count'] / df['Count'].sum()
        df = df.sort_values(by=['%'], ascending=[False]).reset_index(drop=True)
        df['Cum(%)'] = df['%'].cumsum()
        df = df[df['Cum(%)'] <= cumsum_ul] if cumsum_ul is not None else df

        return df

    def slope_classification(
        self,
        slope_file: str,
        reclass_lb: list[int],
        reclass_file: str
    ) -> str:

        '''
        Multiply the slope array by 100 and reclassify the percentage values based on the given intervals.

        Parameters
        ----------
        slope_file : str
            Raster file path of the input slope.

        reclass_lb : list
            List of left bounds of intervals. For example, [0, 2, 5] would be treated as
            three intervals: [0, 2), [2, 5), and [5, maximum slope). The reclassified
            slope values start with 1 for the first interval and
            increase by 1 with each subsequent interval.

        reclass_file : str
            Raster file path to save the output reclassified slope.

            .. note::
                Recommended classifications for erosion risk:

                ======================  ===========================
                Slope Percentage (%)     Slope Type
                ======================  ===========================
                < 2 %                    Flats
                [2 - 8) %                Gentle
                [8 - 20) %               Moderate
                [20 - 40) %              Steep
                >= 40 %                  Very Steep
                ======================  ===========================

            .. tip::
                Recommended for standard classifications:

                ======================  ===========================
                Slope Percentage (%)     Slope Type
                ======================  ===========================
                < 5 %                    Flat
                [5 - 15) %               Gentle
                [15 - 30) %              Moderate
                [30 - 50) %              Steep
                [50 - 75) %              Very Steep
                >= 75 %                  Extremely Steep
                ======================  ===========================

        Returns
        -------
        str
            A confirmation message indicating that all geoprocessing is complete.
        '''

        # start time
        start_time = time.time()

        # slope array
        with rasterio.open(slope_file) as input_slope:
            raster_profile = input_slope.profile
            nodata = raster_profile['nodata']
            slope_array = 100 * input_slope.read(1)
            slope_array[slope_array == nodata * 100] = nodata
            # slope reclassification
            reclass_array = numpy.zeros_like(slope_array)
            reclass_value = 1
            for index, rc_val in enumerate(reclass_lb):
                if rc_val == reclass_lb[-1]:
                    reclass_array[(slope_array >= rc_val) & (slope_array != nodata)] = reclass_value
                else:
                    reclass_array[(slope_array >= rc_val) & (slope_array < reclass_lb[index + 1])] = reclass_value
                reclass_value = reclass_value + 1
            reclass_array[reclass_array == 0] = nodata
            # saving reclassified slope raster
            raster_profile.update(
                {'dtype': 'int32'}
            )
            with rasterio.open(reclass_file, 'w', **raster_profile) as output_reclass:
                output_reclass.write(reclass_array, 1)

        required_time = time.time() - start_time
        print(f'Required time: {required_time:.2f} seconds.')

        return 'All geoprocessing has been completed.'
