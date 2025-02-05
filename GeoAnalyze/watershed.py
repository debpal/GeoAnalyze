import os
import time
import json
import pyflwdir
import rasterio
import rasterio.features
import shapely
import geopandas
import numpy
from .core import Core


class Watershed:

    '''
    Provides functionality for watershed delineation from Digital Elevation Model (DEM).
    '''

    def flow_direction_after_filling_pits(
        self,
        dem_file: str,
        outlet_type: str,
        pitfill_file: str,
        flwdir_file: str
    ) -> str:

        '''
        Compute flow direction after filling the pits of the DEM.

        Parameters
        ----------
        dem_file : str
            Path to the input DEM raster file.

        outlet_type : str
            Type of outlet from one of [single, multiple]. The 'single' option forces all flow directions
            toward a single outlet at the lowest pit, while 'multiple' allows for multiple outlets.

        pitfill_file : str
            Path to save the output pit-filled DEM raster file.

        flwdir_file : str
            Path to save the output flow direction raster file.

        Returns
        -------
        str
            A message indicating the time required for all geoprocessing computations.
        '''

        # start time
        start_time = time.time()

        # check validity of output file path
        for file in [pitfill_file, flwdir_file]:
            check_file = Core().is_valid_raster_driver(file)
            if check_file is False:
                raise Exception('Could not retrieve driver from the file path.')
            else:
                pass

        # check validty of outlet type
        if outlet_type in ['single', 'multiple']:
            pass
        else:
            raise Exception('Outlet type must be one of [single, multiple].')

        # pit filling and flow direction from the DEM
        with rasterio.open(dem_file) as input_dem:
            raster_profile = input_dem.profile
            outlets = 'edge' if outlet_type == 'multiple' else 'min'
            pitfill_array, flwdir_array = pyflwdir.dem.fill_depressions(
                elevtn=input_dem.read(1).astype('float32'),
                outlets=outlets,
                nodata=raster_profile['nodata']
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

        # required time
        required_time = time.time() - start_time
        output = f'Time required for computing pit filling and flow direction: {required_time:.2f} seconds.'

        return output

    def flow_accumulation(
        self,
        pitfill_file: str,
        flwdir_file: str,
        flwacc_file: str
    ) -> str:

        '''
        Computes flow accumulation from the pit-filled DEM and flow direction rasters.

        Parameters
        ----------
        pitfill_file : str
            Path to the input pit-filled DEM raster file.

        flwdir_file : str
            Path of the input flow direction raster file.

        flwacc_file : str
            Path to save the output flow accumulation raster file.

        Returns
        -------
        str
            A message indicating the time required for all geoprocessing computations.
        '''

        # start time
        start_time = time.time()

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(flwacc_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')
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

        # required time
        required_time = time.time() - start_time
        output = f'Time required for computing flow accumulation: {required_time:.2f} seconds.'

        return output

    def stream_network_and_main_outlets(
        self,
        flwdir_file: str,
        flwacc_file: str,
        tacc_type: str,
        tacc_value: str,
        stream_file: str,
        outlet_file: str
    ) -> str:

        '''
        Generates stream network and main outlet GeoDataFrames from flow direction and accumulation.

        Parameters
        ----------
        flwdir_file : str
            Path to the input flow direction raster file.

        flwacc_file : str
            Path to the input flow accumulation raster file.

        tacc_type : str
            Type of threshold for flow accumulation, chosen from ['percentage', 'absolute'].
            The 'percentage' option takes the percent value of the maximum flow accumulation, while
            'absolute' specifies a direct accumulation value.

        tacc_value : float
            If 'percentage' is selected, this value must be between 0 and 100, representing the
            percentage of maximum flow accumulation.

        stream_file : str
            Path to save the output stream shapefile.

        outlet_file : str
            Path to save the output outlet shapefile.

        Returns
        -------
        str
            A message indicating the time required for all geoprocessing computations.
        '''

        # start time
        start_time = time.time()

        # check validity of output file path
        for file in [stream_file, outlet_file]:
            check_file = Core().is_valid_ogr_driver(file)
            if check_file is False:
                raise Exception('Could not retrieve driver from the file path.')
            else:
                pass

        # check validity of flow accumulation thereshold type
        if tacc_type not in ['percentage', 'absolute']:
            raise Exception('Threshold accumulation type must be one of [percentage, absolute].')
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

        # flow accumulation to stream path
        acc_threshold = tacc_value if tacc_type == 'absolute' else round(max_flwacc * tacc_value / 100)
        print(f'Threshold flow accumulation: {acc_threshold}.')
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

        # required time
        required_time = time.time() - start_time
        output = f'Time required for computing stream network and main outlets: {required_time:.2f} seconds.'

        return output

    def subbasin_and_pourpoints(
        self,
        flwdir_file: str,
        stream_file: str,
        outlet_file: str,
        subbasin_file: str,
        pour_file: str
    ) -> str:

        '''
        Generates subbasins and their pour points from flow direction, stream and outlets.

        Parameters
        ----------
        flwdir_file : str
            Path to the input flow direction raster file.

        stream_file : str
            Path of the input stream shapefile.

        outlet_file : str
            Path of the input outlet shapefile.

        subbasin_file : str
            Path to save the output subbasins shapefile.

        pour_file : str
            Path to save the output pour points shapefile.

        Returns
        -------
        str
            A message indicating the time required for all geoprocessing computations.
        '''

        # start time
        start_time = time.time()

        # check validity of output file path
        for file in [subbasin_file, pour_file]:
            check_file = Core().is_valid_ogr_driver(file)
            if check_file is False:
                raise Exception('Could not retrieve driver from the file path.')
            else:
                pass

        # flow direction object
        with rasterio.open(flwdir_file) as input_flwdir:
            raster_profile = input_flwdir.profile
            flowdir_object = pyflwdir.from_array(
                data=input_flwdir.read(1),
                transform=input_flwdir.transform
            )

        # stream GeoDataFrame
        stream_gdf = geopandas.read_file(stream_file)

        # subbasin pour points
        pits = geopandas.read_file(outlet_file)['idx_ds'].values
        pour_coords = stream_gdf.apply(
            lambda row: row.geometry.coords[-1] if row['idx_ds'] in pits else row.geometry.coords[-2],
            axis=1
        )
        pour_gdf = stream_gdf.copy()
        pour_points = list(map(lambda x: shapely.Point(*x), pour_coords))
        pour_gdf['geometry'] = pour_points

        # saving subbasin pour points GeoDataFrame
        pour_gdf.to_file(pour_file)

        # subbasins
        subbasin_array = flowdir_object.basins(
            xy=(pour_gdf.geometry.x, pour_gdf.geometry.y),
            ids=pour_gdf['SID'].astype('uint32')
        )
        subbasin_shapes = rasterio.features.shapes(
            source=subbasin_array.astype('int32'),
            mask=subbasin_array != 0,
            transform=raster_profile['transform'],
            connectivity=8
        )
        subbasin_features = [
            {'geometry': geometry, 'properties': {'SID': value}} for geometry, value in subbasin_shapes
        ]
        subbasin_gdf = geopandas.GeoDataFrame.from_features(
            features=subbasin_features,
            crs=raster_profile['crs']
        )

        # saving subbasins GeoDataFrame
        subbasin_gdf.to_file(subbasin_file)

        # required time
        required_time = time.time() - start_time
        output = f'Time required for computing subbasins and their pour points: {required_time:.2f} seconds.'

        return output

    def slope_from_dem_without_pit_filling(
        self,
        dem_file: str,
        slope_file: str
    ) -> str:

        '''
        Computes slope from the DEM without pit filling.

        Parameters
        ----------
        dem_file : str
            Path to the input DEM raster file.

        slope_file : str
            Path to save the output slope raster file.

        Returns
        -------
        str
            A message indicating the time required for all geoprocessing computations.
        '''

        # start time
        start_time = time.time()

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(slope_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')
        else:
            pass

        # raster profile
        with rasterio.open(dem_file) as input_dem:
            raster_profile = input_dem.profile
            slope_array = pyflwdir.dem.slope(
                elevtn=input_dem.read(1).astype('float32'),
                nodata=raster_profile['nodata'],
                transform=raster_profile['transform']
            )

        # saving slope raster
        raster_profile.update(
            {'dtype': 'float32'}
        )
        with rasterio.open(slope_file, 'w', **raster_profile) as output_slope:
            output_slope.write(slope_array, 1)

        # required time
        required_time = time.time() - start_time
        output = f'Time required for computing slope: {required_time:.2f} seconds.'

        return output

    def slope_classification(
        self,
        slope_file: str,
        reclass_lb: list[int],
        reclass_values: list[int],
        reclass_file: str
    ) -> str:

        '''
        Multiplies the slope array by 100 and reclassifies the values based on the given intervals.

        Parameters
        ----------
        slope_file : str
            Path of the input slope raster file.

        reclass_lb : list
            List of left bounds of intervals. For example, [0, 2, 5] would be treated as
            three intervals: [0, 2), [2, 5), and [5, maximum slope).

        reclass_values : list
            List of reclassified slope values.

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
            A message indicating the time required for all geoprocessing computations.
        '''

        # Start time
        start_time = time.time()

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(reclass_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')
        else:
            pass

        # check lengths of lowerbounds and reclass values
        if len(reclass_values) == len(reclass_lb):
            pass
        else:
            raise Exception('Both input lists must have the same length.')

        # slope array
        with rasterio.open(slope_file) as input_slope:
            raster_profile = input_slope.profile
            nodata = raster_profile['nodata']
            slope_array = 100 * input_slope.read(1).astype(float)
            slope_array[slope_array == nodata * 100] = numpy.nan
            # slope reclassification
            reclass_array = numpy.full_like(slope_array, numpy.nan)
            for index, rc_val in enumerate(reclass_lb):
                if rc_val == reclass_lb[-1]:
                    true_value = (slope_array >= rc_val) & ~numpy.isnan(slope_array)
                else:
                    true_value = (slope_array >= rc_val) & (slope_array < reclass_lb[index + 1]) & ~numpy.isnan(slope_array)
                reclass_array[true_value] = reclass_values[index]
            reclass_array[numpy.isnan(reclass_array)] = nodata
            # saving reclassified slope raster
            raster_profile.update(
                {
                    'dtype': 'int32'
                }
            )
            with rasterio.open(reclass_file, 'w', **raster_profile) as output_reclass:
                output_reclass.write(reclass_array.astype('int32'), 1)

        # required time
        required_time = time.time() - start_time

        return f'Time required for computing slope: {required_time:.2f} seconds.'

    def delineation_files_by_single_function(
        self,
        dem_file: str,
        outlet_type: str,
        tacc_type: str,
        tacc_value: float,
        folder_path: str
    ) -> str:

        '''
        Generates delineation raster outputs, including flow direction (`flwdir.tif`), slope (`slope.tif`),
        and flow accumulation (`flwacc.tif`). Using the provided flow accumulation threshold, the function also generates shapefiles
        for streams (`stream_lines.shp`), subbasins (`subbasins.shp`), pour points (`subbasin_pour_points.shp`), and main outlets
        (`outlet_points.shp`). All shapefiles share a common identifier column, `flw_id`, for easy cross-referencing.
        The `subbasins.shp` file contains an additional column, `area_m2`, which stores the area of each subbasin.
        A summary file is created detailing the processing time and other relevant parameters. All outputs are saved to the specified folder.

        Parameters
        ----------
        dem_file : str
            Path to the input DEM raster file.

        outlet_type : str
            Type of outlet from one of [single, multiple]. The 'single' option forces all flow directions
            toward a single outlet at the lowest pit, while 'multiple' allows for multiple outlets.

        tacc_type : str
            Type of threshold for flow accumulation, chosen from ['percentage', 'absolute'].
            The 'percentage' option takes the percent value of the maximum flow accumulation, while
            'absolute' specifies a direct accumulation value.

        tacc_value : float
            If 'percentage' is selected, this value must be between 0 and 100, representing the
            percentage of maximum flow accumulation.

        folder_path : str
            Path to the output folder for saving files.

        Returns
        -------
        str
            A confirmation message that all geoprocessing has been completed.
        '''

        # time at starting of the program
        run_time = time.time()

        # summary dictionary
        summary = {}

        # check validity of output folder path
        if os.path.isdir(folder_path):
            pass
        else:
            raise Exception('Input folder path does not exsit.')

        # check validty of outlet type
        if outlet_type in ['single', 'multiple']:
            pass
        else:
            raise Exception('Outlet type must be one of [single, multiple].')

        # check validity of threshold flow accumalation type
        if tacc_type in ['percentage', 'absolute']:
            pass
        else:
            raise Exception('Threshold accumulation type must be one of [percentage, absolute].')

        # DEM and mask array
        start_time = time.time()
        with rasterio.open(dem_file) as input_dem:
            cell_area = input_dem.res[0] * input_dem.res[1]
            dem_profile = input_dem.profile
            dem_profile.update(
                {
                    'dtype': 'float32'
                }
            )
            dem_array = input_dem.read(1).astype('float32')
        required_time = round(time.time() - start_time, 2)
        print(
            f'DEM reading time (seconds): {required_time}',
            flush=True
        )
        summary['DEM reading time (seconds)'] = required_time
        mask_array = (dem_array != dem_profile['nodata']).astype('int32')
        valid_cells = int((mask_array != 0).sum())
        summary['Number of valid DEM cells'] = valid_cells
        summary['Cell resolution'] = input_dem.res
        watershed_area = valid_cells * cell_area
        summary['Watershed area (m^2)'] = watershed_area

        # flow direction array and saving raster
        start_time = time.time()
        outlets = 'edge' if outlet_type == 'multiple' else 'min'
        pitfill_array, flwdir_array = pyflwdir.dem.fill_depressions(
            elevtn=dem_array,
            outlets=outlets,
            nodata=dem_profile['nodata']
        )
        flwdir_profile = dem_profile.copy()
        flwdir_profile.update(
            dtype=flwdir_array.dtype,
            nodata=247
        )
        flwdir_file = os.path.join(folder_path, 'flwdir.tif')
        with rasterio.open(flwdir_file, 'w', **flwdir_profile) as output_flwdir:
            output_flwdir.write(flwdir_array, 1)
        required_time = round(time.time() - start_time, 2)
        print(
            f'Pit filling and flow direction calculation time (seconds): {required_time}',
            flush=True
        )
        summary['Pit filling and flow direction calculation time (seconds)'] = required_time

        # slope array and saving raster
        start_time = time.time()
        slope_array = pyflwdir.dem.slope(
            elevtn=pitfill_array.astype('float32'),
            nodata=dem_profile['nodata'],
            transform=dem_profile['transform']
        )
        slope_file = os.path.join(folder_path, 'slope.tif')
        with rasterio.open(slope_file, 'w', **dem_profile) as output_slope:
            output_slope.write(slope_array, 1)
        required_time = round(time.time() - start_time, 2)
        print(
            f'Slope calculation time (seconds): {required_time}',
            flush=True
        )
        summary['Slope calculation time (seconds)'] = required_time

        # flow accumulation array and saving raster
        start_time = time.time()
        flwdir_object = pyflwdir.from_array(
            data=flwdir_array,
            transform=dem_profile['transform']
        )
        flwacc_array = flwdir_object.accuflux(
            data=mask_array
        )
        flwacc_array[mask_array == 0] = dem_profile['nodata']
        dem_profile.update(
            {'dtype': 'float32'}
        )
        flwacc_file = os.path.join(folder_path, 'flwacc.tif')
        with rasterio.open(flwacc_file, 'w', **dem_profile) as output_flwacc:
            output_flwacc.write(flwacc_array, 1)
        required_time = round(time.time() - start_time, 2)
        print(
            f'Flow accumulation calculation time (seconds): {required_time}',
            flush=True
        )
        summary['Flow accumulation calculation time (seconds)'] = required_time

        # maximum flow accumulation
        max_flwacc = int(flwacc_array[mask_array != 0].max())
        summary['Maximum flow accumulation'] = max_flwacc
        threshold = int(max_flwacc * tacc_value / 100) if tacc_type == 'percentage' else tacc_value
        summary['Stream generation from threshold cells'] = threshold
        threshold_area = threshold * cell_area
        summary['Stream generation from threshold area (m^2)'] = threshold_area

        # flow features
        start_time = time.time()
        flwacc_features = flwdir_object.streams(
            mask=flwacc_array >= threshold
        )
        feature_gdf = geopandas.GeoDataFrame.from_features(
            features=flwacc_features,
            crs=dem_profile['crs']
        )
        # flow line GeoDataFrame
        flw_col = 'flw_id'
        flw_gdf = feature_gdf[feature_gdf['pit'] == 0].reset_index(drop=True)
        flw_gdf[flw_col] = list(range(1, flw_gdf.shape[0] + 1))
        flw_gdf = flw_gdf[[flw_col, 'geometry']]
        flw_gdf.to_file(
            filename=os.path.join(folder_path, 'stream_lines.shp')
        )
        required_time = round(time.time() - start_time, 2)
        print(
            f'Stream calculation time (seconds): {required_time}',
            flush=True
        )
        summary['Stream calculation time (seconds)'] = required_time
        summary['Number of stream segments'] = flw_gdf.shape[0]
        # outlet point GeoDataFrame
        outlet_gdf = feature_gdf[feature_gdf['pit'] == 1].reset_index(drop=True)
        outlet_gdf['outlet_id'] = range(1, outlet_gdf.shape[0] + 1)
        outlet_gdf = outlet_gdf.geometry.apply(lambda x: shapely.Point(x.coords[-1]))
        outlet_gdf.to_file(
            filename=os.path.join(folder_path, 'outlet_points.shp')
        )
        summary['Number of outlets'] = outlet_gdf.shape[0]

        # Subbaisn pour point GeoDataFrame
        start_time = time.time()
        pour_gdf = flw_gdf.copy()
        pour_gdf['pour_coords'] = pour_gdf.geometry.apply(
            lambda x: shapely.Point(x.coords[-2])
        )
        pour_gdf['geometry'] = pour_gdf.apply(
            lambda row: shapely.Point(row['pour_coords']),
            axis=1
        )
        pour_gdf = pour_gdf.drop(
            columns=['pour_coords']
        )
        pour_gdf.to_file(
            filename=os.path.join(folder_path, 'subbasin_pour_points.shp')
        )
        # subbasins polygon GeoDataFrame
        subbasin_array = flwdir_object.basins(
            xy=(pour_gdf.geometry.x, pour_gdf.geometry.y),
            ids=pour_gdf[flw_col].astype('uint32')
        )
        subbasin_shapes = rasterio.features.shapes(
            source=subbasin_array.astype('int32'),
            mask=subbasin_array != 0,
            transform=dem_profile['transform'],
            connectivity=8
        )
        subbasin_features = [
            {'geometry': geom, 'properties': {flw_col: val}} for geom, val in subbasin_shapes
        ]
        subbasin_gdf = geopandas.GeoDataFrame.from_features(
            features=subbasin_features,
            crs=dem_profile['crs']
        )
        subbasin_gdf = subbasin_gdf.sort_values(
            by=[flw_col],
            ascending=[True],
            ignore_index=True
        )
        subbasin_gdf['area_m2'] = subbasin_gdf.geometry.area.round(decimals=2)
        # schema dictionary for polygons
        polygon_schema = {
            'geometry': 'Polygon',
            'properties': {
                flw_col: 'int',
                'area_m2': 'float:19.1'
            }
        }
        subbasin_gdf.to_file(
            filename=os.path.join(folder_path, 'subbasins.shp'),
            schema=polygon_schema,
            engine='fiona'
        )
        required_time = round(time.time() - start_time, 1)
        print(
            f'Subbasin calculation time (seconds): {required_time}',
            flush=True
        )
        summary['Subbasin calculation time (seconds)'] = required_time

        # total time to run the program
        total_time = round(time.time() - run_time, 2)
        print(
            f'Total time (seconds): {total_time}',
            flush=True
        )

        summary['Total time (seconds)'] = total_time

        # saving summary
        summary_file = os.path.join(folder_path, 'summary_swatplus_preliminary_files.json')
        with open(summary_file, 'w') as output_summary:
            json.dump(summary, output_summary, indent='\t')

        return 'All geoprocessing has been completed.'
