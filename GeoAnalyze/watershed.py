import os
import typing
import time
import json
import pyflwdir
import rasterio
import rasterio.features
import shapely
import geopandas
import numpy
from .core import Core
from .raster import Raster


class Watershed:

    '''
    Provides functionality for watershed delineation from Digital Elevation Model (DEM).
    '''

    def dem_extended_area_to_basin(
        self,
        input_file: str,
        basin_file: str,
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Computes the basin from an extended DEM area by considering the highest flow accumulation point
        as the main outlet. Generally, open-source DEMs have a rectangular shape with a geographic
        Coordinate Reference System (CRS). The DEM must be converted to a projected CRS using the
        :meth:`GeoAnalyze.Raster.crs_reprojection` method.

            .. note::
                Since the basin is generated without any input outlet point, the main outlet point should be
                located close to the corresponding edge of the extended DEM area. The greater the distance
                between the outlet point and the edge of the extended DEM area, the higher the probability
                of obtaining a larger basin area than expected.

        Parameters
        ----------
        input_file : str
            Path to the input DEM raster file.

        basin_file : str
            Path to save the output basin shapefile.

        output_file : str
            Path to save the output clipped DEM raster file by the basin area.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame representing the output basin polygon area.
        '''

        # time at starting of the program
        run_time = time.time()

        # check validity of output shapefile path
        check_file = Core().is_valid_ogr_driver(basin_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # check validity of output raster file path
        check_file = Core().is_valid_raster_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # flow direction array
        start_time = time.time()
        with rasterio.open(input_file) as input_dem:
            dem_profile = input_dem.profile
            dem_array = input_dem.read(1).astype('float32')
            dem_res = input_dem.res
            pitfill_array, flwdir_array = pyflwdir.dem.fill_depressions(
                elevtn=dem_array,
                outlets='edge',
                nodata=dem_profile['nodata']
            )
            required_time = round(time.time() - start_time, 2)
            print(
                f'Pit filling and flow direction calculation time (seconds): {required_time}',
                flush=True
            )

        # flow accumulation array
        start_time = time.time()
        mask_array = (dem_array != dem_profile['nodata']).astype('int32')
        flwdir_object = pyflwdir.from_array(
            data=flwdir_array,
            transform=dem_profile['transform']
        )
        flwacc_array = flwdir_object.accuflux(
            data=mask_array
        )
        flwacc_array[mask_array == 0] = dem_profile['nodata']
        required_time = round(time.time() - start_time, 2)
        print(
            f'Flow accumulation calculation time (seconds): {required_time}',
            flush=True
        )

        # highest flow accumulation point GeoDataFrame
        start_time = time.time()
        point_shape = rasterio.features.shapes(
            source=flwacc_array,
            mask=flwacc_array == flwacc_array.max(),
            transform=dem_profile['transform']
        )
        point_feature = [
            {'geometry': geom, 'properties': {'flwacc': val}} for geom, val in point_shape
        ]
        point_gdf = geopandas.GeoDataFrame.from_features(
            features=point_feature,
            crs=dem_profile['crs']
        )
        point_gdf['id'] = 1
        point_gdf['geometry'] = point_gdf.geometry.centroid

        # basin polygon GeoDataFrame
        basin_array = flwdir_object.basins(
            xy=(point_gdf.geometry.x, point_gdf.geometry.y),
            ids=point_gdf['id'].astype('uint32')
        )
        basin_shape = rasterio.features.shapes(
            source=basin_array.astype('int32'),
            mask=basin_array != 0,
            transform=dem_profile['transform'],
            connectivity=8
        )
        basin_feature = [
            {'geometry': geom, 'properties': {'id': val}} for geom, val in basin_shape
        ]
        basin_gdf = geopandas.GeoDataFrame.from_features(
            features=basin_feature,
            crs=dem_profile['crs']
        )
        flwacc_value = point_gdf['flwacc'].iloc[0]
        basin_gdf['flwacc'] = flwacc_value
        basin_gdf.to_file(basin_file)
        required_time = round(time.time() - start_time, 2)
        print(
            f'Basin calculation time (seconds): {required_time}',
            flush=True
        )
        print(
            f'Basin area: {flwacc_value * dem_res[0] * dem_res[1]}',
            flush=True
        )

        # dem clipping
        Raster().clipping_by_shapes(
            input_file=input_file,
            shape_file=basin_file,
            output_file=output_file
        )

        # total time to run the program
        total_time = round(time.time() - run_time, 2)
        print(
            f'Total time (seconds): {total_time}',
            flush=True
        )

        return basin_gdf

    def dem_delineation(
        self,
        dem_file: str,
        outlet_type: str,
        tacc_type: str,
        tacc_value: float,
        folder_path: str
    ) -> str:

        '''
        Generates delineation raster outputs, including flow direction (`flwdir.tif`), slope (`slope.tif`), aspect (`aspect.tif`),
        and flow accumulation (`flwacc.tif`). Using the provided flow accumulation threshold, the function also generates shapefiles
        for streams (`stream_lines.shp`), subbasins (`subbasins.shp`), subbasin drainage points (`subbasin_drainage_points.shp`), and main outlets
        (`outlet_points.shp`). All shapefiles share a common identifier column, `flw_id`, for easy cross-referencing.

        The `subbasins.shp` file contains an additional column, `area_m2`, which stores the area of each subbasin.
        The `subbasin_drainage_points.shp` file contains an additional column, `flwacc`, which stores the flow accumulation value at the drainage points.

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
            The 'percentage' option uses the percent value of the maximum flow accumulation, while
            'absolute' specifies a threshold based on a specific number of cells.

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
        summary: dict[str, typing.Any] = {}

        # check validity of output folder path
        if os.path.isdir(folder_path) is False:
            raise Exception('Input folder path does not exsit.')

        # check validty of outlet type
        if outlet_type not in ['single', 'multiple']:
            raise Exception('Outlet type must be one of [single, multiple].')

        # check validity of threshold flow accumalation type
        if tacc_type not in ['percentage', 'absolute']:
            raise Exception('Threshold accumulation type must be one of [percentage, absolute].')

        # DEM and mask array
        start_time = time.time()
        with rasterio.open(dem_file) as input_dem:
            dem_shape = input_dem.shape
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

        # aspect array and saving raster
        start_time = time.time()
        grad_y, grad_x = numpy.gradient(
            dem_array,
            input_dem.res[1],
            input_dem.res[0],
        )
        aspect_array = numpy.arctan2(-grad_y, grad_x) * (180 / numpy.pi)
        aspect_array[aspect_array < 0] += 360
        aspect_array[dem_array == dem_profile['nodata']] = dem_profile['nodata']
        aspect_file = os.path.join(folder_path, 'aspect.tif')
        with rasterio.open(aspect_file, 'w', **dem_profile) as output_aspect:
            output_aspect.write(aspect_array, 1)
        required_time = round(time.time() - start_time, 2)
        print(
            f'Aspect calculation time (seconds): {required_time}',
            flush=True
        )
        summary['Aspect calculation time (seconds)'] = required_time

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
        summary['Flow accumulation threshold type and value'] = (tacc_type, tacc_value)
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

        # subbaisn pour point GeoDataFrame
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
        pour_array = rasterio.features.rasterize(
            shapes=zip(pour_gdf.geometry, pour_gdf['flw_id']),
            out_shape=dem_shape,
            transform=dem_profile['transform'],
            all_touched=True,
            fill=dem_profile['nodata'],
            dtype=dem_profile['dtype']
        )
        pour_flwacc = {}
        for pid in pour_gdf['flw_id']:
            pid_flwacc = flwacc_array[pour_array == pid]
            pour_flwacc[pid] = pid_flwacc[0]
        pour_gdf['flwacc'] = pour_gdf['flw_id'].apply(lambda x: pour_flwacc.get(x))
        pour_gdf.to_file(
            filename=os.path.join(folder_path, 'subbasin_drainage_points.shp')
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
        subbasin_gdf.geometry = subbasin_gdf.geometry.make_valid()
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

    def get_flwdir(
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

        # check validty of outlet type
        if outlet_type not in ['single', 'multiple']:
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

    def get_flwacc(
        self,
        flwdir_file: str,
        flwacc_file: str
    ) -> str:

        '''
        Computes flow accumulation from flow direction rasters.

        Parameters
        ----------
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

        # flow direction object
        with rasterio.open(flwdir_file) as input_flwdir:
            raster_profile = input_flwdir.profile
            flwdir_array = input_flwdir.read(1)
            mask_array = (flwdir_array != input_flwdir.nodata).astype('int32')
            flwdir_object = pyflwdir.from_array(
                data=flwdir_array,
                transform=raster_profile['transform']
            )
            # flow accumulation array
            flwacc_array = flwdir_object.accuflux(
                data=mask_array
            )
        max_flwacc = flwacc_array.max()
        print(f'Maximum flow accumulation: {max_flwacc}.')
        # saving flow accumulation raster
        flwacc_array[mask_array == 0] = -9999
        raster_profile.update(
            {
                'dtype': 'float32',
                'nodata': -9999
            }
        )
        with rasterio.open(flwacc_file, 'w', **raster_profile) as output_flwacc:
            output_flwacc.write(flwacc_array, 1)

        # required time
        required_time = time.time() - start_time
        output = f'Time required for computing flow accumulation: {required_time:.2f} seconds.'

        return output

    def get_stream(
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
            The 'percentage' option uses the percent value of the maximum flow accumulation, while
            'absolute' specifies a threshold based on a specific number of cells.

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

        # check validity of flow accumulation thereshold type
        if tacc_type not in ['percentage', 'absolute']:
            raise Exception('Threshold accumulation type must be one of [percentage, absolute].')

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

    def get_subbasins(
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

    def get_aspect(
        self,
        dem_file: str,
        aspect_file: str
    ) -> str:

        '''
        Computes the terrain aspect from a DEM without applying pit filling.

        Parameters
        ----------
        dem_file : str
            Path to the input DEM raster file (e.g., GeoTIFF).

        aspect_file : str
            Path to save the output aspect raster file.

        Returns
        -------
        str
            A message indicating the time required for all geoprocessing computations.
        '''

        # start time
        start_time = time.time()

        # check validity of output file path
        check_file = Core().is_valid_raster_driver(aspect_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # aspect raster
        with rasterio.open(dem_file) as input_dem:
            dem_profile = input_dem.profile
            dem_array = input_dem.read(1)
            grad_y, grad_x = numpy.gradient(
                dem_array,
                input_dem.res[1],
                input_dem.res[0],
            )
            # angles
            aspect_array = numpy.arctan2(-grad_y, grad_x) * (180 / numpy.pi)
            # negative angles to compass direction
            aspect_array[aspect_array < 0] += 360
            aspect_array[dem_array == dem_profile['nodata']] = dem_profile['nodata']
            # update raster profile
            dem_profile.update(
                {
                    'dtype': 'float32'
                }
            )
            # saving the raster
            with rasterio.open(aspect_file, 'w', **dem_profile) as output_aspect:
                output_aspect.write(aspect_array, 1)

        # required time
        required_time = time.time() - start_time
        output = f'Time required for computing aspect: {required_time:.2f} seconds.'

        return output

    def get_slope(
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

        # slope raster
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

        # check lengths of lowerbounds and reclass values
        if len(reclass_values) != len(reclass_lb):
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
