import matplotlib
import matplotlib.pyplot
import rasterio
import geopandas
from .core import Core


class Visual:

    '''
    Provides functions to plot of raster and vector data.
    '''

    def quickview_raster(
        self,
        raster_file: str,
        figure_file: str,
        colormap: str = 'terrain',
        fig_width: float = 6,
        fig_height: float = 6,
        log_scale: bool = False,
        gui_window: bool = True
    ) -> matplotlib.figure.Figure:

        '''
        Generates a figure for a quick view of a raster array.

        Parameters
        ----------
        raster_file : str
            Path to the input raster file.

        figure_file : str
            Path to the output figure file.

        colormap : str, optional
            Registered colormap name in the `matplotlib` Python package.
            Default is 'terrain'.

        fig_width : float, optional
            Width of the figure in inches. Default is 6 inches.

        fig_height : float, optional
            Height of the figure in inches. Default is 6 inches.

        log_scale : bool, optional
            If True, display the colormap in logarithmic scale. Default is False.

        gui_window : bool, optional
            If True, open a graphical user interface window of the plot. Default is True.

        Returns
        -------
        Figure
            A figure displaying the plot of the input raster array.
        '''

        # check validity of input figure file path
        check_file = Core().is_valid_figure_extension(figure_file)
        if check_file is False:
            raise Exception('Input figure file extension is not supported.')

        # raster characteristics
        with rasterio.open(raster_file) as input_raster:
            raster_profile = input_raster.profile
            raster_extent = tuple(
                getattr(input_raster.bounds, i) for i in ('left', 'right', 'bottom', 'top')
            )
            raster_array = input_raster.read(1).astype('float32')
            mask_array = raster_array != raster_profile['nodata']
            raster_min = raster_array[mask_array].min()
            raster_max = raster_array[mask_array].max()
            raster_array[~mask_array] = float('nan')

        # figure setting
        figure = matplotlib.pyplot.figure(
            figsize=(fig_width, fig_height)
        )
        subplot = figure.subplots(1, 1)

        # raster plotting
        norm = matplotlib.colors.LogNorm(1, raster_max) if log_scale else matplotlib.colors.Normalize(raster_min, raster_max)
        raster_image = subplot.imshow(
            X=raster_array,
            cmap=colormap,
            interpolation='nearest',
            norm=norm,
            extent=raster_extent
        )
        # colorbar formatting
        figure.colorbar(
            mappable=raster_image,
            ax=subplot,
            shrink=0.75
        )

        # saving figure
        figure.tight_layout()
        figure.savefig(
            fname=figure_file,
            bbox_inches='tight'
        )

        # figure display
        matplotlib.pyplot.show() if gui_window else None
        matplotlib.pyplot.close(figure)

        return figure

    def quickview_geometry(
        self,
        shape_file: str,
        column_name: str,
        figure_file: str,
        colormap: str = 'terrain',
        fig_width: float = 6,
        fig_height: float = 6,
        log_scale: bool = False,
        gui_window: bool = True
    ) -> matplotlib.figure.Figure:

        '''
        Generates a figure for a quick view of a shapefile column.

        Parameters
        ----------
        shape_file : str
            Path to the input shapefile.

        column_name : str
            Name of the column to be plotted.

        figure_file : str
            Path to the output figure file.

        colormap : str, optional
            Registered colormap name in the `matplotlib` Python package.
            Default is 'terrain'.

        fig_width : float, optional
            Width of the figure in inches. Default is 6 inches.

        fig_height : float, optional
            Height of the figure in inches. Default is 6 inches.

        log_scale : bool, optional
            If True, display the colormap in logarithmic scale. Default is False.

        gui_window : bool, optional
            If True, open a graphical user interface window of the plot. Default is True.

        Returns
        -------
        Figure
            A figure displaying the selected column from the shapefile.
        '''

        # check validity of input figure file path
        check_file = Core().is_valid_figure_extension(figure_file)
        if check_file is False:
            raise Exception('Input figure file extension is not supported.')

        # input GeoDataFrame
        gdf = geopandas.read_file(shape_file)
        column_min = gdf[column_name].min()
        column_max = gdf[column_name].max()

        # figure setting
        figure = matplotlib.pyplot.figure(
            figsize=(fig_width, fig_height)
        )
        subplot = figure.subplots(1, 1)

        # GeoDataFrame plotting
        norm = matplotlib.colors.LogNorm(1, column_max) if log_scale else matplotlib.colors.Normalize(column_min, column_max)
        gdf.plot(
            column_name,
            ax=subplot,
            cmap=colormap,
            norm=norm,
            legend=True,
            legend_kwds={"shrink": 0.75}
        )

        # saving figure
        figure.tight_layout()
        figure.savefig(
            fname=figure_file,
            bbox_inches='tight'
        )

        # figure display
        matplotlib.pyplot.show() if gui_window else None
        matplotlib.pyplot.close(figure)

        return figure
