"Module for plotting data using plotly.express."

# *******************************************************************************#
# This module contains extra features of the geemap package.                     #
# The geemap community will maintain the extra features.                         #
# *******************************************************************************#

import pandas as pd
import plotly.express as px

from .common import *


def bar_chart(
    data=None,
    x=None,
    y=None,
    color=None,
    descending=True,
    sort_column=None,
    max_rows=None,
    x_label=None,
    y_label=None,
    title=None,
    legend_title=None,
    width=None,
    height=500,
    layout_args={},
    **kwargs,
):
    """Create a bar chart with plotly.express,

    Args:
        data: DataFrame | array-like | dict | str (local file path or HTTP URL)
            This argument needs to be passed for column names (and not keyword
            names) to be used. Array-like and dict are transformed internally to a
            pandas DataFrame. Optional: if missing, a DataFrame gets constructed
            under the hood using the other arguments.
        x: str or int or Series or array-like
            Either a name of a column in `data_frame`, or a pandas Series or
            array_like object. Values from this column or array_like are used to
            position marks along the x axis in cartesian coordinates. Either `x` or
            `y` can optionally be a list of column references or array_likes,  in
            which case the data will be treated as if it were 'wide' rather than
            'long'.
        y: str or int or Series or array-like
            Either a name of a column in `data_frame`, or a pandas Series or
            array_like object. Values from this column or array_like are used to
            position marks along the y axis in cartesian coordinates. Either `x` or
            `y` can optionally be a list of column references or array_likes,  in
            which case the data will be treated as if it were 'wide' rather than
            'long'.
        color: str or int or Series or array-like
            Either a name of a column in `data_frame`, or a pandas Series or
            array_like object. Values from this column or array_like are used to
            assign color to marks.
        descending (bool, optional): Whether to sort the data in descending order. Defaults to True.
        sort_column (str, optional): The column to sort the data. Defaults to None.
        max_rows (int, optional): Maximum number of rows to display. Defaults to None.
        x_label (str, optional): Label for the x axis. Defaults to None.
        y_label (str, optional): Label for the y axis. Defaults to None.
        title (str, optional): Title for the plot. Defaults to None.
        legend_title (str, optional): Title for the legend. Defaults to None.
        width (int, optional): Width of the plot in pixels. Defaults to None.
        height (int, optional): Height of the plot in pixels. Defaults to 500.
        layout_args (dict, optional): Layout arguments for the plot to be passed to fig.update_layout(),
            such as {'title':'Plot Title', 'title_x':0.5}. Defaults to None.
        **kwargs: Any additional arguments to pass to plotly.express.bar(), such as:

            pattern_shape: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                assign pattern shapes to marks.
            facet_row: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                assign marks to facetted subplots in the vertical direction.
            facet_col: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                assign marks to facetted subplots in the horizontal direction.
            facet_col_wrap: int
                Maximum number of facet columns. Wraps the column variable at this
                width, so that the column facets span multiple rows. Ignored if 0, and
                forced to 0 if `facet_row` or a `marginal` is set.
            facet_row_spacing: float between 0 and 1
                Spacing between facet rows, in paper units. Default is 0.03 or 0.0.7
                when facet_col_wrap is used.
            facet_col_spacing: float between 0 and 1
                Spacing between facet columns, in paper units Default is 0.02.
            hover_name: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like appear in bold
                in the hover tooltip.
            hover_data: list of str or int, or Series or array-like, or dict
                Either a list of names of columns in `data_frame`, or pandas Series, or
                array_like objects or a dict with column names as keys, with values
                True (for default formatting) False (in order to remove this column
                from hover information), or a formatting string, for example ':.3f' or
                '|%a' or list-like data to appear in the hover tooltip or tuples with a
                bool or formatting string as first element, and list-like data to
                appear in hover as second element Values from these columns appear as
                extra data in the hover tooltip.
            custom_data: list of str or int, or Series or array-like
                Either names of columns in `data_frame`, or pandas Series, or
                array_like objects Values from these columns are extra data, to be used
                in widgets or Dash callbacks for example. This data is not user-visible
                but is included in events emitted by the figure (lasso selection etc.)
            text: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like appear in the
                figure as text labels.
            base: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                position the base of the bar.
            error_x: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                size x-axis error bars. If `error_x_minus` is `None`, error bars will
                be symmetrical, otherwise `error_x` is used for the positive direction
                only.
            error_x_minus: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                size x-axis error bars in the negative direction. Ignored if `error_x`
                is `None`.
            error_y: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                size y-axis error bars. If `error_y_minus` is `None`, error bars will
                be symmetrical, otherwise `error_y` is used for the positive direction
                only.
            error_y_minus: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                size y-axis error bars in the negative direction. Ignored if `error_y`
                is `None`.
            animation_frame: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                assign marks to animation frames.
            animation_group: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                provide object-constancy across animation frames: rows with matching
                `animation_group`s will be treated as if they describe the same object
                in each frame.
            category_orders: dict with str keys and list of str values (default `{}`)
                By default, in Python 3.6+, the order of categorical values in axes,
                legends and facets depends on the order in which these values are first
                encountered in `data_frame` (and no order is guaranteed by default in
                Python below 3.6). This parameter is used to force a specific ordering
                of values per column. The keys of this dict should correspond to column
                names, and the values should be lists of strings corresponding to the
                specific display order desired.
            labels: dict with str keys and str values (default `{}`)
                By default, column names are used in the figure for axis titles, legend
                entries and hovers. This parameter allows this to be overridden. The
                keys of this dict should correspond to column names, and the values
                should correspond to the desired label to be displayed.
            color_discrete_sequence: list of str
                Strings should define valid CSS-colors. When `color` is set and the
                values in the corresponding column are not numeric, values in that
                column are assigned colors by cycling through `color_discrete_sequence`
                in the order described in `category_orders`, unless the value of
                `color` is a key in `color_discrete_map`. Various useful color
                sequences are available in the `plotly.express.colors` submodules,
                specifically `plotly.express.colors.qualitative`.
            color_discrete_map: dict with str keys and str values (default `{}`)
                String values should define valid CSS-colors Used to override
                `color_discrete_sequence` to assign a specific colors to marks
                corresponding with specific values. Keys in `color_discrete_map` should
                be values in the column denoted by `color`. Alternatively, if the
                values of `color` are valid colors, the string `'identity'` may be
                passed to cause them to be used directly.
            color_continuous_scale: list of str
                Strings should define valid CSS-colors This list is used to build a
                continuous color scale when the column denoted by `color` contains
                numeric data. Various useful color scales are available in the
                `plotly.express.colors` submodules, specifically
                `plotly.express.colors.sequential`, `plotly.express.colors.diverging`
                and `plotly.express.colors.cyclical`.
            pattern_shape_sequence: list of str
                Strings should define valid plotly.js patterns-shapes. When
                `pattern_shape` is set, values in that column are assigned patterns-
                shapes by cycling through `pattern_shape_sequence` in the order
                described in `category_orders`, unless the value of `pattern_shape` is
                a key in `pattern_shape_map`.
            pattern_shape_map: dict with str keys and str values (default `{}`)
                Strings values define plotly.js patterns-shapes. Used to override
                `pattern_shape_sequences` to assign a specific patterns-shapes to lines
                corresponding with specific values. Keys in `pattern_shape_map` should
                be values in the column denoted by `pattern_shape`. Alternatively, if
                the values of `pattern_shape` are valid patterns-shapes names, the
                string `'identity'` may be passed to cause them to be used directly.
            range_color: list of two numbers
                If provided, overrides auto-scaling on the continuous color scale.
            color_continuous_midpoint: number (default `None`)
                If set, computes the bounds of the continuous color scale to have the
                desired midpoint. Setting this value is recommended when using
                `plotly.express.colors.diverging` color scales as the inputs to
                `color_continuous_scale`.
            opacity: float
                Value between 0 and 1. Sets the opacity for markers.
            orientation: str, one of `'h'` for horizontal or `'v'` for vertical.
                (default `'v'` if `x` and `y` are provided and both continuous or both
                categorical,  otherwise `'v'`(`'h'`) if `x`(`y`) is categorical and
                `y`(`x`) is continuous,  otherwise `'v'`(`'h'`) if only `x`(`y`) is
                provided)
            barmode: str (default `'relative'`)
                One of `'group'`, `'overlay'` or `'relative'` In `'relative'` mode,
                bars are stacked above zero for positive values and below zero for
                negative values. In `'overlay'` mode, bars are drawn on top of one
                another. In `'group'` mode, bars are placed beside each other.
            log_x: boolean (default `False`)
                If `True`, the x-axis is log-scaled in cartesian coordinates.
            log_y: boolean (default `False`)
                If `True`, the y-axis is log-scaled in cartesian coordinates.
            range_x: list of two numbers
                If provided, overrides auto-scaling on the x-axis in cartesian
                coordinates.
            range_y: list of two numbers
                If provided, overrides auto-scaling on the y-axis in cartesian
                coordinates.
            text_auto: bool or string (default `False`)
                If `True` or a string, the x or y or z values will be displayed as
                text, depending on the orientation A string like `'.2f'` will be
                interpreted as a `texttemplate` numeric formatting directive.
            template: str or dict or plotly.graph_objects.layout.Template instance
                The figure template name (must be a key in plotly.io.templates) or
                definition.


    Returns:
        plotly.graph_objs._figure.Figure: A plotly figure object.
    """

    if isinstance(data, str):
        if data.startswith("http"):
            data = github_raw_url(data)
            data = get_direct_url(data)

        try:
            data = pd.read_csv(data)
        except Exception as e:
            raise ValueError(f"Could not read data from {data}. {e}")

    if not isinstance(data, pd.DataFrame):
        raise ValueError(
            "data must be a pandas DataFrame, a string or an ee.FeatureCollection."
        )

    if descending is not None:
        if sort_column is None:
            if isinstance(y, str):
                sort_column = y
            elif isinstance(y, list):
                sort_column = y[0]
        data.sort_values([sort_column, x], ascending=not (descending), inplace=True)
        if "barmode" not in kwargs:
            kwargs["barmode"] = "group"

    if isinstance(max_rows, int):
        data = data.head(max_rows)

    if "labels" in kwargs:
        labels = kwargs["labels"]
        kwargs.pop("labels")
    else:
        labels = {}

    if x_label is not None:
        labels[x] = x_label
    if y_label is not None:
        if isinstance(y, str):
            labels[y] = y_label
        elif isinstance(y, list):
            labels[y[0]] = y_label

    if isinstance(legend_title, str):
        if "legend" not in layout_args:
            layout_args["legend"] = {}
        layout_args["legend"]["title"] = legend_title

    try:
        fig = px.bar(
            data,
            x=x,
            y=y,
            color=color,
            labels=labels,
            title=title,
            width=width,
            height=height,
            **kwargs,
        )

        if isinstance(layout_args, dict):
            fig.update_layout(**layout_args)

        return fig
    except Exception as e:
        raise ValueError(f"Could not create bar plot. {e}")


