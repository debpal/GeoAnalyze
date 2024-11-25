import geopandas
import shapely
import random
import typing
from .core import Core


class Stream:

    '''
    Provides functionality for stream path operations.
    '''

    def check_flow_direction(
        self,
        stream_file: str
    ) -> bool:

        '''
        Checks the flow direction from upstream to downstream
        by comparing the number of segments in the flow path
        to the number of their most upstream points.

        Parameters
        ----------
        stream_file : str
            Shapefile path containing the stream data.

        Returns
        -------
        bool
            True if the number of flow path segments aligns with
            the number of upstream points, indicating correct
            flow direction; otherwise, False.
        '''

        # input stream GeoDataFrame
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

    def reverse_flow_direction(
        self,
        input_stream: str,
        output_stream: str
    ) -> geopandas.GeoDataFrame:

        '''
        Reverses the coordinate order for each segment in the input flow path,
        ensuring that the starting point of each segment becomes its most upstream point.

        Parameters
        ----------
        input_stream : str
            Shapefile path containing the stream data.

        output_stream : str or GeoDataFrame
            File path to save the output GeoDataFrame.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame with each stream segment’s coordinates reversed.
        '''

        # input stream GeoDataFrame
        gdf = geopandas.read_file(input_stream)
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

        # saving GeoDataFrame
        gdf.to_file(output_stream)

        return output

    def downstream_link(
        self,
        input_stream: str,
        stream_col: str,
        link_col: str,
        output_stream: str
    ) -> geopandas.GeoDataFrame:

        '''
        Identifies downstream link identifiers for all flow segments
        and saves the updated GeoDataFrame to the specified shapefile path.

        Parameters
        ----------
        input_stream : str
            Shapefile path containing line segments representing the stream path.

        stream_col : str
            Column name in the stream shapefile containing a unique identifier for each stream segment.

        link_col : str
            Column name where the downstream link identifiers of flow segments will be stored.

        output_stream : str
            Shapefile path to save the output GeoDataFrame of stream path.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame with an additional column for downstream link identifiers of flow segments.
        '''

        # stream geodataframe
        stream_gdf = geopandas.read_file(input_stream)

        # endpoints of flow segments
        upstream_points = {
            idx: line.coords[0] for idx, line in zip(stream_gdf['LINKNO'], stream_gdf.geometry)
        }
        downstream_points = {
            idx: line.coords[-1] for idx, line in zip(stream_gdf['LINKNO'], stream_gdf.geometry)
        }

        # link between flow segments
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
                downstream_link[dp_id] = -1

        # update stream GeoDataFrame with downstream link and save
        stream_gdf[link_col] = downstream_link.values()
        stream_gdf.to_file(output_stream)

        return stream_gdf

    def junction_points(
        self,
        stream_file: str,
        stream_col: str,
        junction_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Identifies junction points in the stream path and maps stream segment identifiers
        whose most downstream points coincide with these junction points. Additionally,
        a new column 'jid' will be added to assign a unique identifier to each junction point, starting from 1.

        Parameters
        ----------
        stream_file : str
            Shapefile path containing line segments representing the stream path.

        stream_col : str
            Column name in the stream shapefile containing a unique identifier for each stream segment.

        junction_file : str
            Shapefile path to save the output GeoDataFrame of junction points.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame of junction points with their corresponding stream segment identifiers.
        '''

        # stream geodataframe
        stream_gdf = geopandas.read_file(stream_file)

        # downstream endpoint GeoDataFrame
        downstream_points = stream_gdf.geometry.apply(lambda x: shapely.Point(*x.coords[-1]))
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

        # save the output GeoDataFrame
        output_gdf = geopandas.GeoDataFrame(
            data={
                'jid': range(1, len(junction_groups) + 1),
                junction_groups.name: junction_groups.values
            },
            geometry=list(junction_groups.index),
            crs=stream_gdf.crs
        )
        output_gdf.to_file(junction_file)

        return output_gdf

    def main_outlets(
        self,
        stream_file: str,
        stream_col: str,
        outlet_file: str
    ) -> geopandas.GeoDataFrame:

        '''
        Identifies the main outlet points of a stream path and
        saves the resulting GeoDataFrame to the specified shapefile path.

        Parameters
        ----------
        stream_file : str
            Shapefile path containing line segments representing the stream path.

        stream_col : str
            Column name in the stream shapefile containing a unique identifier for each stream segment.

        outlet_file : str
            Shapefile path to save the output GeoDataFrame of main outlet points.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the main outlet points along
            with their associated flow segment identifiers.
        '''

        # stream geodataframe
        stream_gdf = geopandas.read_file(stream_file)

        # downstream endpoint GeoDataFrame
        downstream_points = stream_gdf.geometry.apply(lambda x: shapely.Point(*x.coords[-1]))
        downstream_gdf = geopandas.GeoDataFrame(
            {
                stream_col: stream_gdf[stream_col],
                'geometry': downstream_points
            },
            crs=stream_gdf.crs
        )

        # outlet point GeoDataFrame
        downstream_counts = downstream_gdf['geometry'].value_counts()
        outlet_points = downstream_counts[downstream_counts == 1].index
        outlet_gdf = downstream_gdf[downstream_gdf['geometry'].isin(outlet_points.tolist())]
        outlet_gdf = outlet_gdf.reset_index(drop=True)
        outlet_gdf.insert(
            loc=0,
            column='moid',
            value=range(1, len(outlet_gdf) + 1)
        )

        # save the outlet point GeoDataFrame
        outlet_gdf.to_file(outlet_file)

        return outlet_gdf

    def create_box_touching_selected_segment(
        self,
        input_stream: str,
        column_name: str,
        column_value: typing.Any,
        box_length: float,
        output_box: str
    ) -> geopandas.GeoDataFrame:

        '''
        Creates a square box polygon that touches a specified stream segment
        in the input flow path at a randomly chosen point along the segment.

        Parameters
        ----------
        input_stream : str
            Shapefile path containing the stream data.

        column_name : str
            Name of the column used for selecting the target stream segment.

        column_value : Any
            Value in the specified column that identifies the target stream segment.

        box_length : float
            Length of each side of the square box polygon.

        output_box : str
            Shapefile path to save the output GeoDataFrame containing the box polygon.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the created box polygon, which
            touches the specified stream segment at a random point.
        '''

        # input line segment
        gdf = geopandas.read_file(input_stream)
        line = gdf[gdf[column_name].isin([column_value])].geometry.iloc[0]

        # line coords
        if isinstance(line, shapely.LineString):
            line_coords = line.coords[:]
        else:
            line_coords = []
            for line_split in line.geoms:
                line_coords.extend(line_split.coords[:])

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
            else:
                pass

        # saving box geodataframe
        box_gdf = geopandas.GeoDataFrame(
            geometry=[rotate_box],
            crs=gdf.crs
        )
        box_gdf.to_file(output_box)

        return box_gdf

    def create_box_crosses_segment_at_endpoint(
        self,
        input_stream: str,
        column_name: str,
        column_value: typing.Any,
        box_length: float,
        output_box: str,
        downstream_point: bool = True
    ) -> geopandas.GeoDataFrame:

        '''
        Creates a square box polygon that crosses a specified stream segment
        in the input flow path and passes through an endpoint of the segment.

        Parameters
        ----------
        input_stream : str
            Shapefile path containing the stream data.

        column_name : str
            Name of the column used for selecting the target stream segment.

        column_value : Any
            Value in the specified column that identifies the target stream segment.

        box_length : float
            Length of each side of the square box polygon.

        output_box : str
            Shapefile path to save the output GeoDataFrame containing box polygon.

        downstream_point : bool, optional
            If True, the box is positioned to pass through the downstream endpoint
            of the segment; if False, it passes through the upstream endpoint. Default is True.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the box polygon, which crosses the
            specified stream segment and passes through an endpoint of the segment.
        '''

        # input line segement
        gdf = geopandas.read_file(input_stream)
        line = gdf[gdf[column_name].isin([column_value])].geometry.iloc[0]

        # get point
        point_coords = line.coords[-1] if downstream_point is True else line.coords[0]
        point = shapely.Point(*point_coords)

        # create box
        box = shapely.box(
            xmin=point.x,
            ymin=point.y,
            xmax=point.x + box_length,
            ymax=point.y + box_length,
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

        # saving box geodataframe
        box_gdf = geopandas.GeoDataFrame(
            geometry=[box],
            crs=gdf.crs
        )
        box_gdf.to_file(output_box)

        return box_gdf

    def create_box_touch_segment_at_endpoint(
        self,
        input_stream: str,
        column_name: str,
        column_value: typing.Any,
        box_length: float,
        output_box: str,
        upstream_point: bool = True
    ) -> geopandas.GeoDataFrame:

        '''
        Creates a square box polygon that touches an endpoint
        of a specified segment in the input stream path.

        Parameters
        ----------
        input_stream : str
            Shapefile path containing the stream data.

        column_name : str
            Name of the column used for selecting the target stream segment.

        column_value : Any
            Value in the specified column that identifies the target stream segment.

        box_length : float
            Length of each side of the square box polygon.

        output_box : str
            Shapefile path to save the output GeoDataFrame containing the box polygon.

        upstream_point : bool, optional
            If True, the box is positioned to pass through the upstream endpoint
            of the segment; if False, it passes through the downstream endpoint. Default is True.

        Returns
        -------
        GeoDataFrame
            A GeoDataFrame containing the box polygon, which touches an endpoint of
            the specified segment in the input stream path.
        '''

        # input line segement
        gdf = geopandas.read_file(input_stream)
        line = gdf[gdf[column_name].isin([column_value])].geometry.iloc[0]

        # get point
        point_coords = line.coords[0] if upstream_point is True else line.coords[-1]
        point = shapely.Point(*point_coords)

        # create box
        box = shapely.box(
            xmin=point.x,
            ymin=point.y,
            xmax=point.x + box_length,
            ymax=point.y + box_length,
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

        # saving box geodataframe
        box_gdf = geopandas.GeoDataFrame(
            geometry=[box],
            crs=gdf.crs
        )
        box_gdf.to_file(output_box)

        return box_gdf
