import geopandas
import shapely
import pandas
import pyogrio
import os
import typing
import operator
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
        column_list: list[str],
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Delete specified columns from a GeoDataFrame.
        Useful when the user wants to delete specific columns.

        Parameters
        ----------
        input_file : str
            Path to the input shapefile.

        column_list : list
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
        column_list.remove('geometry') if 'geometry' in column_list else column_list
        gdf = gdf.drop(columns=column_list)

        # saving output GeoDataFrame
        gdf.to_file(output_file)

        return gdf

    def column_retain(
        self,
        input_file: str,
        column_list: list[str],
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

        column_list : list
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
        column_list = column_list + ['geometry']
        drop_cols = [col for col in gdf.columns if col not in column_list]
        gdf = gdf.drop(columns=drop_cols)

        # saving output GeoDataFrame
        gdf.to_file(output_file)

        return gdf

    def column_unique_values(
        self,
        shape_file: str,
        column_list: list[str] | None = None
    ) -> dict[str, list[typing.Any]]:

        '''
        Retrieves unique values from specified columns in a shapefile.

        Parameters
        ----------
        shape_file : str
            Path to the input shapefile.

        column_list : list, optional
            List of column names to extract unique values from, excluding the 'geometry' column.
            Defaults to None, in which case all non-geometry columns are selected.

        Returns
        -------
        dict
            A dictionary where each key is a column name and the corresponding value
            is a list of that column's unique entries.
        '''

        # getting unique values
        gdf = geopandas.read_file(shape_file)
        unique_values = {}
        target_columns = list(gdf.columns) if column_list is None else column_list
        for col in target_columns:
            if col != 'geometry':
                unique_values[col] = gdf[col].unique().tolist()

        return unique_values

    def column_area_by_value(
        self,
        shape_file: str,
        column_name: str,
        csv_file: str,
        descending_area: bool = True
    ) -> pandas.DataFrame:

        '''
        Calculate the total area for each unique value
        in a specified column of the input shapefile.

        Parameters
        ----------
        shape_file : str
            Path to the input shapefile.

        column_name : str
            Name of the target column.

        csv_file : str
            Path to the CSV file where the output DataFrame will be saved.

        descending_area : bool, optional
             If True, the output DataFrame is sorted in descending order by area.
             The default is True.

        Returns
        -------
        DataFrame
            A DataFrame with unique column values,
            their corresponding total area, and area percentage.
        '''

        # check LineString geometry type
        if 'Polygon' not in Core().shapefile_geometry_type(shape_file):
            raise Exception('Input shapefile must have geometries of type Polygon.')

        # unique column entries
        gdf = geopandas.read_file(shape_file)
        unique_values = gdf[column_name].unique().tolist()

        # get area for unique values
        area_list = []
        for i in unique_values:
            i_area = gdf[gdf[column_name].isin([i])].geometry.area.sum()
            area_list.append(
                {
                    'value': i,
                    'area': i_area
                }
            )

        # DataFrame
        df = pandas.DataFrame.from_records(
            data=area_list
        )
        df['area (%)'] = 100 * df['area'] / df['area'].sum()
        df = df.sort_values(
            by='area (%)',
            ascending=not descending_area,
            ignore_index=True
        )

        # saving the DataFrame
        df.to_csv(
            path_or_buf=csv_file,
            sep='\t',
            index_label='index'
        )

        return df

    def column_add_mapped_values(
        self,
        input_file: str,
        column_exist: str,
        column_new: str,
        mapping_value: dict[typing.Any, typing.Any],
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Adds a new column to the GeoDataFrame from the input shapefile,
        using a mapping applied to values in an existing column.

        Parameters
        ----------
        input_file : str
            Path to the input shapefile.

        column_exsit : str
            Name of the existing column in the GeoDataFrame to be used for value mapping.

        column_new : str
            Name of the new column to be added to the GeoDataFrame.

        mapping_value : dict
            A dictionary where keys correspond to unique values in the existing column,
            and values are the new values to assign in the new column.

        output_file : str
            Path to the shapefile where the output GeoDataFrame will be saved.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame with an additional column containing values mapped from the existing column.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # value mapping of new column
        gdf = geopandas.read_file(input_file)
        gdf[column_new] = gdf[column_exist].apply(
            lambda x: mapping_value.get(x)
        )

        # saving modified geodataframe
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

    def extract_polygons_by_overlap_threshold(
        self,
        input_file: str,
        mask_file: str,
        output_file: str,
        overlap_percent: float = 0,
        greater_strict: bool = False,
        overlap_col: str = 'overlap(%)'
    ) -> geopandas.GeoDataFrame:

        '''
        Extracts polygons from an input shapefile based on their overlap percentage with mask geometries.

            .. note::
                Although extraction is based on overlap percentage, the output shapefile
                will contain the entire original polygons, not clipped geometries.

        Parameters
        ----------
        input_file : str
            Path to the input polygon shapefile.

        mask_file : str
            Path to the mask polygon shapefile used for overlap calculation.

        output_file : str
            Path to the output shapefile where the extracted polygons will be saved.

        overlap_percent : float, optional
            Threshold for minimum percentage of overlap to include a polygon.
            Default is 0, meaning all overlapping geometries are included.

        greater_strict : bool, optional
            If False (default), includes polygons with overlap percentage greater than or equal to `overlap_percent`.
            If True, includes only those with overlap strictly greater than `overlap_percent`.

        overlap_col : str, optional
            Name of the column in the output shapefile that will store the computed overlap percentages.
            Default is 'overlap(%)'.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing polygons that meet the specified overlap threshold with the mask geometries.
        '''

        # check validity of output file path
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
        tmp_col = '1tc3_id'
        input_gdf = geopandas.read_file(input_file)
        input_gdf['tc_actual_area'] = input_gdf.geometry.area
        input_gdf = input_gdf.reset_index(names=tmp_col)

        # overlap GeoDataFrame
        overlap_gdf = geopandas.overlay(
            df1=input_gdf.copy(),
            df2=geopandas.read_file(mask_file),
            how='intersection'
        )

        # raise error if no overlapping geometry if found
        if overlap_gdf.shape[0] == 0:
            raise Exception('No overlapping geometry found')

        # extract polygons index
        overlap_gdf['tc_overlap_area'] = overlap_gdf.geometry.area
        overlap_gdf = overlap_gdf.drop(
            columns=['tc_actual_area']
        )
        overlap_gdf = overlap_gdf.merge(
            right=input_gdf[[tmp_col, 'tc_actual_area']],
            on=[tmp_col]
        )
        overlap_gdf[overlap_col] = 100 * overlap_gdf['tc_overlap_area'] / overlap_gdf['tc_actual_area']
        greater_sign = operator.gt if greater_strict else operator.ge
        extract_rows = overlap_gdf[greater_sign(overlap_gdf[overlap_col], overlap_percent)][tmp_col].tolist()

        # saving GeoDataFrame
        extract_gdf = input_gdf[input_gdf[tmp_col].isin(extract_rows)].reset_index(drop=True)
        extract_gdf = extract_gdf.merge(
            right=overlap_gdf[[tmp_col, overlap_col]],
            on=[tmp_col]
        )
        extract_gdf[overlap_col] = extract_gdf[overlap_col].round(2)
        extract_gdf = extract_gdf.drop(
            columns=[tmp_col, 'tc_actual_area']
        )
        extract_gdf.to_file(output_file)

        return extract_gdf

    def aggregate_geometries_from_shapefiles(
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

    def aggregate_geometries_from_layers(
        self,
        input_file: str,
        geometry_type: str,
        output_file: str,
        column_list: list[str] | None = None,
        layer_column: str = 'layer'
    ) -> geopandas.GeoDataFrame:

        '''
        Aggregates geometries of a specified type from multiple layers in an input file.

        Parameters
        ----------
        input_file : str
            Path to the input file containing multiple layers.

        geometry_type : str
            Type of geometry to aggregate. Must be one of: 'Point', 'LineString', or 'Polygon'.

        output_file : str
            Path to the output file where the aggregated GeoDataFrame will be saved.

        column_list : list, optional
            List of common columns (excluding 'geometry') to include in the aggregated GeoDataFrame.
            If None (default), only the 'geometry' column and an additional column with the layer name
            will be included.

        layer_column : str, optional
            Name of the column that will store the layer names in the aggregated GeoDataFrame. Default is 'layer'.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing all geometries of the specified type
            aggregated from the layers of the input file, including a column with the corresponding layer names.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # check for restricted use of 'geometry' in column_list
        if column_list is not None and 'geometry' in column_list:
            raise Exception(
                'The column name "geometry" cannot be included in the column_list.'
            )

        # check for restricted use of the layer column name in column_list
        if column_list is not None and layer_column in column_list:
            raise Exception(
                f'To include "{layer_column}" in column_list, the name of the optional variable layer_column must be changed.'
            )

        # check geometry type
        geometry_list = ['Point', 'LineString', 'Polygon']
        if geometry_type not in geometry_list:
            raise Exception(
                f'Input geometry type must be one of {geometry_list}.'
            )

        # target layers in the KML file
        layer_list = []
        for layer_name, layer_type in pyogrio.list_layers(input_file):
            if layer_type is not None and geometry_type in layer_type:
                layer_list.append(layer_name)

        # list of GeoDataFrames for layers
        gdf_list = []
        default_cols = [layer_column, 'geometry']
        for layer in layer_list:
            layer_gdf = geopandas.read_file(
                filename=input_file,
                layer=layer
            )
            layer_gdf[layer_column] = layer
            gdf_columns = default_cols if column_list is None else column_list + default_cols
            layer_gdf = layer_gdf[gdf_columns]
            gdf_list.append(layer_gdf)

        # combine the GeoDataFrames
        gdf = geopandas.GeoDataFrame(
            pandas.concat(
                objs=gdf_list,
                ignore_index=True
            )
        )

        # saving GeoDataFrame
        gdf.to_file(
            filename=output_file
        )

        return gdf