def line_chart(
    data=None,
    x=None,
    y=None,
    color=None,
    descending=None,
    max_rows=None,
    x_label=None,
    y_label=None,
    title=None,
    legend_title=None,
    width=None,
    height=500,
    layout_args={},
    **kwargs,
):
    """Create a line chart with plotly.express,

    Args:
        data: DataFrame | array-like | dict | str (local file path or HTTP URL)
            This argument needs to be passed for column names (and not keyword
            names) to be used. Array-like and dict are transformed internally to a
            pandas DataFrame. Optional: if missing, a DataFrame gets constructed
            under the hood using the other arguments.
        x: str or int or Series or array-like
            Either a name of a column in `data_frame`, or a pandas Series or
            array_like object. Values from this column or array_like are used to
            position marks along the x axis in cartesian coordinates. Either `x` or
            `y` can optionally be a list of column references or array_likes,  in
            which case the data will be treated as if it were 'wide' rather than
            'long'.
        y: str or int or Series or array-like
            Either a name of a column in `data_frame`, or a pandas Series or
            array_like object. Values from this column or array_like are used to
            position marks along the y axis in cartesian coordinates. Either `x` or
            `y` can optionally be a list of column references or array_likes,  in
            which case the data will be treated as if it were 'wide' rather than
            'long'.
        color: str or int or Series or array-like
            Either a name of a column in `data_frame`, or a pandas Series or
            array_like object. Values from this column or array_like are used to
            assign color to marks.
        descending (bool, optional): Whether to sort the data in descending order. Defaults to None.
        max_rows (int, optional): Maximum number of rows to display. Defaults to None.
        x_label (str, optional): Label for the x axis. Defaults to None.
        y_label (str, optional): Label for the y axis. Defaults to None.
        title (str, optional): Title for the plot. Defaults to None.
        legend_title (str, optional): Title for the legend. Defaults to None.
        width (int, optional): Width of the plot in pixels. Defaults to None.
        height (int, optional): Height of the plot in pixels. Defaults to 500.
        layout_args (dict, optional): Layout arguments for the plot to be passed to fig.update_layout(),
            such as {'title':'Plot Title', 'title_x':0.5}. Defaults to None.
        **kwargs: Any additional arguments to pass to plotly.express.bar(), such as:

            pattern_shape: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                assign pattern shapes to marks.
            facet_row: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                assign marks to facetted subplots in the vertical direction.
            facet_col: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                assign marks to facetted subplots in the horizontal direction.
            facet_col_wrap: int
                Maximum number of facet columns. Wraps the column variable at this
                width, so that the column facets span multiple rows. Ignored if 0, and
                forced to 0 if `facet_row` or a `marginal` is set.
            facet_row_spacing: float between 0 and 1
                Spacing between facet rows, in paper units. Default is 0.03 or 0.0.7
                when facet_col_wrap is used.
            facet_col_spacing: float between 0 and 1
                Spacing between facet columns, in paper units Default is 0.02.
            hover_name: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like appear in bold
                in the hover tooltip.
            hover_data: list of str or int, or Series or array-like, or dict
                Either a list of names of columns in `data_frame`, or pandas Series, or
                array_like objects or a dict with column names as keys, with values
                True (for default formatting) False (in order to remove this column
                from hover information), or a formatting string, for example ':.3f' or
                '|%a' or list-like data to appear in the hover tooltip or tuples with a
                bool or formatting string as first element, and list-like data to
                appear in hover as second element Values from these columns appear as
                extra data in the hover tooltip.
            custom_data: list of str or int, or Series or array-like
                Either names of columns in `data_frame`, or pandas Series, or
                array_like objects Values from these columns are extra data, to be used
                in widgets or Dash callbacks for example. This data is not user-visible
                but is included in events emitted by the figure (lasso selection etc.)
            text: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like appear in the
                figure as text labels.
            base: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                position the base of the bar.
            error_x: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                size x-axis error bars. If `error_x_minus` is `None`, error bars will
                be symmetrical, otherwise `error_x` is used for the positive direction
                only.
            error_x_minus: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                size x-axis error bars in the negative direction. Ignored if `error_x`
                is `None`.
            error_y: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                size y-axis error bars. If `error_y_minus` is `None`, error bars will
                be symmetrical, otherwise `error_y` is used for the positive direction
                only.
            error_y_minus: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                size y-axis error bars in the negative direction. Ignored if `error_y`
                is `None`.
            animation_frame: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                assign marks to animation frames.
            animation_group: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                provide object-constancy across animation frames: rows with matching
                `animation_group`s will be treated as if they describe the same object
                in each frame.
            category_orders: dict with str keys and list of str values (default `{}`)
                By default, in Python 3.6+, the order of categorical values in axes,
                legends and facets depends on the order in which these values are first
                encountered in `data_frame` (and no order is guaranteed by default in
                Python below 3.6). This parameter is used to force a specific ordering
                of values per column. The keys of this dict should correspond to column
                names, and the values should be lists of strings corresponding to the
                specific display order desired.
            labels: dict with str keys and str values (default `{}`)
                By default, column names are used in the figure for axis titles, legend
                entries and hovers. This parameter allows this to be overridden. The
                keys of this dict should correspond to column names, and the values
                should correspond to the desired label to be displayed.
            color_discrete_sequence: list of str
                Strings should define valid CSS-colors. When `color` is set and the
                values in the corresponding column are not numeric, values in that
                column are assigned colors by cycling through `color_discrete_sequence`
                in the order described in `category_orders`, unless the value of
                `color` is a key in `color_discrete_map`. Various useful color
                sequences are available in the `plotly.express.colors` submodules,
                specifically `plotly.express.colors.qualitative`.
            color_discrete_map: dict with str keys and str values (default `{}`)
                String values should define valid CSS-colors Used to override
                `color_discrete_sequence` to assign a specific colors to marks
                corresponding with specific values. Keys in `color_discrete_map` should
                be values in the column denoted by `color`. Alternatively, if the
                values of `color` are valid colors, the string `'identity'` may be
                passed to cause them to be used directly.
            color_continuous_scale: list of str
                Strings should define valid CSS-colors This list is used to build a
                continuous color scale when the column denoted by `color` contains
                numeric data. Various useful color scales are available in the
                `plotly.express.colors` submodules, specifically
                `plotly.express.colors.sequential`, `plotly.express.colors.diverging`
                and `plotly.express.colors.cyclical`.
            pattern_shape_sequence: list of str
                Strings should define valid plotly.js patterns-shapes. When
                `pattern_shape` is set, values in that column are assigned patterns-
                shapes by cycling through `pattern_shape_sequence` in the order
                described in `category_orders`, unless the value of `pattern_shape` is
                a key in `pattern_shape_map`.
            pattern_shape_map: dict with str keys and str values (default `{}`)
                Strings values define plotly.js patterns-shapes. Used to override
                `pattern_shape_sequences` to assign a specific patterns-shapes to lines
                corresponding with specific values. Keys in `pattern_shape_map` should
                be values in the column denoted by `pattern_shape`. Alternatively, if
                the values of `pattern_shape` are valid patterns-shapes names, the
                string `'identity'` may be passed to cause them to be used directly.
            range_color: list of two numbers
                If provided, overrides auto-scaling on the continuous color scale.
            color_continuous_midpoint: number (default `None`)
                If set, computes the bounds of the continuous color scale to have the
                desired midpoint. Setting this value is recommended when using
                `plotly.express.colors.diverging` color scales as the inputs to
                `color_continuous_scale`.
            opacity: float
                Value between 0 and 1. Sets the opacity for markers.
            orientation: str, one of `'h'` for horizontal or `'v'` for vertical.
                (default `'v'` if `x` and `y` are provided and both continuous or both
                categorical,  otherwise `'v'`(`'h'`) if `x`(`y`) is categorical and
                `y`(`x`) is continuous,  otherwise `'v'`(`'h'`) if only `x`(`y`) is
                provided)
            barmode: str (default `'relative'`)
                One of `'group'`, `'overlay'` or `'relative'` In `'relative'` mode,
                bars are stacked above zero for positive values and below zero for
                negative values. In `'overlay'` mode, bars are drawn on top of one
                another. In `'group'` mode, bars are placed beside each other.
            log_x: boolean (default `False`)
                If `True`, the x-axis is log-scaled in cartesian coordinates.
            log_y: boolean (default `False`)
                If `True`, the y-axis is log-scaled in cartesian coordinates.
            range_x: list of two numbers
                If provided, overrides auto-scaling on the x-axis in cartesian
                coordinates.
            range_y: list of two numbers
                If provided, overrides auto-scaling on the y-axis in cartesian
                coordinates.
            text_auto: bool or string (default `False`)
                If `True` or a string, the x or y or z values will be displayed as
                text, depending on the orientation A string like `'.2f'` will be
                interpreted as a `texttemplate` numeric formatting directive.
            template: str or dict or plotly.graph_objects.layout.Template instance
                The figure template name (must be a key in plotly.io.templates) or
                definition.


    Returns:
        plotly.graph_objs._figure.Figure: A plotly figure object.
    """

    if isinstance(data, str):
        if data.startswith("http"):
            data = github_raw_url(data)
            data = get_direct_url(data)

        try:
            data = pd.read_csv(data)
        except Exception as e:
            raise ValueError(f"Could not read data from {data}. {e}")

    if not isinstance(data, pd.DataFrame):
        raise ValueError(
            "data must be a pandas DataFrame, a string or an ee.FeatureCollection."
        )

    if descending is not None:
        data.sort_values([y, x], ascending=not (descending), inplace=True)

    if isinstance(max_rows, int):
        data = data.head(max_rows)

    if "labels" in kwargs:
        labels = kwargs["labels"]
        kwargs.pop("labels")
    else:
        labels = {}

    if x_label is not None:
        labels[x] = x_label
    if y_label is not None:
        labels[y] = y_label

    if isinstance(legend_title, str):
        if "legend" not in layout_args:
            layout_args["legend"] = {}
        layout_args["legend"]["title"] = legend_title

    try:
        fig = px.line(
            data,
            x=x,
            y=y,
            color=color,
            labels=labels,
            title=title,
            width=width,
            height=height,
            **kwargs,
        )

        if isinstance(layout_args, dict):
            fig.update_layout(**layout_args)

        return fig
    except Exception as e:
        raise ValueError(f"Could not create bar plot. {e}")


