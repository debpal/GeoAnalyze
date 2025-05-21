import os
import geopandas
import shapely
from .core import Core
from .file import File


class Shape:

    '''
    Provides functionality for shapefile operations.
    '''

    def column_nondecimal_float_to_int_type(
        self,
        input_file: str,
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Converts float columns with whole numbers to integer.

        Parameters
        ----------
        input_file : str
            Path to the input shapefile.

        output_file : str
            Path to save the output shapefile.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame with applicable float columns converted to integer.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # input GeoDataFrame
        gdf = geopandas.read_file(input_file)

        # convert data type from float to integer
        for column in gdf.columns:
            if 'float' in str(gdf[column].dtype):
                no_decimal = (gdf[column] % 1 == 0).all()
                gdf[column] = gdf[column].apply(lambda x: round(x)) if no_decimal else gdf[column]
            else:
                pass

        # saving GeoDataFrame
        gdf.to_file(output_file)

        return gdf

    def column_add_for_id(
        self,
        input_file: str,
        column_name: str,
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Adds an identifier column to the geometries,
        starting from 1 and incrementing by 1.

        Parameters
        ----------
        input_file : str
            Path to the input shapefile.

        colums_name : str
            Name of the identifier column to be added.

        output_file : str
            Path to save the output shapefile.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame with an added identifier column,
            where values start from 1 and increase by 1.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # input GeoDataFrame
        gdf = geopandas.read_file(input_file)

        # insert ID column
        gdf.insert(0, column_name, list(range(1, gdf.shape[0] + 1)))

        # saving output GeoDataFrame
        gdf.to_file(output_file)

        return gdf

    def column_delete(
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
            Path to save the output shapefile.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame with the deletion of speificed columns.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # input GeoDataFrame
        gdf = geopandas.read_file(input_file)

        # list of columns to drop
        delete_cols.remove('geometry') if 'geometry' in delete_cols else delete_cols
        gdf = gdf.drop(columns=delete_cols)

        # saving output GeoDataFrame
        gdf.to_file(output_file)

        return gdf

    def column_retain(
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
            Path to save the output shapefile.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the speificed columns.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
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

    def crs_reprojection(
        self,
        input_file: str,
        target_crs: str,
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Reprojects a GeoDataFrame to a new Coordinate Reference System.

        Parameters
        ----------
        input_file : str
            Path to the input shapefile.

        target_crs : str
            Target Coordinate Reference System for the output GeoDataFrame (e.g., 'EPSG:4326').

        output_file : str
            Path to save the output shapefile.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame with reprojected Coordinate Reference System.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # input GeoDataFrame
        gdf = geopandas.read_file(input_file)

        # crs reprojection
        gdf = gdf.to_crs(target_crs)

        # saving output GeoDataFrame
        gdf.to_file(output_file)

        return gdf

    # pytest pending
    def boundary_box(
        self,
        input_file: str,
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Generate a rectangular bounding box from input geometries.

        Parameters
        ----------
        input_file : str
            Path to the shapefile containing input geometries.

        output_file : str
            Path to the output shapefile where the bounding box polygon will be saved.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing a single polygon representing the bounding box.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # input GeoDataFrame
        gdf = geopandas.read_file(input_file)

        # boundary box
        box_boundary = shapely.box(*list(gdf.total_bounds))

        # GeoDataFrame
        box_gdf = geopandas.GeoDataFrame(
            geometry=[box_boundary],
            crs=gdf.crs
        )
        box_gdf.geometry = box_gdf.geometry.make_valid()
        box_gdf['box_id'] = 1

        # saving output GeoDataFrame
        box_gdf.to_file(output_file)

        return box_gdf

    def polygons_to_boundary_lines(
        self,
        input_file: str,
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Extracts boundary lines from polygons.

        Parameters
        ----------
        input_file : str
            Path to the input polygon shapefile.

        output_file : str
            Path to save the output line shapefile.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the extracted boundary lines of the polygons.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # input GeoDataFrame
        gdf = geopandas.read_file(input_file)

        # polygon to line
        gdf.geometry = gdf.boundary

        # saving output GeoDataFrame
        gdf.to_file(output_file)

        return gdf

    def polygon_fill(
        self,
        input_file: str,
        output_file: str,
        explode: bool = False
    ) -> geopandas.GeoDataFrame:

        '''
        Fills holes in polygon.

        Parameters
        ----------
        input_file : str
            Path to the input shapefile.

        output_file : str
            Path to save the output shapefile.

        explode : bool, optional
            Explode the multi-part polygons, if any, into single pieces
            and fill the holes, if any, inside the polygons. Default is False

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame with any holes in the polygons filled.
        '''

        # check output file
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # confirming input geometry type is Polygon
        geometry_type = Core().shapefile_geometry_type(
            shape_file=input_file
        )
        if 'Polygon' in geometry_type:
            pass
        else:
            raise Exception('Input shapefile must have geometries of type Polygon.')

        # input GeoDataFrame
        gdf = geopandas.read_file(input_file)

        # polygon filling
        tmp_col = Core()._tmp_df_column_name(list(gdf.columns))
        gdf = gdf.reset_index(names=[tmp_col])
        gdf = gdf.explode(index_parts=False, ignore_index=True)
        gdf = gdf.drop_duplicates(
            subset=['geometry'],
            ignore_index=True
        )
        gdf.geometry = gdf.geometry.apply(
            lambda x: shapely.Polygon(x.exterior.coords)
        )
        gdf = gdf.dissolve(by=[tmp_col]) if explode is False else gdf.drop(columns=[tmp_col])
        gdf = gdf.reset_index(drop=True)

        # saving output geodataframe
        gdf.to_file(output_file)

        return gdf

    def polygon_fill_after_merge(
        self,
        input_file: str,
        column_name: str,
        output_file: str,
    ) -> geopandas.GeoDataFrame:

        '''
        Merges overlapping polygons, explodes multi-part,
        and fills any holes within the polygons.

        Parameters
        ----------
        input_file : str
            Path to the input shapefile.

        column_name : str
            Name of the column to assign unique identifiers to each polygon after merging.

        output_file : str
            Path to save the output shapefile.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing individual polygons after merging, exploding, and
            filling holes, with each polygon assigned an ID from the specified column.
        '''

        # check output file
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # confirming input geometry type is Polygon
        geometry_type = Core().shapefile_geometry_type(
            shape_file=input_file
        )
        if 'Polygon' in geometry_type:
            pass
        else:
            raise Exception('Input shapefile must have geometries of type Polygon.')

        # input GeoDataFrame
        gdf = geopandas.read_file(input_file)

        # polygon filling
        merge_polygons = gdf.union_all()
        gdf = geopandas.GeoDataFrame(
            geometry=[merge_polygons],
            crs=gdf.crs
        )
        gdf = gdf.explode(index_parts=False, ignore_index=True)
        gdf = gdf.drop_duplicates(
            subset=['geometry'],
            ignore_index=True
        )
        gdf.geometry = gdf.geometry.apply(
            lambda x: shapely.Polygon(x.exterior.coords)
        )
        gdf.insert(0, column_name, list(range(1, gdf.shape[0] + 1)))

        # saving output geodataframe
        gdf.to_file(output_file)

        return gdf

    def polygon_count_by_cumsum_area(
        self,
        shape_file: str
    ) -> dict[float, int]:

        '''
        Sorts the polygons by area in descending order, calculate cumulative sum percentages,
        and returns a dictionary with cumulative area percentages as keys
        and the corresponding cumulative polygon counts as values.

        Parameters
        ----------
        shape_file : str
            Path to the input shapefile.

        Returns
        -------
        dict
            A dictionary where the keys are cumulative percentage areas of polygons,
            and values are the cumulative counts of polygons.
        '''

        # confirming input geometry type is Polygon
        geometry_type = Core().shapefile_geometry_type(
            shape_file=shape_file
        )
        if 'Polygon' not in geometry_type:
            raise Exception('Input shapefile must have geometries of type Polygon.')

        # input GeoDataFrame
        gdf = geopandas.read_file(shape_file)

        # cumulative area percentage of polygons
        tmp_col = Core()._tmp_df_column_name(list(gdf.columns))
        per_col = tmp_col + '(%)'
        cumsum_col = per_col + '-cs'
        gdf[tmp_col] = gdf.geometry.area
        gdf = gdf.sort_values(by=[tmp_col], ascending=[False])
        gdf[per_col] = 100 * gdf[tmp_col] / gdf[tmp_col].sum()
        gdf[cumsum_col] = gdf[per_col].cumsum().round()

        # count cumulative percentage
        cumsum_df = gdf[cumsum_col].value_counts().to_frame().reset_index(names=['Cumsum(%)'])
        cumsum_df = cumsum_df.sort_values(by=['Cumsum(%)'], ascending=[True]).reset_index(drop=True)
        cumsum_df['Count_cumsum'] = cumsum_df['count'].cumsum()
        output = dict(
            zip(
                cumsum_df['Cumsum(%)'],
                cumsum_df['Count_cumsum']
            )
        )

        return output

    def polygons_remove_by_cumsum_area_percent(
        self,
        input_file: str,
        percent_cutoff: float,
        output_file: str,
        index_sort: bool = False
    ) -> geopandas.GeoDataFrame:

        '''
        Sorts the percentage area of polygons in descending order
        and removes polygons whose cumulative percentage
        exceeds the specified cutoff (ranging from 0 to 100).

        Parameters
        ----------
        input_file : str
            Path to the input shapefile.

        percent_cutoff : float
            Only polygons with a cumulative area percentage less than or equal
            to the specified cutoff (between 0 and 100) are retained.

        output_file : str
            Path to save the output shapefile.

        index_sort : bool, False
            If True, polygons are sorted by their index before sorting cumulative area percentages.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing polygons with a cumulative area percentage
            less than or equal to the specified cutoff.
        '''

        # check output file
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # confirming input geometry type is Polygon
        geometry_type = Core().shapefile_geometry_type(
            shape_file=input_file
        )
        if 'Polygon' not in geometry_type:
            raise Exception('Input shapefile must have geometries of type Polygon.')

        # input GeoDataFrame
        gdf = geopandas.read_file(input_file)

        # removing polygons
        tmp_col = Core()._tmp_df_column_name(list(gdf.columns))
        per_col = tmp_col + '(%)'
        cumsum_col = per_col + '-cs'
        gdf[tmp_col] = gdf.geometry.area
        gdf = gdf.sort_values(by=[tmp_col], ascending=[False])
        gdf[per_col] = 100 * gdf[tmp_col] / gdf[tmp_col].sum()
        gdf[cumsum_col] = gdf[per_col].cumsum()
        gdf = gdf[gdf[cumsum_col] <= percent_cutoff]
        gdf = gdf.sort_index() if index_sort else gdf
        gdf = gdf.reset_index(drop=True)
        gdf = gdf.drop(columns=[tmp_col, per_col, cumsum_col])

        # saving output GeoDataFrame
        gdf.to_file(output_file)

        return gdf

    def extract_spatial_join_geometries(
        self,
        input_file: str,
        overlay_file: str,
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Performs a spatial join to extract geometries
        that intersect with other geometries.

        Parameters
        ----------
        input_file : str
            Path to the input shapefile.

        overlay_file : str
            Path to the input overlay shapefile.

        output_file : str
            Path to save the output shapefile.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame of extracted geometries that intersect with other geometries.
        '''

        # check output file
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # input GeoDataFrame
        input_gdf = geopandas.read_file(input_file)

        # overlay GeoDataFrame
        overlay_gdf = geopandas.read_file(overlay_file)

        # extracting geometries
        extract_gdf = geopandas.sjoin(
            left_df=input_gdf,
            right_df=overlay_gdf,
            how='inner'
        )
        extract_gdf = extract_gdf.iloc[:, :input_gdf.shape[1]]
        extract_gdf.columns = input_gdf.columns
        extract_gdf = extract_gdf.drop_duplicates(
            subset=['geometry'],
            ignore_index=True
        )

        # saving output GeoDataFrame
        extract_gdf.to_file(output_file)

        return extract_gdf

    def aggregate_geometries(
        self,
        folder_path: str,
        geometry_type: str,
        column_name: str,
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Aggregates geometries of a specified type from shapefiles in a folder.

        Parameters
        ----------
        folde_path : str
            Folder path containing the input shapefiles.

        geometry_type : str
            Type of geometry to aggregate, one of 'Point', 'LineString', or 'Polygon'.

        column_name : str
            Name of the column where unique identifiers will be assigned to each geometry after aggregation.

        output_file : str
            Path to save the output shapefile.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing all geometries of the specified type
            aggregated from the shapefiles in the folder.
        '''

        # check output file
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # get shape files
        shapefiles = File().extract_specific_extension(
            folder_path=folder_path,
            extension='.shp'
        )

        # files path
        files_path = map(
            lambda x: os.path.join(folder_path, x), shapefiles
        )

        # polygon files
        polygon_files = filter(
            lambda x: geometry_type in Core().shapefile_geometry_type(x), files_path
        )

        # GeoDataFrames
        gdfs = list(map(lambda x: geopandas.read_file(x), polygon_files))

        # check same Coordinate Reference System of all shapefiles
        target_crs = gdfs[0].crs
        same_crs = all(map(lambda gdf: gdf.crs == target_crs, gdfs))
        if same_crs is True:
            pass
        else:
            raise Exception('Not all shapefiles have the same Coordinate Reference System.')

        # aggregate GeoDataFrame
        geometries = []
        for gdf in gdfs:
            geometries.extend(list(gdf.geometry))
        aggr_gdf = geopandas.GeoDataFrame(
            geometry=geometries,
            crs=target_crs
        )
        aggr_gdf = aggr_gdf.drop_duplicates(
            subset=['geometry'],
            ignore_index=True
        )
        aggr_gdf[column_name] = range(1, len(aggr_gdf) + 1)

        # saving GeoDataFrame
        aggr_gdf.to_file(output_file)

        return aggr_gdf
