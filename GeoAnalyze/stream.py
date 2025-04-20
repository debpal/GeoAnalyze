import geopandas
import shapely
import random
import pandas
import typing
import tempfile
import os
import json
from .core import Core


class Stream:

    '''
    Provides functionality for stream path operations.
    '''

    def flw_path_us2ds_check(
        self,
        stream_file: str
    ) -> bool:

        '''
        Checks the flow path direction from upstream to downstream
        by comparing the number of segments in the flow path
        to the number of their most upstream points.

        Parameters
        ----------
        stream_file : str
            Path to the input stream shapefile.

        Returns
        -------
        bool
            True if the number of flow path segments aligns with
            the number of upstream points, indicating correct
            flow direction; otherwise, False.
        '''

        # check LineString geometry type
        if 'LineString' not in Core().shapefile_geometry_type(stream_file):
            raise Exception('Input shapefile must have geometries of type LineString.')

        # stream GeoDataFrame
        gdf = geopandas.read_file(stream_file)
        gdf = gdf.explode(
            index_parts=False,
            ignore_index=True
        )

        # upstream points
        upstream_points = set(gdf.geometry.apply(lambda x: x.coords[0]))

        # check flow direction
        output = True if len(gdf) == len(upstream_points) else False

        return output

    def flw_path_reverse(
        self,
        input_file: str,
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Reverses the coordinate order for each segment in the input flow path,
        ensuring that the starting point of each segment becomes its most upstream point.

        Parameters
        ----------
        input_file : str
            Path to the input stream shapefile.

        output_file : str
            Path to save the output stream shapefile.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame with each stream segment’s coordinates reversed.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # check LineString geometry type
        if 'LineString' not in Core().shapefile_geometry_type(input_file):
            raise Exception('Input shapefile must have geometries of type LineString.')

        # input stream GeoDataFrame
        gdf = geopandas.read_file(input_file)
        tmp_col = Core()._tmp_df_column_name(list(gdf.columns))
        gdf = gdf.reset_index(names=[tmp_col])
        gdf = gdf.explode(index_parts=False, ignore_index=True)

        # reversed stream coordinates order
        gdf.geometry = gdf.geometry.apply(
            lambda x: shapely.LineString(x.coords[::-1])
        )
        upstream_points = len(
            set(
                gdf.geometry.apply(lambda x: x.coords[0])
            )
        )
        output = f'Flow segments: {len(gdf)}, upstream points: {upstream_points} after splitting MultiLineString(s), if present.'
        gdf = gdf.dissolve(by=[tmp_col]).reset_index(drop=True)

        # saving output GeoDataFrame
        gdf.to_file(output_file)

        return output

    def connectivity_adjacent_downstream_segment(
        self,
        input_file: str,
        stream_col: str,
        output_file: str,
        link_col: str = 'ds_id',
        unlinked_id: int = -1
    ) -> geopandas.GeoDataFrame:

        '''
        Identifies the adjacent connected downstream identifier
        for each segment in a stream network shapefile.

        Parameters
        ----------
        input_file : str
            Path to the input stream shapefile.

        stream_col : str
            Column name in the stream shapefile containing
            a unique identifier for each stream segment.

        output_file : str
            Path to save the output stream shapefile
            with adjacent downstream connectivity information.

        link_col : str, optional
            Name of the column to store the connected
            downstream segment identifiers. Default is 'ds_id'.

        unlinked_id : int, optional
            Value to assign when a downstream segment identifier
            is not found. Default is -1.

        Returns
        -------
        GeoDataFrame
             A GeoDataFrame representing the input shapefile,
             enhanced with an additional column that indicates
             the downstream segment identifier for each feature.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # check LineString geometry type
        if 'LineString' not in Core().shapefile_geometry_type(input_file):
            raise Exception('Input shapefile must have geometries of type LineString.')

        # stream geodataframe
        stream_gdf = geopandas.read_file(input_file)

        # endpoints of flow segments
        upstream_points = {
            idx: line.coords[0] for idx, line in zip(stream_gdf[stream_col], stream_gdf.geometry)
        }
        downstream_points = {
            idx: line.coords[-1] for idx, line in zip(stream_gdf[stream_col], stream_gdf.geometry)
        }

        # downstream segment identifiers
        downstream_link = {}
        for dp_id in downstream_points.keys():
            up_link = list(
                filter(
                    lambda up_id: upstream_points[up_id] == downstream_points[dp_id], upstream_points
                )
            )
            if len(up_link) == 1:
                downstream_link[dp_id] = up_link[0]
            else:
                downstream_link[dp_id] = unlinked_id

        # saving output GeoDataFrame
        stream_gdf[link_col] = downstream_link.values()
        stream_gdf.to_file(output_file)

        return stream_gdf

    def connectivity_adjacent_upstream_segment(
        self,
        stream_file: str,
        stream_col: str,
        csv_file: str,
        link_col: str = 'us_id',
        unlinked_id: int = -1
    ) -> pandas.DataFrame:

        '''
        Identifies the adjacent connected upstream identifiers
        for each segment in a stream network shapefile.

        Parameters
        ----------
        input_file : str
            Path to the input stream shapefile.

        stream_col : str
            Column name in the stream shapefile containing
            a unique identifier for each stream segment.

        csv_file : str
            Path to save the output CSV file
            with adjacent upstream connectivity information.

        link_col : str, optional
            Name of the column to store the connected
            upstream segment identifiers. Default is 'us_id'.

        unlinked_id : int, optional
            Value to assign when an upstream segment identifier
            is not found. Default is -1.

        Returns
        -------
        DataFrame
            A DataFrame with two columns `stream_col` and `link_col`.
            The `stream_col` contains stream segment identifiers
            (which may appear multiple times), and the `link_col` contains
            their corresponding connected adjacent upstream segment identifiers.
        '''

        # check LineString geometry type
        if 'LineString' not in Core().shapefile_geometry_type(stream_file):
            raise Exception('Input shapefile must have geometries of type LineString.')

        # temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # connectivity to downstream segment identifiers
            stream_gdf = self.connectivity_adjacent_downstream_segment(
                input_file=stream_file,
                stream_col=stream_col,
                output_file=os.path.join(tmp_dir, 'stream_downstream_id.shp')
            )
            # non headwater segments by exchanging stream and adjacent donwstream columns
            nhw_df = stream_gdf[['ds_id', stream_col]]
            nhw_df = nhw_df[~nhw_df['ds_id'].isin([-1])].reset_index(drop=True)
            nhw_df.columns = [stream_col, link_col]
            # predict headwater segments
            hw_list = [
                i for i in stream_gdf[stream_col] if i not in nhw_df[stream_col].tolist()
            ]
            hw_df = pandas.DataFrame({stream_col: hw_list})
            hw_df[link_col] = unlinked_id
            # adjance upstream segements
            ul_df = pandas.concat(
                objs=[nhw_df, hw_df],
                ignore_index=True
            )
            ul_df = ul_df.sort_values(
                by=[stream_col, link_col],
                ignore_index=True
            )
            # saving adjacent upstream connectivity
            ul_df.to_csv(
                path_or_buf=csv_file,
                sep='\t',
                index=False
            )

        return ul_df

    def connectivity_upstream_to_downstream(
        self,
        stream_file: str,
        stream_col: str,
        json_file: str
    ) -> dict[float, list[float]]:

        '''
        Identifies all consecutively connected downstream segment identifiers
        up to the outlet point for each segment in a stream network shapefile.

        Parameters
        ----------
        stream_file : str
            Path to the input stream shapefile.

        stream_col : str
            Column name in the stream shapefile containing
            a unique identifier for each stream segment.

        json_file : str
            Path to save the output JSON file
            representing upstream to downstream connections.

        Returns
        -------
        dict
            A dictionary where each key is a stream segment identifier,
            and the corresponding value is a list of all consecutively
            connected downstream identifiers, ending at the outlet.
            If no connected downstream segment is found, the value list
            contains the segment identifier itself.
        '''

        # check LineString geometry type
        if 'LineString' not in Core().shapefile_geometry_type(stream_file):
            raise Exception('Input shapefile must have geometries of type LineString.')

        # temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # connectivity to downstream segment identifiers
            stream_gdf = self.connectivity_adjacent_downstream_segment(
                input_file=stream_file,
                stream_col=stream_col,
                output_file=os.path.join(tmp_dir, 'stream_downstream_id.shp')
            )
            stream_df = stream_gdf[[stream_col, 'ds_id']]
            stream_link = dict(
                (i, i) if j == -1 else (i, j) for i, j in zip(stream_df[stream_col], stream_df['ds_id'])
            )
            # upstream to downstream total connectivity
            us2ds_link: dict[float, list[float]] = {
                i: list() for i in stream_link.keys()
            }
            for i in stream_link:
                fix_i = i
                while True:
                    if stream_link[i] in us2ds_link[fix_i]:
                        break
                    else:
                        us2ds_link[fix_i].append(stream_link[i])
                        i = stream_link[i]
            # saving upstream to downstream connectivity
            with open(json_file, 'w') as output_us2ds:
                json.dump(us2ds_link, output_us2ds)

        return us2ds_link

    def connectivity_downstream_to_upstream(
        self,
        stream_file: str,
        stream_col: str,
        json_file: str
    ) -> dict[float, list[list[float]]]:

        '''
        Identifies the connected upstream structure for each segment
        in a stream network shapefile, tracing all upstream paths until
        reaching a headwater segment.

        Parameters
        ----------
        stream_file : str
            Path to the input stream shapefile.

        stream_col : str
            Column name in the stream shapefile containing
            a unique identifier for each stream segment.

        json_file : str
            Path to save the output JSON file
            representing downstream to upstream connections.

        Returns
        -------
        dict
            A dictionary where each key is a stream segment identifier,
            and the corresponding value is a list of lists, each representing
            a unique upstream path ending at a headwater segment.
        '''

        # check LineString geometry type
        if 'LineString' not in Core().shapefile_geometry_type(stream_file):
            raise Exception('Input shapefile must have geometries of type LineString.')

        # temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # connectivity to downstream segment identifiers
            stream_gdf = self.connectivity_adjacent_downstream_segment(
                input_file=stream_file,
                stream_col=stream_col,
                output_file=os.path.join(tmp_dir, 'stream_downstream_id.shp')
            )
            stream_df = stream_gdf[[stream_col, 'ds_id']]
            stream_link = {
                i: j for i, j in zip(stream_df[stream_col], stream_df['ds_id'])
            }
            # downstream to upstream total connectivity
            ds2us_link: dict[float, list[list[float]]] = {
                i: list() for i in stream_link.keys()
            }
            for i in stream_link.keys():
                if i not in stream_link.values():
                    pass
                else:
                    i_connect = [i]
                    while True:
                        i_upstream = list(
                            filter(
                                lambda x: stream_link[x] in i_connect, stream_link
                            )
                        )
                        if len(i_upstream) == 0:
                            break
                        else:
                            ds2us_link[i].append(i_upstream)
                            i_connect = ds2us_link[i][-1]
            # saving downstream to upstream connectivitye
            with open(json_file, 'w') as output_ds2us:
                json.dump(ds2us_link, output_ds2us)

        return ds2us_link

    def connectivity_to_all_upstream_segments(
        self,
        stream_file: str,
        stream_col: str,
        csv_file: str,
        link_col: str = 'us_id',
        unlinked_id: int = -1
    ) -> pandas.DataFrame:

        '''
        Converts the dictionary output from the
        :meth:`GeoAnalyze.Stream.conncetivity_downstream_to_upstream` method
        into a DataFrame with two columns: `stream_col` and `link_col`,
        representing stream segment identifiers (which may appear multiple times)
        and their corresponding consecutively connected upstream segments
        ending at a headwater segment, respectively.

        Parameters
        ----------
        stream_file : str
            Path to the input stream shapefile.

        stream_col : str
            Column name in the stream shapefile containing
            a unique identifier for each stream segment.

        csv_file : str
            Path to save the output JSON file
            representing downstream to upstream connections.

        link_col : str, optional
            Name of the column to store the connected
            upstream segment identifiers. Default is 'us_id'.

        unlinked_id : int, optional
            Value to assign when a upstream segment identifier is not found. Default is -1.

        Returns
        -------
        DataFrame
            A DataFrame with two columns `stream_col` and `link_col`.
            The `stream_col` contains stream segment identifiers (which may appear multiple times),
            and the `link_col` contains their corresponding consecutively connected
            upstream segment identifiers ending at a headwater segment.
        '''

        # check LineString geometry type
        if 'LineString' not in Core().shapefile_geometry_type(stream_file):
            raise Exception('Input shapefile must have geometries of type LineString.')

        # temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # downstream to upstream total connectivity
            ds2us_link = self.connectivity_downstream_to_upstream(
                stream_file=stream_file,
                stream_col=stream_col,
                json_file=os.path.join(tmp_dir, 'stream_ds2us.json')
            )
            # adjacent upstream segment
            up_link = []
            for key, value in ds2us_link.items():
                value_list = [j for i in value for j in i]
                if len(value_list) == 0:
                    up_link.append({stream_col: key, link_col: unlinked_id})
                else:
                    for ul in value_list:
                        up_link.append({stream_col: key, link_col: ul})
            # converting list to DataFrame
            ul_df = pandas.DataFrame(up_link)
            ul_df = ul_df.sort_values(
                by=[stream_col, link_col],
                ignore_index=True
            )
            # saving adjacent upstream connectivity
            ul_df.to_csv(
                path_or_buf=csv_file,
                sep='\t',
                index=False
            )

        return ul_df

    def connectivity_remove_to_headwater(
        self,
        input_file: str,
        stream_col: str,
        remove_segments: list[float],
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Removes targeted stream segments and all their upstream connections
        up to headwaters in a stream network shapefile.

        Parameters
        ----------
        input_file : str
            Path to the input stream shapefile.

        stream_col : str
            Column name in the stream shapefile containing
            a unique identifier for each stream segment.

        remove_segments : list
            A list of stream segment identifiers to remove, along with
            all their upstream connections up to the headwaters.

        output_file : str
            Path to save the output stream shapefile after removing the
            specified segments and their upstream connections.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame representing the updated stream network after
            removing the targeted stream segments and their upstream paths.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # check LineString geometry type
        if 'LineString' not in Core().shapefile_geometry_type(input_file):
            raise Exception('Input shapefile must have geometries of type LineString.')

        # stream geodataframe
        stream_gdf = geopandas.read_file(input_file)

        if len(remove_segments) == 0:
            pass
        else:
            # temporary directory
            with tempfile.TemporaryDirectory() as tmp_dir:
                # downstream to upstream total connectivity
                ds2us_link = self.connectivity_downstream_to_upstream(
                    stream_file=input_file,
                    stream_col=stream_col,
                    json_file=os.path.join(tmp_dir, 'stream_ds2us.json')
                )
                # collecting targeted remove ids and their upstream connectivity
                remove_ids: list[float] = []
                for i in remove_segments:
                    remove_ids = remove_ids + [i]
                    if len(ds2us_link[i]) == 0:
                        pass
                    else:
                        i_ul = [k for j in ds2us_link[i] for k in j]
                        remove_ids = remove_ids + i_ul
                # saving output GeoDataFrame
                stream_gdf = stream_gdf[~stream_gdf[stream_col].isin(set(remove_ids))].reset_index(drop=True)
                stream_gdf.to_file(output_file)

        return stream_gdf

    def connectivity_merge_of_split_segments(
        self,
        input_file: str,
        stream_col: str,
        output_file: str,
        json_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Merges split segments in the stream network, if any, either between
        two junction points or from a junction point upstream until a headwater occurs.
        The merged segment is assigned the identifier of the most downstream segment
        among those being merged.

        Parameters
        ----------
        input_file : str
            Path to the input stream shapefile.

        stream_col : str
            Column name in the stream shapefile containing
            a unique identifier for each stream segment.

        output_file : str
            Path to save the output stream shapefile
            with updated downstream connectivity information.

        json_file : str
            Path to save the output JSON file representing the merge information
            of stream segments. For example, {5: [4, 39, 38, 2]} indicates that
            stream segment 5 is the result of merging segments 4, 39, 38, and 2,
            which are consecutively connected from downstream to upstream until
            a junction point is reached or no upstream segment exists.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame where each merged segment is represented by the most
            downstream segment identifier, absorbing all connected upstream segments
            either between junction points or from a junction point to a headwater.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # check LineString geometry type
        if 'LineString' not in Core().shapefile_geometry_type(input_file):
            raise Exception('Input shapefile must have geometries of type LineString.')

        # temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # connectivity to downstream segment identifiers
            stream_gdf = self.connectivity_adjacent_downstream_segment(
                input_file=input_file,
                stream_col=stream_col,
                output_file=os.path.join(tmp_dir, 'stream_downstream_id.shp')
            )
            slm_gdf = stream_gdf[[stream_col, 'ds_id', 'geometry']]
            stream_link = dict(
                zip(slm_gdf[stream_col], slm_gdf['ds_id'])
            )
            # upstream link until either junction point or headwater occurs
            upstream_link: dict[float, list[list[float]]] = {
                i: list() for i in slm_gdf[stream_col]
            }
            for i in stream_link.keys():
                if i not in stream_link.values():
                    pass
                else:
                    i_connect = [i]
                    while True:
                        i_upstream = list(
                            filter(
                                lambda x: stream_link[x] in i_connect, stream_link
                            )
                        )
                        if len(i_upstream) == 0:
                            break
                        elif len(i_upstream) > 1:
                            break
                        else:
                            upstream_link[i].append(i_upstream)
                            i_connect = upstream_link[i][-1]
            # non-empty upstream link until either junction point or headwater occurs
            jh_link = {
                i: j for i, j in upstream_link.items() if len(j) > 0
            }
            # end segment identifiers until either junction point or headwater occurs
            jh_ids = set([jh_link[i][-1][0] for i in jh_link])
            # select most downstream segments for merged links
            ds_link = {}
            for i in jh_ids:
                i_jh = list(
                    filter(
                        lambda x: jh_link[x][-1][0] == i, jh_link.keys()
                    )
                )
                i_length = list(
                    map(
                        lambda x: len(jh_link[x]), i_jh
                    )
                )
                i_select = i_jh[i_length.index(max(i_length))]
                ds_link[i_select] = jh_link[i_select]
            # dictionary of merged link
            merged_link: dict[float, list[float]] = dict(
                zip(
                    ds_link.keys(), map(lambda x: [i[0] for i in ds_link[x]], ds_link.keys())
                )
            )
            # saving merged information of split segments in json file
            with open(json_file, 'w') as output_merged:
                json.dump(merged_link, output_merged)

            # saving output GeoDataFrame
            slm_gdf = slm_gdf.drop(columns=['ds_id'])
            reverse_merge = {
                val: key for key, values in merged_link.items() for val in values
            }
            slm_gdf['m_id'] = slm_gdf[stream_col].apply(
                lambda x: reverse_merge.get(x, x)
            )
            slm_gdf = slm_gdf.dissolve(by=['m_id']).reset_index()
            slm_gdf['geometry'] = slm_gdf['geometry'].apply(
                lambda x: shapely.line_merge(x)
            )
            slm_gdf = slm_gdf.drop(columns=[stream_col])
            slm_gdf = slm_gdf.rename(
                columns={'m_id': stream_col}
            )
            slm_gdf.to_file(output_file)

        return slm_gdf

    def point_junctions(
        self,
        input_file: str,
        stream_col: str,
        output_file: str,
        junction_col: str = 'j_id'
    ) -> geopandas.GeoDataFrame:

        '''
        Identifies junction points in the stream path and maps stream segment identifiers
        whose most downstream points coincide with these junction points. Additionally,
        a new column 'j_id' will be added to assign a unique identifier to each junction point, starting from 1.

        Parameters
        ----------
        input_file : str
            Path to the input stream shapefile.

        stream_col : str
            Column name in the stream shapefile containing a unique identifier for each stream segment.

        output_file : str
            Path to save the output junction point shapefile.

        junction_col : str, optional
            Name of the column to store the connected downstream segment identifiers. Default is 'j_id'.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame of junction points with their corresponding stream segment identifiers.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # check LineString geometry type
        if 'LineString' not in Core().shapefile_geometry_type(input_file):
            raise Exception('Input shapefile must have geometries of type LineString.')

        # stream geodataframe
        stream_gdf = geopandas.read_file(input_file)

        # downstream endpoint GeoDataFrame
        downstream_points = stream_gdf.geometry.apply(lambda x: shapely.Point(x.coords[-1]))
        downstream_gdf = geopandas.GeoDataFrame(
            {
                stream_col: stream_gdf[stream_col],
                'geometry': downstream_points
            },
            crs=stream_gdf.crs
        )

        # junction point GeoDataFrame
        downstream_counts = downstream_gdf['geometry'].value_counts()
        junction_points = downstream_counts[downstream_counts > 1].index
        junction_gdf = downstream_gdf[downstream_gdf['geometry'].isin(junction_points.tolist())]

        # get the segment identfiers of junction points
        junction_groups = junction_gdf.groupby('geometry')[stream_col].apply(lambda x: x.tolist())

        # saving output GeoDataFrame
        output_gdf = geopandas.GeoDataFrame(
            data={
                junction_col: range(1, len(junction_groups) + 1),
                junction_groups.name: junction_groups.values
            },
            geometry=list(junction_groups.index),
            crs=stream_gdf.crs
        )
        output_gdf.to_file(output_file)

        return output_gdf

    def point_segment_subbasin_drainage(
        self,
        input_file: str,
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Generates a GeoDataFrame of subbasin drainage points for flow segments in the stream path.
        For each flow segment, the most downstream point is selected unless it is a junction point,
        in which case the second most downstream point is used.

        Parameters
        ----------
        input_file : str
            Path to the input stream shapefile.

        output_file : str
            Path to save the output pour point shapefile.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the subbasin drainage points.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # check LineString geometry type
        if 'LineString' not in Core().shapefile_geometry_type(input_file):
            raise Exception('Input shapefile must have geometries of type LineString.')

        # stream GeoDataFrame
        stream_gdf = geopandas.read_file(input_file)

        # junction points
        downstream_points = stream_gdf.geometry.apply(lambda x: shapely.Point(x.coords[-1]))
        point_count = downstream_points.value_counts()
        junction_points = point_count[point_count > 1].index.to_list()

        # subbasin drainage points
        pour_gdf = stream_gdf.copy()
        pour_gdf['junction'] = pour_gdf['geometry'].apply(
            lambda x: 'YES' if shapely.Point(*x.coords[-1]) in junction_points else 'NO'
        )
        pour_gdf['pour_coords'] = pour_gdf.apply(
            lambda row: row.geometry.coords[-2] if row['junction'] == 'YES' else row.geometry.coords[-1],
            axis=1
        )
        pour_gdf['geometry'] = pour_gdf.apply(
            lambda row: shapely.Point(*row['pour_coords']),
            axis=1
        )
        pour_gdf = pour_gdf.drop(columns=['pour_coords', 'junction'])

        # saving output GeoDataFrame
        pour_gdf.to_file(output_file)

        return pour_gdf

    def point_main_outlets(
        self,
        input_file: str,
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Identifies the main outlet points of a stream path and
        saves the resulting GeoDataFrame to the specified shapefile path.

        Parameters
        ----------
        input_file : str
            Path to the input stream shapefile.

        output_file : str
            Path to save the output outlet point shapefile.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the main outlet points along
            with their associated flow segment identifiers.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # check LineString geometry type
        if 'LineString' not in Core().shapefile_geometry_type(input_file):
            raise Exception('Input shapefile must have geometries of type LineString.')

        # stream geodataframe
        stream_gdf = geopandas.read_file(input_file)

        # outlet point GeoDataFrame
        downstream_gdf = stream_gdf.copy()
        downstream_gdf['geometry'] = stream_gdf.geometry.apply(lambda x: shapely.Point(*x.coords[-1]))
        downstream_counts = downstream_gdf['geometry'].value_counts()
        outlet_points = downstream_counts[downstream_counts == 1].index
        outlet_gdf = downstream_gdf[downstream_gdf['geometry'].isin(outlet_points.tolist())]
        outlet_gdf = outlet_gdf.reset_index(drop=True)

        # saving output GeoDataFrame
        outlet_gdf.to_file(output_file)

        return outlet_gdf

    def point_headwaters(
        self,
        input_file: str,
        stream_col: str,
        output_file: str,
    ) -> geopandas.GeoDataFrame:

        '''
        Identifies headwater points in the stream network. A headwater point
        is defined as the starting point of a stream segment with no upstream connections.

        Parameters
        ----------
        input_file : str
            Path to the input stream shapefile.

        output_file : str
            Path to save the output shapefile containing identified headwater points.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the geometries and attributes of headwater points.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # check LineString geometry type
        if 'LineString' not in Core().shapefile_geometry_type(input_file):
            raise Exception('Input shapefile must have geometries of type LineString.')

        # temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # connectivity to downstream segment identifiers
            stream_gdf = self.connectivity_adjacent_downstream_segment(
                input_file=input_file,
                stream_col=stream_col,
                output_file=os.path.join(tmp_dir, 'stream_downstream_id.shp')
            )
            # predict headwater segments
            hw_ids = [
                i for i in stream_gdf[stream_col] if i not in stream_gdf['ds_id'].tolist()
            ]
            hw_gdf = stream_gdf[stream_gdf[stream_col].isin(hw_ids)].reset_index(drop=True)
            hw_gdf.geometry = hw_gdf.geometry.apply(lambda x: shapely.Point(x.coords[0]))
            # saving output GeoDataFrame
            hw_gdf.to_file(output_file)

        return hw_gdf

    def order_strahler(
        self,
        input_file: str,
        stream_col: str,
        output_file: str,
        order_col: str = 'strahler'
    ) -> geopandas.GeoDataFrame:

        '''
        Computes the Strahler order for each segment
        in a stream network shapefile.

        Parameters
        ----------
        input_file : str
            Path to the input stream shapefile.

        stream_col : str
            Column name in the stream shapefile containing
            a unique identifier for each stream segment.

        output_file : str
            Path to save the output stream shapefile
            with Strahler stream order information.

        order_col : str, optional
            Name of the column to store the Strahler order
            of stream segments. Default is 'strahler'.

        Returns
        -------
        GeoDataFrame
             A GeoDataFrame representing the input shapefile,
             enhanced with an additional column that indicates
             the Strahler stream order for each stream segment.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # check LineString geometry type
        if 'LineString' not in Core().shapefile_geometry_type(input_file):
            raise Exception('Input shapefile must have geometries of type LineString.')

        # temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # stream GeoDataFrame
            stream_gdf = geopandas.read_file(input_file)
            # connectivity to upstream segment identifiers
            ul_df = self.connectivity_adjacent_upstream_segment(
                stream_file=input_file,
                stream_col=stream_col,
                csv_file=os.path.join(tmp_dir, 'upstream_id.csv'),
            )
            ul_dict = {
                key: df['us_id'].tolist() for key, df in ul_df.groupby(stream_col)
            }
            ul_ids = {
                key: ([] if value == [-1] else value) for key, value in ul_dict.items()
            }
            ul_count = {
                key: len(value) for key, value in ul_ids.items()
            }
            # compute Strahler order
            strahler_order = ul_count.copy()
            for i in stream_gdf[stream_col]:
                # if no upstream link
                if ul_count[i] == 0:
                    strahler_order[i] = 1
                else:
                    # update strahler_order order if upstream link is present
                    update_order = 0
                    update_count = 0
                    for j in ul_ids[i]:
                        if strahler_order[j] > update_order:
                            update_order = strahler_order[j]
                            update_count = 1
                        elif strahler_order[j] == update_order:
                            update_count = update_count + 1
                        else:
                            pass
                    if update_count > 1:
                        strahler_order[i] = update_order + 1
                    else:
                        strahler_order[i] = update_order
            # insert Strahler order into the stream GeoDataFrame
            stream_gdf[order_col] = stream_gdf[stream_col].apply(
                lambda x: strahler_order.get(x)
            )
            # saving output GeoDataFrame
            stream_gdf.to_file(output_file)

        return stream_gdf

    def order_shreve(
        self,
        input_file: str,
        stream_col: str,
        output_file: str,
        order_col: str = 'shreve'
    ) -> geopandas.GeoDataFrame:

        '''
        Computes the Shreve order for each segment
        in a stream network shapefile.

        Parameters
        ----------
        input_file : str
            Path to the input stream shapefile.

        stream_col : str
            Column name in the stream shapefile containing
            a unique identifier for each stream segment.

        output_file : str
            Path to save the output stream shapefile
            with Shreve stream order information.

        order_col : str, optional
            Name of the column to store the Shreve order
            of stream segments. Default is 'shreve'.

        Returns
        -------
        GeoDataFrame
             A GeoDataFrame representing the input shapefile,
             enhanced with an additional column that indicates
             the Shreve stream order for each stream segment.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # check LineString geometry type
        if 'LineString' not in Core().shapefile_geometry_type(input_file):
            raise Exception('Input shapefile must have geometries of type LineString.')

        # temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # stream GeoDataFrame
            stream_gdf = geopandas.read_file(input_file)
            # connectivity to upstream segment identifiers
            ul_df = self.connectivity_adjacent_upstream_segment(
                stream_file=input_file,
                stream_col=stream_col,
                csv_file=os.path.join(tmp_dir, 'upstream_id.csv'),
            )
            ul_dict = {
                key: df['us_id'].tolist() for key, df in ul_df.groupby(stream_col)
            }
            ul_ids = {
                key: ([] if value == [-1] else value) for key, value in ul_dict.items()
            }
            # initialize all segments with 0 Shreve order
            shreve_order = {
                i: 0 for i in stream_gdf[stream_col]
            }
            # find segments with no upstream link and set Shreve order to 1
            for i in shreve_order:
                if len(ul_ids[i]) == 0:
                    shreve_order[i] = 1
            # iterate until Shreve order of all segments are updated
            stream_ids = stream_gdf[stream_col].tolist()
            while len(stream_ids) > 0:
                for i in stream_ids:
                    # get upstream link of stream segement i
                    i_ul = ul_ids[i]
                    # check if all upstream segments have Shreve order greater than 0
                    if all(shreve_order[j] > 0 for j in i_ul):
                        # no change of Shreve order if upstream link is not found
                        if len(i_ul) == 0:
                            pass
                        # add Shreve orders of upstream links
                        else:
                            shreve_order[i] = sum(shreve_order[j] for j in i_ul)
                        stream_ids.remove(i)
            # insert Shreve order into the stream GeoDataFrame
            stream_gdf[order_col] = stream_gdf[stream_col].apply(
                lambda x: shreve_order.get(x)
            )
            # saving output GeoDataFrame
            stream_gdf.to_file(output_file)

        return stream_gdf

    def box_touch_selected_segment(
        self,
        input_file: str,
        column_name: str,
        column_value: typing.Any,
        box_length: float,
        output_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Creates a square box polygon that touches a specified segment
        in the stream path at a randomly chosen point along the segment.

        Parameters
        ----------
        input_file : str
            Path to the input stream shapefile.

        column_name : str
            Name of the column used for selecting the target stream segment.

        column_value : Any
            Value in the specified column that identifies the target stream segment.

        box_length : float
            Length of each side of the square box polygon.

        output_file : str
            Path to save the output box polygon shapefile.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the created box polygon, which
            touches the specified stream segment at a random point.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # input line segment
        gdf = geopandas.read_file(input_file)
        line = gdf[gdf[column_name].isin([column_value])].geometry.iloc[0]

        # line coords
        line_coords = line.coords[:] if isinstance(line, shapely.LineString) else [c for ls in line.geoms for c in ls.coords[:]]

        while True:
            # choose points
            point_index = random.randint(
                a=0,
                b=len(line_coords) - 1
            )
            point = shapely.Point(line.coords[point_index])
            # create box
            box = shapely.box(
                xmin=point.x,
                ymin=point.y,
                xmax=point.x + box_length,
                ymax=point.y + box_length
            )
            # random angle between 0 and 360
            rotate_box = shapely.affinity.rotate(
                geom=box,
                angle=random.randint(0, 360),
                origin=point
            )
            check_touch = line.touches(rotate_box) and not line.crosses(rotate_box)
            if check_touch is True:
                break

        # saving output GeoDataFrame
        box_gdf = geopandas.GeoDataFrame(
            geometry=[rotate_box],
            crs=gdf.crs
        )
        box_gdf.to_file(output_file)

        return box_gdf

    def box_touch_selected_segment_at_endpoint(
        self,
        input_file: str,
        column_name: str,
        column_value: typing.Any,
        box_length: float,
        output_file: str,
        upstream_point: bool = True
    ) -> geopandas.GeoDataFrame:

        '''
        Creates a square box polygon that touches an endpoint
        of a specified segment in the input stream path.

        Parameters
        ----------
        input_file : str
            Path to the input stream shapefile.

        column_name : str
            Name of the column used for selecting the target stream segment.

        column_value : Any
            Value in the specified column that identifies the target stream segment.

        box_length : float
            Length of each side of the square box polygon.

        output_file : str
            Path to save the output box polygon shapefile.

        upstream_point : bool, optional
            If True, the box is positioned to pass through the upstream endpoint
            of the segment; if False, it passes through the downstream endpoint. Default is True.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the box polygon, which touches an endpoint of
            the specified segment in the input stream path.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # input line segement
        gdf = geopandas.read_file(input_file)
        line = gdf[gdf[column_name].isin([column_value])].geometry.iloc[0]

        # get point
        point_coords = line.coords[0] if upstream_point is True else line.coords[-1]
        point = shapely.Point(*point_coords)

        # create box
        box = shapely.box(
            xmin=point.x,
            ymin=point.y,
            xmax=point.x + box_length,
            ymax=point.y + box_length
        )

        # check whether the box touches the line; otherwise rotate
        while True:
            check_touch = line.touches(box) and not line.crosses(box)
            if check_touch:
                break
            else:
                box = shapely.affinity.rotate(
                    geom=box,
                    angle=random.randint(0, 360),
                    origin=point
                )

        # saving output GeoDataFrame
        box_gdf = geopandas.GeoDataFrame(
            geometry=[box],
            crs=gdf.crs
        )
        box_gdf.to_file(output_file)

        return box_gdf

    def box_cross_selected_segment_at_endpoint(
        self,
        input_file: str,
        column_name: str,
        column_value: typing.Any,
        box_length: float,
        output_file: str,
        downstream_point: bool = True
    ) -> geopandas.GeoDataFrame:

        '''
        Creates a square box polygon that crosses a specified segment
        in the stream path and passes through an endpoint of the segment.

        Parameters
        ----------
        input_file : str
            Path to the input stream shapefile.

        column_name : str
            Name of the column used for selecting the target stream segment.

        column_value : Any
            Value in the specified column that identifies the target stream segment.

        box_length : float
            Length of each side of the square box polygon.

        output_file : str
            Path to save the output box polygon shapefile.

        downstream_point : bool, optional
            If True, the box is positioned to pass through the downstream endpoint
            of the segment; if False, it passes through the upstream endpoint. Default is True.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the box polygon, which crosses the
            specified stream segment and passes through an endpoint of the segment.
        '''

        # check validity of output file path
        check_file = Core().is_valid_ogr_driver(output_file)
        if check_file is False:
            raise Exception('Could not retrieve driver from the file path.')

        # input line segement
        gdf = geopandas.read_file(input_file)
        line = gdf[gdf[column_name].isin([column_value])].geometry.iloc[0]

        # get point
        point_coords = line.coords[-1] if downstream_point is True else line.coords[0]
        point = shapely.Point(*point_coords)

        # create box
        box = shapely.box(
            xmin=point.x,
            ymin=point.y,
            xmax=point.x + box_length,
            ymax=point.y + box_length
        )

        # check whether the box crosses the line; otherwise rotate
        while True:
            if line.crosses(box):
                break
            else:
                box = shapely.affinity.rotate(
                    geom=box,
                    angle=random.randint(0, 360),
                    origin=point
                )

        # saving output GeoDataFrame
        box_gdf = geopandas.GeoDataFrame(
            geometry=[box],
            crs=gdf.crs
        )
        box_gdf.to_file(output_file)

        return box_gdf