def histogram(
    data=None,
    x=None,
    y=None,
    color=None,
    descending=None,
    max_rows=None,
    x_label=None,
    y_label=None,
    title=None,
    width=None,
    height=500,
    layout_args={},
    **kwargs,
):
    """Create a line chart with plotly.express,

    Args:
        data: DataFrame | array-like | dict | str (local file path or HTTP URL)
            This argument needs to be passed for column names (and not keyword
            names) to be used. Array-like and dict are transformed internally to a
            pandas DataFrame. Optional: if missing, a DataFrame gets constructed
            under the hood using the other arguments.
        x: str or int or Series or array-like
            Either a name of a column in `data_frame`, or a pandas Series or
            array_like object. Values from this column or array_like are used to
            position marks along the x axis in cartesian coordinates. Either `x` or
            `y` can optionally be a list of column references or array_likes,  in
            which case the data will be treated as if it were 'wide' rather than
            'long'.
        y: str or int or Series or array-like
            Either a name of a column in `data_frame`, or a pandas Series or
            array_like object. Values from this column or array_like are used to
            position marks along the y axis in cartesian coordinates. Either `x` or
            `y` can optionally be a list of column references or array_likes,  in
            which case the data will be treated as if it were 'wide' rather than
            'long'.
        color: str or int or Series or array-like
            Either a name of a column in `data_frame`, or a pandas Series or
            array_like object. Values from this column or array_like are used to
            assign color to marks.
        descending (bool, optional): Whether to sort the data in descending order. Defaults to None.
        max_rows (int, optional): Maximum number of rows to display. Defaults to None.
        x_label (str, optional): Label for the x axis. Defaults to None.
        y_label (str, optional): Label for the y axis. Defaults to None.
        title (str, optional): Title for the plot. Defaults to None.
        width (int, optional): Width of the plot in pixels. Defaults to None.
        height (int, optional): Height of the plot in pixels. Defaults to 500.
        layout_args (dict, optional): Layout arguments for the plot to be passed to fig.update_layout(),
            such as {'title':'Plot Title', 'title_x':0.5}. Defaults to None.
        **kwargs: Any additional arguments to pass to plotly.express.bar(), such as:

            pattern_shape: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                assign pattern shapes to marks.
            facet_row: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                assign marks to facetted subplots in the vertical direction.
            facet_col: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                assign marks to facetted subplots in the horizontal direction.
            facet_col_wrap: int
                Maximum number of facet columns. Wraps the column variable at this
                width, so that the column facets span multiple rows. Ignored if 0, and
                forced to 0 if `facet_row` or a `marginal` is set.
            facet_row_spacing: float between 0 and 1
                Spacing between facet rows, in paper units. Default is 0.03 or 0.0.7
                when facet_col_wrap is used.
            facet_col_spacing: float between 0 and 1
                Spacing between facet columns, in paper units Default is 0.02.
            hover_name: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like appear in bold
                in the hover tooltip.
            hover_data: list of str or int, or Series or array-like, or dict
                Either a list of names of columns in `data_frame`, or pandas Series, or
                array_like objects or a dict with column names as keys, with values
                True (for default formatting) False (in order to remove this column
                from hover information), or a formatting string, for example ':.3f' or
                '|%a' or list-like data to appear in the hover tooltip or tuples with a
                bool or formatting string as first element, and list-like data to
                appear in hover as second element Values from these columns appear as
                extra data in the hover tooltip.
            custom_data: list of str or int, or Series or array-like
                Either names of columns in `data_frame`, or pandas Series, or
                array_like objects Values from these columns are extra data, to be used
                in widgets or Dash callbacks for example. This data is not user-visible
                but is included in events emitted by the figure (lasso selection etc.)
            text: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like appear in the
                figure as text labels.
            base: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                position the base of the bar.
            error_x: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                size x-axis error bars. If `error_x_minus` is `None`, error bars will
                be symmetrical, otherwise `error_x` is used for the positive direction
                only.
            error_x_minus: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                size x-axis error bars in the negative direction. Ignored if `error_x`
                is `None`.
            error_y: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                size y-axis error bars. If `error_y_minus` is `None`, error bars will
                be symmetrical, otherwise `error_y` is used for the positive direction
                only.
            error_y_minus: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                size y-axis error bars in the negative direction. Ignored if `error_y`
                is `None`.
            animation_frame: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                assign marks to animation frames.
            animation_group: str or int or Series or array-like
                Either a name of a column in `data_frame`, or a pandas Series or
                array_like object. Values from this column or array_like are used to
                provide object-constancy across animation frames: rows with matching
                `animation_group`s will be treated as if they describe the same object
                in each frame.
            category_orders: dict with str keys and list of str values (default `{}`)
                By default, in Python 3.6+, the order of categorical values in axes,
                legends and facets depends on the order in which these values are first
                encountered in `data_frame` (and no order is guaranteed by default in
                Python below 3.6). This parameter is used to force a specific ordering
                of values per column. The keys of this dict should correspond to column
                names, and the values should be lists of strings corresponding to the
                specific display order desired.
            labels: dict with str keys and str values (default `{}`)
                By default, column names are used in the figure for axis titles, legend
                entries and hovers. This parameter allows this to be overridden. The
                keys of this dict should correspond to column names, and the values
                should correspond to the desired label to be displayed.
            color_discrete_sequence: list of str
                Strings should define valid CSS-colors. When `color` is set and the
                values in the corresponding column are not numeric, values in that
                column are assigned colors by cycling through `color_discrete_sequence`
                in the order described in `category_orders`, unless the value of
                `color` is a key in `color_discrete_map`. Various useful color
                sequences are available in the `plotly.express.colors` submodules,
                specifically `plotly.express.colors.qualitative`.
            color_discrete_map: dict with str keys and str values (default `{}`)
                String values should define valid CSS-colors Used to override
                `color_discrete_sequence` to assign a specific colors to marks
                corresponding with specific values. Keys in `color_discrete_map` should
                be values in the column denoted by `color`. Alternatively, if the
                values of `color` are valid colors, the string `'identity'` may be
                passed to cause them to be used directly.
            color_continuous_scale: list of str
                Strings should define valid CSS-colors This list is used to build a
                continuous color scale when the column denoted by `color` contains
                numeric data. Various useful color scales are available in the
                `plotly.express.colors` submodules, specifically
                `plotly.express.colors.sequential`, `plotly.express.colors.diverging`
                and `plotly.express.colors.cyclical`.
            pattern_shape_sequence: list of str
                Strings should define valid plotly.js patterns-shapes. When
                `pattern_shape` is set, values in that column are assigned patterns-
                shapes by cycling through `pattern_shape_sequence` in the order
                described in `category_orders`, unless the value of `pattern_shape` is
                a key in `pattern_shape_map`.
            pattern_shape_map: dict with str keys and str values (default `{}`)
                Strings values define plotly.js patterns-shapes. Used to override
                `pattern_shape_sequences` to assign a specific patterns-shapes to lines
                corresponding with specific values. Keys in `pattern_shape_map` should
                be values in the column denoted by `pattern_shape`. Alternatively, if
                the values of `pattern_shape` are valid patterns-shapes names, the
                string `'identity'` may be passed to cause them to be used directly.
            range_color: list of two numbers
                If provided, overrides auto-scaling on the continuous color scale.
            color_continuous_midpoint: number (default `None`)
                If set, computes the bounds of the continuous color scale to have the
                desired midpoint. Setting this value is recommended when using
                `plotly.express.colors.diverging` color scales as the inputs to
                `color_continuous_scale`.
            opacity: float
                Value between 0 and 1. Sets the opacity for markers.
            orientation: str, one of `'h'` for horizontal or `'v'` for vertical.
                (default `'v'` if `x` and `y` are provided and both continuous or both
                categorical,  otherwise `'v'`(`'h'`) if `x`(`y`) is categorical and
                `y`(`x`) is continuous,  otherwise `'v'`(`'h'`) if only `x`(`y`) is
                provided)
            barmode: str (default `'relative'`)
                One of `'group'`, `'overlay'` or `'relative'` In `'relative'` mode,
                bars are stacked above zero for positive values and below zero for
                negative values. In `'overlay'` mode, bars are drawn on top of one
                another. In `'group'` mode, bars are placed beside each other.
            log_x: boolean (default `False`)
                If `True`, the x-axis is log-scaled in cartesian coordinates.
            log_y: boolean (default `False`)
                If `True`, the y-axis is log-scaled in cartesian coordinates.
            range_x: list of two numbers
                If provided, overrides auto-scaling on the x-axis in cartesian
                coordinates.
            range_y: list of two numbers
                If provided, overrides auto-scaling on the y-axis in cartesian
                coordinates.
            text_auto: bool or string (default `False`)
                If `True` or a string, the x or y or z values will be displayed as
                text, depending on the orientation A string like `'.2f'` will be
                interpreted as a `texttemplate` numeric formatting directive.
            template: str or dict or plotly.graph_objects.layout.Template instance
                The figure template name (must be a key in plotly.io.templates) or
                definition.


    Returns:
        plotly.graph_objs._figure.Figure: A plotly figure object.
    """

    if isinstance(data, str):
        if data.startswith("http"):
            data = github_raw_url(data)
            data = get_direct_url(data)

        try:
            data = pd.read_csv(data)
        except Exception as e:
            raise ValueError(f"Could not read data from {data}. {e}")

    if not isinstance(data, pd.DataFrame):
        raise ValueError(
            "data must be a pandas DataFrame, a string or an ee.FeatureCollection."
        )

    if descending is not None:
        data.sort_values([y, x], ascending=not (descending), inplace=True)

    if isinstance(max_rows, int):
        data = data.head(max_rows)

    if "labels" in kwargs:
        labels = kwargs["labels"]
    else:
        labels = {}

    if x_label is not None:
        labels[x] = x_label
    if y_label is not None:
        labels[y] = y_label

    try:
        fig = px.histogram(
            data,
            x=x,
            y=y,
            color=color,
            labels=labels,
            title=title,
            width=width,
            height=height,
            **kwargs,
        )

        if isinstance(layout_args, dict):
            fig.update_layout(**layout_args)

        return fig
    except Exception as e:
        raise ValueError(f"Could not create bar plot. {e}")


def pie_chart(
    data,
    names=None,
    values=None,
    descending=True,
    max_rows=None,
    other_label=None,
    color=None,
    color_discrete_sequence=None,
    color_discrete_map=None,
    hover_name=None,
    hover_data=None,
    custom_data=None,
    labels=None,
    title=None,
    legend_title=None,
    template=None,
    width=None,
    height=None,
    opacity=None,
    hole=None,
    layout_args={},
    **kwargs,
):
    """Create a plotly pie chart.

    Args:
        data: DataFrame or array-like or dict
            This argument needs to be passed for column names (and not keyword
            names) to be used. Array-like and dict are transformed internally to a
            pandas DataFrame. Optional: if missing, a DataFrame gets constructed
            under the hood using the other arguments.
        names: str or int or Series or array-like
            Either a name of a column in `data_frame`, or a pandas Series or
            array_like object. Values from this column or array_like are used as
            labels for sectors.
        values: str or int or Series or array-like
            Either a name of a column in `data_frame`, or a pandas Series or
            array_like object. Values from this column or array_like are used to
            set values associated to sectors.
        descending (bool, optional): Whether to sort the data in descending order. Defaults to True.
        max_rows (int, optional): Maximum number of rows to display. Defaults to None.
        other_label (str, optional): Label for the "other" category. Defaults to None.
        color: str or int or Series or array-like
            Either a name of a column in `data_frame`, or a pandas Series or
            array_like object. Values from this column or array_like are used to
            assign color to marks.
        color_discrete_sequence: list of str
            Strings should define valid CSS-colors. When `color` is set and the
            values in the corresponding column are not numeric, values in that
            column are assigned colors by cycling through `color_discrete_sequence`
            in the order described in `category_orders`, unless the value of
            `color` is a key in `color_discrete_map`. Various useful color
            sequences are available in the `plotly.express.colors` submodules,
            specifically `plotly.express.colors.qualitative`.
        color_discrete_map: dict with str keys and str values (default `{}`)
            String values should define valid CSS-colors Used to override
            `color_discrete_sequence` to assign a specific colors to marks
            corresponding with specific values. Keys in `color_discrete_map` should
            be values in the column denoted by `color`. Alternatively, if the
            values of `color` are valid colors, the string `'identity'` may be
            passed to cause them to be used directly.
        hover_name: str or int or Series or array-like
            Either a name of a column in `data_frame`, or a pandas Series or
            array_like object. Values from this column or array_like appear in bold
            in the hover tooltip.
        hover_data: list of str or int, or Series or array-like, or dict
            Either a list of names of columns in `data_frame`, or pandas Series, or
            array_like objects or a dict with column names as keys, with values
            True (for default formatting) False (in order to remove this column
            from hover information), or a formatting string, for example ':.3f' or
            '|%a' or list-like data to appear in the hover tooltip or tuples with a
            bool or formatting string as first element, and list-like data to
            appear in hover as second element Values from these columns appear as
            extra data in the hover tooltip.
        custom_data: list of str or int, or Series or array-like
            Either names of columns in `data_frame`, or pandas Series, or
            array_like objects Values from these columns are extra data, to be used
            in widgets or Dash callbacks for example. This data is not user-visible
            but is included in events emitted by the figure (lasso selection etc.)
        labels: dict with str keys and str values (default `{}`)
            By default, column names are used in the figure for axis titles, legend
            entries and hovers. This parameter allows this to be overridden. The
            keys of this dict should correspond to column names, and the values
            should correspond to the desired label to be displayed.
        title: str
            The figure title.
        template: str or dict or plotly.graph_objects.layout.Template instance
            The figure template name (must be a key in plotly.io.templates) or
            definition.
        width: int (default `None`)
            The figure width in pixels.
        height: int (default `None`)
            The figure height in pixels.
        opacity: float
            Value between 0 and 1. Sets the opacity for markers.
        hole: float
            Sets the fraction of the radius to cut out of the pie.Use this to make
            a donut chart.

    Returns:
        plotly.graph_objs._figure.Figure: A plotly figure object.
    """
    if isinstance(data, str):
        if data.startswith("http"):
            data = github_raw_url(data)
            data = get_direct_url(data)

        try:
            data = pd.read_csv(data)
        except Exception as e:
            raise ValueError(f"Could not read data from {data}. {e}")

    if not isinstance(data, pd.DataFrame):
        raise ValueError(
            "data must be a pandas DataFrame, a string or an ee.FeatureCollection."
        )

    if descending is not None and isinstance(values, str):
        data.sort_values([values], ascending=not (descending), inplace=True)

    if other_label is None:
        other_label = "Other"

    if max_rows is not None and isinstance(names, str) and isinstance(values, str):
        max_rows = min(len(data), max_rows) - 2
        value = data.iloc[max_rows][values]
        data.loc[data[values] < value, names] = other_label

    if isinstance(legend_title, str):
        if "legend" not in layout_args:
            layout_args["legend"] = {}
        layout_args["legend"]["title"] = legend_title

    try:
        fig = px.pie(
            data_frame=data,
            names=names,
            values=values,
            color=color,
            color_discrete_sequence=color_discrete_sequence,
            color_discrete_map=color_discrete_map,
            hover_name=hover_name,
            hover_data=hover_data,
            custom_data=custom_data,
            labels=labels,
            title=title,
            template=template,
            width=width,
            height=height,
            opacity=opacity,
            hole=hole,
            **kwargs,
        )

        if isinstance(layout_args, dict):
            fig.update_layout(**layout_args)

        return fig
    except Exception as e:
        raise Exception(f"Could not create pie chart. {e}")
