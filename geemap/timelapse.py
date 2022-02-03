"""Module for creating timelapse from various Earth Engine ImageCollection.
"""
import datetime
import io
import os
import shutil

import ee

from .common import *


def add_overlay(
    collection, overlay_data, color="black", width=1, opacity=1.0, region=None
):
    """Adds an overlay to an image collection.

    Args:
        collection (ee.ImageCollection): The image collection to add the overlay to.
        overlay_data (str | ee.Geometry | ee.FeatureCollection): The overlay data to add to the image collection. It can be an HTTP URL to a GeoJSON file.
        color (str, optional): The color of the overlay. Defaults to 'black'.
        width (int, optional): The width of the overlay. Defaults to 1.
        opacity (float, optional): The opacity of the overlay. Defaults to 1.0.
        region (ee.Geometry | ee.FeatureCollection, optional): The region of interest to add the overlay to. Defaults to None.

    Returns:
        ee.ImageCollection: An ImageCollection with the overlay added.
    """

    # Some common administrative boundaries.
    public_assets = ["continents", "countries", "us_states", "china"]

    if not isinstance(collection, ee.ImageCollection):
        raise Exception("The collection must be an ee.ImageCollection.")

    if not isinstance(overlay_data, ee.FeatureCollection):
        if isinstance(overlay_data, str):
            try:
                if overlay_data.lower() in public_assets:
                    overlay_data = ee.FeatureCollection(
                        f"users/giswqs/public/{overlay_data.lower()}"
                    )
                elif overlay_data.startswith("http") and overlay_data.endswith(
                    ".geojson"
                ):
                    overlay_data = geojson_to_ee(overlay_data)
                else:
                    overlay_data = ee.FeatureCollection(overlay_data)

            except Exception as e:
                print(
                    "The overlay_data must be a valid ee.FeatureCollection, a valid ee.FeatureCollection asset id, or http url to a geojson file."
                )
                raise Exception(e)
        elif isinstance(overlay_data, ee.Feature):
            overlay_data = ee.FeatureCollection([overlay_data])
        elif isinstance(overlay_data, ee.Geometry):
            overlay_data = ee.FeatureCollection([ee.Feature(overlay_data)])
        else:
            raise Exception(
                "The overlay_data must be a valid ee.FeatureCollection or a valid ee.FeatureCollection asset id."
            )

    try:
        if region is not None:
            overlay_data = overlay_data.filterBounds(region)

        empty = ee.Image().byte()
        image = empty.paint(
            **{
                "featureCollection": overlay_data,
                "color": 1,
                "width": width,
            }
        ).visualize(**{"palette": check_color(color), "opacity": opacity})
        blend_col = collection.map(
            lambda img: img.blend(image).set(
                "system:time_start", img.get("system:time_start")
            )
        )
        return blend_col
    except Exception as e:
        print("Error in add_overlay:")
        raise Exception(e)


def make_gif(images, out_gif, ext="jpg", fps=10, loop=0, mp4=False, clean_up=False):
    """Creates a gif from a list of images.

    Args:
        images (list | str): The list of images or input directory to create the gif from.
        out_gif (str): File path to the output gif.
        ext (str, optional): The extension of the images. Defaults to 'jpg'.
        fps (int, optional): The frames per second of the gif. Defaults to 10.
        loop (int, optional): The number of times to loop the gif. Defaults to 0.
        mp4 (bool, optional): Whether to convert the gif to mp4. Defaults to False.

    """
    import glob
    from PIL import Image

    if isinstance(images, str) and os.path.isdir(images):
        images = list(glob.glob(os.path.join(images, f"*.{ext}")))
        if len(images) == 0:
            raise ValueError("No images found in the input directory.")
    elif not isinstance(images, list):
        raise ValueError("images must be a list or a path to the image directory.")

    images.sort()

    frames = [Image.open(image) for image in images]
    frame_one = frames[0]
    frame_one.save(
        out_gif,
        format="GIF",
        append_images=frames,
        save_all=True,
        duration=int(1000 / fps),
        loop=loop,
    )

    if mp4:
        if not is_tool("ffmpeg"):
            print("ffmpeg is not installed on your computer.")
            return

        if os.path.exists(out_gif):
            out_mp4 = out_gif.replace(".gif", ".mp4")
            cmd = f"ffmpeg -i {out_gif} -vcodec libx264 -crf 25 -pix_fmt yuv420p {out_mp4}"
            os.system(cmd)
            if not os.path.exists(out_mp4):
                raise Exception(f"Failed to create mp4 file.")
    if clean_up:
        for image in images:
            os.remove(image)


def gif_to_mp4(in_gif, out_mp4):
    """Converts a gif to mp4.

    Args:
        in_gif (str): The input gif file.
        out_mp4 (str): The output mp4 file.
    """
    from PIL import Image

    if not os.path.exists(in_gif):
        raise FileNotFoundError(f"{in_gif} does not exist.")

    out_mp4 = os.path.abspath(out_mp4)
    if not out_mp4.endswith(".mp4"):
        out_mp4 = out_mp4 + ".mp4"

    if not os.path.exists(os.path.dirname(out_mp4)):
        os.makedirs(os.path.dirname(out_mp4))

    if not is_tool("ffmpeg"):
        print("ffmpeg is not installed on your computer.")
        return

    width, height = Image.open(in_gif).size

    if width % 2 == 0 and height % 2 == 0:
        cmd = f"ffmpeg -i {in_gif} -vcodec libx264 -crf 25 -pix_fmt yuv420p {out_mp4}"
        os.system(cmd)
    else:
        width += width % 2
        height += height % 2
        cmd = f"ffmpeg -i {in_gif} -vf scale={width}:{height} -vcodec libx264 -crf 25 -pix_fmt yuv420p {out_mp4}"
        os.system(cmd)

    if not os.path.exists(out_mp4):
        raise Exception(f"Failed to create mp4 file.")


def merge_gifs(in_gifs, out_gif):
    """Merge multiple gifs into one.

    Args:
        in_gifs (str | list): The input gifs as a list or a directory path.
        out_gif (str): The output gif.

    Raises:
        Exception:  Raise exception when gifsicle is not installed.
    """
    import glob

    try:
        if isinstance(in_gifs, str) and os.path.isdir(in_gifs):
            in_gifs = glob.glob(os.path.join(in_gifs, "*.gif"))
        elif not isinstance(in_gifs, list):
            raise Exception("in_gifs must be a list.")

        in_gifs = " ".join(in_gifs)

        cmd = f"gifsicle {in_gifs} > {out_gif}"
        os.system(cmd)

    except Exception as e:
        print(
            "gifsicle is not installed. Run 'sudo apt-get install -y gifsicle' to install it."
        )
        print(e)


def add_text_to_gif(
    in_gif,
    out_gif,
    xy=None,
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="#000000",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    duration=100,
    loop=0,
):
    """Adds animated text to a GIF image.

    Args:
        in_gif (str): The file path to the input GIF image.
        out_gif (str): The file path to the output GIF image.
        xy (tuple, optional): Top left corner of the text. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        text_sequence (int, str, list, optional): Text to be drawn. It can be an integer number, a string, or a list of strings. Defaults to None.
        font_type (str, optional): Font type. Defaults to "arial.ttf".
        font_size (int, optional): Font size. Defaults to 20.
        font_color (str, optional): Font color. It can be a string (e.g., 'red'), rgb tuple (e.g., (255, 127, 0)), or hex code (e.g., '#ff00ff').  Defaults to '#000000'.
        add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
        duration (int, optional): controls how long each frame will be displayed for, in milliseconds. It is the inverse of the frame rate. Setting it to 100 milliseconds gives 10 frames per second. You can decrease the duration to give a smoother animation.. Defaults to 100.
        loop (int, optional): controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.

    """
    # import io
    import warnings

    import pkg_resources
    from PIL import Image, ImageDraw, ImageFont, ImageSequence

    warnings.simplefilter("ignore")
    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    default_font = os.path.join(pkg_dir, "data/fonts/arial.ttf")

    in_gif = os.path.abspath(in_gif)
    out_gif = os.path.abspath(out_gif)

    if not os.path.exists(in_gif):
        print("The input gif file does not exist.")
        return

    if not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    if font_type == "arial.ttf":
        font = ImageFont.truetype(default_font, font_size)
    elif font_type == "alibaba.otf":
        default_font = os.path.join(pkg_dir, "data/fonts/alibaba.otf")
        font = ImageFont.truetype(default_font, font_size)
    else:
        try:
            font_list = system_fonts(show_full_path=True)
            font_names = [os.path.basename(f) for f in font_list]
            if (font_type in font_list) or (font_type in font_names):
                font = ImageFont.truetype(font_type, font_size)
            else:
                print(
                    "The specified font type could not be found on your system. Using the default font instead."
                )
                font = ImageFont.truetype(default_font, font_size)
        except Exception as e:
            print(e)
            font = ImageFont.truetype(default_font, font_size)

    color = check_color(font_color)
    progress_bar_color = check_color(progress_bar_color)

    try:
        image = Image.open(in_gif)
    except Exception as e:
        print("An error occurred while opening the gif.")
        print(e)
        return

    count = image.n_frames
    W, H = image.size
    progress_bar_widths = [i * 1.0 / count * W for i in range(1, count + 1)]
    progress_bar_shapes = [
        [(0, H - progress_bar_height), (x, H)] for x in progress_bar_widths
    ]

    if xy is None:
        # default text location is 5% width and 5% height of the image.
        xy = (int(0.05 * W), int(0.05 * H))
    elif (xy is not None) and (not isinstance(xy, tuple)) and (len(xy) == 2):
        print("xy must be a tuple, e.g., (10, 10), ('10%', '10%')")
        return
    elif all(isinstance(item, int) for item in xy) and (len(xy) == 2):
        x, y = xy
        if (x > 0) and (x < W) and (y > 0) and (y < H):
            pass
        else:
            print(
                f"xy is out of bounds. x must be within [0, {W}], and y must be within [0, {H}]"
            )
            return
    elif all(isinstance(item, str) for item in xy) and (len(xy) == 2):
        x, y = xy
        if ("%" in x) and ("%" in y):
            try:
                x = int(float(x.replace("%", "")) / 100.0 * W)
                y = int(float(y.replace("%", "")) / 100.0 * H)
                xy = (x, y)
            except Exception:
                raise Exception(
                    "The specified xy is invalid. It must be formatted like this ('10%', '10%')"
                )
    else:
        print(
            "The specified xy is invalid. It must be formatted like this: (10, 10) or ('10%', '10%')"
        )
        return

    if text_sequence is None:
        text = [str(x) for x in range(1, count + 1)]
    elif isinstance(text_sequence, int):
        text = [str(x) for x in range(text_sequence, text_sequence + count + 1)]
    elif isinstance(text_sequence, str):
        try:
            text_sequence = int(text_sequence)
            text = [str(x) for x in range(text_sequence, text_sequence + count + 1)]
        except Exception:
            text = [text_sequence] * count
    elif isinstance(text_sequence, list) and len(text_sequence) != count:
        print(
            f"The length of the text sequence must be equal to the number ({count}) of frames in the gif."
        )
        return
    else:
        text = [str(x) for x in text_sequence]

    try:

        frames = []
        # Loop over each frame in the animated image
        for index, frame in enumerate(ImageSequence.Iterator(image)):
            # Draw the text on the frame
            frame = frame.convert("RGB")
            draw = ImageDraw.Draw(frame)
            # w, h = draw.textsize(text[index])
            draw.text(xy, text[index], font=font, fill=color)
            if add_progress_bar:
                draw.rectangle(progress_bar_shapes[index], fill=progress_bar_color)
            del draw

            b = io.BytesIO()
            frame.save(b, format="GIF")
            frame = Image.open(b)

            frames.append(frame)
        # https://www.pythoninformer.com/python-libraries/pillow/creating-animated-gif/
        # Save the frames as a new image

        frames[0].save(
            out_gif,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=loop,
            optimize=True,
        )
    except Exception as e:
        print(e)


def add_image_to_gif(
    in_gif, out_gif, in_image, xy=None, image_size=(80, 80), circle_mask=False
):
    """Adds an image logo to a GIF image.

    Args:
        in_gif (str): Input file path to the GIF image.
        out_gif (str): Output file path to the GIF image.
        in_image (str): Input file path to the image.
        xy (tuple, optional): Top left corner of the text. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        image_size (tuple, optional): Resize image. Defaults to (80, 80).
        circle_mask (bool, optional): Whether to apply a circle mask to the image. This only works with non-png images. Defaults to False.
    """
    # import io
    import warnings

    from PIL import Image, ImageDraw, ImageSequence

    warnings.simplefilter("ignore")

    in_gif = os.path.abspath(in_gif)

    is_url = False
    if in_image.startswith("http"):
        is_url = True

    if not os.path.exists(in_gif):
        print("The input gif file does not exist.")
        return

    if (not is_url) and (not os.path.exists(in_image)):
        print("The provided logo file does not exist.")
        return

    out_dir = check_dir((os.path.dirname(out_gif)))
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:
        gif = Image.open(in_gif)
    except Exception as e:
        print("An error occurred while opening the image.")
        print(e)
        return

    logo_raw_image = None
    try:
        if in_image.startswith("http"):
            logo_raw_image = open_image_from_url(in_image)
        else:
            in_image = os.path.abspath(in_image)
            logo_raw_image = Image.open(in_image)
    except Exception as e:
        print(e)

    logo_raw_size = logo_raw_image.size

    ratio = max(
        logo_raw_size[0] / image_size[0],
        logo_raw_size[1] / image_size[1],
    )
    image_resize = (int(logo_raw_size[0] / ratio), int(logo_raw_size[1] / ratio))
    image_size = min(logo_raw_size[0], image_size[0]), min(
        logo_raw_size[1], image_size[1]
    )

    logo_image = logo_raw_image.convert("RGBA")
    logo_image.thumbnail(image_size, Image.ANTIALIAS)

    gif_width, gif_height = gif.size
    mask_im = None

    if circle_mask:
        mask_im = Image.new("L", image_size, 0)
        draw = ImageDraw.Draw(mask_im)
        draw.ellipse((0, 0, image_size[0], image_size[1]), fill=255)

    if has_transparency(logo_raw_image):
        mask_im = logo_image.copy()

    if xy is None:
        # default logo location is 5% width and 5% height of the image.
        delta = 10
        xy = (gif_width - image_resize[0] - delta, gif_height - image_resize[1] - delta)
        # xy = (int(0.05 * gif_width), int(0.05 * gif_height))
    elif (xy is not None) and (not isinstance(xy, tuple)) and (len(xy) == 2):
        print("xy must be a tuple, e.g., (10, 10), ('10%', '10%')")
        return
    elif all(isinstance(item, int) for item in xy) and (len(xy) == 2):
        x, y = xy
        if (x > 0) and (x < gif_width) and (y > 0) and (y < gif_height):
            pass
        else:
            print(
                "xy is out of bounds. x must be within [0, {}], and y must be within [0, {}]".format(
                    gif_width, gif_height
                )
            )
            return
    elif all(isinstance(item, str) for item in xy) and (len(xy) == 2):
        x, y = xy
        if ("%" in x) and ("%" in y):
            try:
                x = int(float(x.replace("%", "")) / 100.0 * gif_width)
                y = int(float(y.replace("%", "")) / 100.0 * gif_height)
                xy = (x, y)
            except Exception:
                raise Exception(
                    "The specified xy is invalid. It must be formatted like this ('10%', '10%')"
                )

    else:
        raise Exception(
            "The specified xy is invalid. It must be formatted like this: (10, 10) or ('10%', '10%')"
        )

    try:

        frames = []
        for _, frame in enumerate(ImageSequence.Iterator(gif)):
            frame = frame.convert("RGBA")
            frame.paste(logo_image, xy, mask_im)

            b = io.BytesIO()
            frame.save(b, format="GIF")
            frame = Image.open(b)
            frames.append(frame)

        frames[0].save(out_gif, save_all=True, append_images=frames[1:])
    except Exception as e:
        print(e)


def reduce_gif_size(in_gif, out_gif=None):
    """Reduces a GIF image using ffmpeg.

    Args:
        in_gif (str): The input file path to the GIF image.
        out_gif (str, optional): The output file path to the GIF image. Defaults to None.
    """
    import ffmpeg
    import warnings

    warnings.filterwarnings("ignore")

    if not is_tool("ffmpeg"):
        print("ffmpeg is not installed on your computer.")
        return

    if not os.path.exists(in_gif):
        print("The input gif file does not exist.")
        return

    if out_gif is None:
        out_gif = in_gif
    elif not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    if in_gif == out_gif:
        tmp_gif = in_gif.replace(".gif", "_tmp.gif")
        shutil.copyfile(in_gif, tmp_gif)
        stream = ffmpeg.input(tmp_gif)
        stream = ffmpeg.output(stream, in_gif, loglevel="quiet").overwrite_output()
        ffmpeg.run(stream)
        os.remove(tmp_gif)

    else:
        stream = ffmpeg.input(in_gif)
        stream = ffmpeg.output(stream, out_gif, loglevel="quiet").overwrite_output()
        ffmpeg.run(stream)


def create_timeseries(
    collection,
    start_date,
    end_date,
    region=None,
    bands=None,
    frequency="year",
    reducer="median",
    drop_empty=True,
    date_format=None,
):
    """Creates a timeseries from a collection of images by a specified frequency and reducer.

    Args:
        collection (str | ee.ImageCollection): The collection of images to create a timeseries from. It can be a string representing the collection ID or an ee.ImageCollection object.
        start_date (str): The start date of the timeseries. It must be formatted like this: 'YYYY-MM-dd'.
        end_date (str): The end date of the timeseries. It must be formatted like this: 'YYYY-MM-dd'.
        region (ee.Geometry, optional): The region to use to filter the collection of images. It must be an ee.Geometry object. Defaults to None.
        bands (list, optional): The list of bands to use to create the timeseries. It must be a list of strings. Defaults to None.
        frequency (str, optional): The frequency of the timeseries. It must be one of the following: 'year', 'month', 'day', 'hour', 'minute', 'second'. Defaults to 'year'.
        reducer (str, optional):  The reducer to use to reduce the collection of images to a single value. It can be one of the following: 'median', 'mean', 'min', 'max', 'variance', 'sum'. Defaults to 'median'.
        drop_empty (bool, optional): Whether to drop empty images from the timeseries. Defaults to True.
        date_format (str, optional): A pattern, as described at http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html. Defaults to 'YYYY-MM-dd'.

    Returns:
        ee.ImageCollection: The timeseries.
    """
    if not isinstance(collection, ee.ImageCollection):
        if isinstance(collection, str):
            collection = ee.ImageCollection(collection)
        else:
            raise Exception(
                "The collection must be an ee.ImageCollection object or asset id."
            )

    if bands is not None:
        collection = collection.select(bands)
    else:
        bands = collection.first().bandNames()

    feq_dict = {
        "year": "YYYY",
        "month": "YYYY-MM",
        "quarter": "YYYY-MM",
        "week": "YYYY-MM-dd",
        "day": "YYYY-MM-dd",
        "hour": "YYYY-MM-dd HH",
        "minute": "YYYY-MM-dd HH:mm",
        "second": "YYYY-MM-dd HH:mm:ss",
    }

    if date_format is None:
        date_format = feq_dict[frequency]

    dates = date_sequence(start_date, end_date, frequency, date_format)

    try:
        reducer = eval(f"ee.Reducer.{reducer}()")
    except Exception as e:
        print("The provided reducer is invalid.")
        raise Exception(e)

    def create_image(date):
        start = ee.Date(date)
        if frequency == "quarter":
            end = start.advance(3, "month")
        else:
            end = start.advance(1, frequency)

        if region is None:
            sub_col = collection.filterDate(start, end)
            image = sub_col.reduce(reducer)

        else:
            sub_col = collection.filterDate(start, end).filterBounds(region)
            image = sub_col.reduce(reducer).clip(region)
        return image.set(
            {
                "system:time_start": ee.Date(date).millis(),
                "system:date": ee.Date(date).format(date_format),
                "empty": sub_col.size().eq(0),
            }
        ).rename(bands)

    try:

        images = ee.ImageCollection(dates.map(create_image))
        if drop_empty:
            return images.filterMetadata("empty", "equals", 0)
        else:
            return images
    except Exception as e:
        raise Exception(e)


def create_timelapse(
    collection,
    start_date,
    end_date,
    region=None,
    bands=None,
    frequency="year",
    reducer="median",
    date_format=None,
    out_gif=None,
    palette=None,
    vis_params=None,
    dimensions=768,
    frames_per_second=10,
    crs="EPSG:3857",
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
    title=None,
    title_xy=("2%", "90%"),
    add_text=True,
    text_xy=("2%", "2%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="white",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    add_colorbar=False,
    colorbar_width=6.0,
    colorbar_height=0.4,
    colorbar_label=None,
    colorbar_label_size=12,
    colorbar_label_weight="normal",
    colorbar_tick_size=10,
    colorbar_bg_color=None,
    colorbar_orientation="horizontal",
    colorbar_dpi="figure",
    colorbar_xy=None,
    colorbar_size=(300, 300),
    loop=0,
    mp4=False,
):
    """Create a timelapse from any ee.ImageCollection.

    Args:
        collection (str | ee.ImageCollection): The collection of images to create a timeseries from. It can be a string representing the collection ID or an ee.ImageCollection object.
        start_date (str): The start date of the timeseries. It must be formatted like this: 'YYYY-MM-dd'.
        end_date (str): The end date of the timeseries. It must be formatted like this: 'YYYY-MM-dd'.
        region (ee.Geometry, optional): The region to use to filter the collection of images. It must be an ee.Geometry object. Defaults to None.
        bands (list, optional): A list of band names to use in the timelapse. Defaults to None.
        frequency (str, optional): The frequency of the timeseries. It must be one of the following: 'year', 'month', 'day', 'hour', 'minute', 'second'. Defaults to 'year'.
        reducer (str, optional):  The reducer to use to reduce the collection of images to a single value. It can be one of the following: 'median', 'mean', 'min', 'max', 'variance', 'sum'. Defaults to 'median'.
        drop_empty (bool, optional): Whether to drop empty images from the timeseries. Defaults to True.
        date_format (str, optional): A pattern, as described at http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html. Defaults to 'YYYY-MM-dd'.
        out_gif (str): The output gif file path. Defaults to None.
        palette (list, optional): A list of colors to render a single-band image in the timelapse. Defaults to None.
        vis_params (dict, optional): A dictionary of visualization parameters to use in the timelapse. Defaults to None. See more at https://developers.google.com/earth-engine/guides/image_visualization.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.
        crs (str, optional): The coordinate reference system to use. Defaults to "EPSG:3857".
        overlay_data (int, str, list, optional): Administrative boundary to be drawn on the timelapse. Defaults to None.
        overlay_color (str, optional): Color for the overlay data. Can be any color name or hex color code. Defaults to 'black'.
        overlay_width (int, optional): Width of the overlay. Defaults to 1.
        overlay_opacity (float, optional): Opacity of the overlay. Defaults to 1.0.
        title (str, optional): The title of the timelapse. Defaults to None.
        title_xy (tuple, optional): Lower left corner of the title. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        add_text (bool, optional): Whether to add animated text to the timelapse. Defaults to True.
        title_xy (tuple, optional): Lower left corner of the text sequency. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        text_sequence (int, str, list, optional): Text to be drawn. It can be an integer number, a string, or a list of strings. Defaults to None.
        font_type (str, optional): Font type. Defaults to "arial.ttf".
        font_size (int, optional): Font size. Defaults to 20.
        font_color (str, optional): Font color. It can be a string (e.g., 'red'), rgb tuple (e.g., (255, 127, 0)), or hex code (e.g., '#ff00ff').  Defaults to '#000000'.
        add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
        add_colorbar (bool, optional): Whether to add a colorbar to the timelapse. Defaults to False.
        colorbar_width (float, optional): Width of the colorbar. Defaults to 6.0.
        colorbar_height (float, optional): Height of the colorbar. Defaults to 0.4.
        colorbar_label (str, optional): Label for the colorbar. Defaults to None.
        colorbar_label_size (int, optional): Font size for the colorbar label. Defaults to 12.
        colorbar_label_weight (str, optional): Font weight for the colorbar label. Defaults to 'normal'.
        colorbar_tick_size (int, optional): Font size for the colorbar ticks. Defaults to 10.
        colorbar_bg_color (str, optional): Background color for the colorbar, can be color like "white", "black". Defaults to None.
        colorbar_orientation (str, optional): Orientation of the colorbar. Defaults to 'horizontal'.
        colorbar_dpi (str, optional): DPI for the colorbar, can be numbers like 100, 300. Defaults to 'figure'.
        colorbar_xy (tuple, optional): Lower left corner of the colorbar. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        colorbar_size (tuple, optional): Size of the colorbar. It can be formatted like this: (300, 300). Defaults to (300, 300).
        loop (int, optional): Controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.
        mp4 (bool, optional): Whether to create an mp4 file. Defaults to False.

    Returns:
        str: File path to the timelapse gif.
    """
    import geemap.colormaps as cm

    if not isinstance(collection, ee.ImageCollection):
        if isinstance(collection, str):
            collection = ee.ImageCollection(collection)
        else:
            raise Exception(
                "The collection must be an ee.ImageCollection object or asset id."
            )

    col = create_timeseries(
        collection,
        start_date,
        end_date,
        region=region,
        bands=bands,
        frequency=frequency,
        reducer=reducer,
        drop_empty=True,
        date_format=date_format,
    )

    # rename the bands to remove the '_reducer' characters from the band names.
    col = col.map(
        lambda img: img.rename(
            img.bandNames().map(lambda name: ee.String(name).replace(f"_{reducer}", ""))
        )
    )

    if out_gif is None:
        out_gif = temp_file_path(".gif")
    else:
        out_gif = check_file_path(out_gif)

    out_dir = os.path.dirname(out_gif)

    if bands is None:
        names = col.first().bandNames().getInfo()
        if len(names) < 3:
            bands = [names[0]]
        else:
            bands = names[:3][::-1]
    elif isinstance(bands, str):
        bands = [bands]
    elif not isinstance(bands, list):
        raise Exception("The bands must be a string or a list of strings.")

    if isinstance(palette, str):
        palette = cm.get_palette(palette, 15)
    elif isinstance(palette, list) or isinstance(palette, tuple):
        pass
    elif palette is not None:
        raise Exception("The palette must be a string or a list of strings.")

    if vis_params is None:
        img = col.first().select(bands)
        scale = collection.first().select(0).projection().nominalScale().multiply(10)
        min_value = min(
            image_min_value(img, region=region, scale=scale).getInfo().values()
        )
        max_value = max(
            image_max_value(img, region=region, scale=scale).getInfo().values()
        )
        vis_params = {"bands": bands, "min": min_value, "max": max_value}

        if len(bands) == 1:
            if palette is not None:
                vis_params["palette"] = palette
            else:
                vis_params["palette"] = cm.palettes.ndvi
    elif isinstance(vis_params, dict):
        if "bands" not in vis_params:
            vis_params["bands"] = bands
        if "min" not in vis_params:
            img = col.first().select(bands)
            scale = (
                collection.first().select(0).projection().nominalScale().multiply(10)
            )
            vis_params["min"] = min(
                image_min_value(img, region=region, scale=scale).getInfo().values()
            )
        if "max" not in vis_params:
            img = col.first().select(bands)
            scale = (
                collection.first().select(0).projection().nominalScale().multiply(10)
            )
            vis_params["max"] = max(
                image_max_value(img, region=region, scale=scale).getInfo().values()
            )
        if palette is None and (len(bands) == 1) and ("palette" not in vis_params):
            vis_params["palette"] = cm.palettes.ndvi
        elif palette is not None and ("palette" not in vis_params):
            vis_params["palette"] = palette
        if len(bands) > 1 and "palette" in vis_params:
            del vis_params["palette"]
    else:
        raise Exception("The vis_params must be a dictionary.")

    col = col.select(bands).map(
        lambda img: img.visualize(**vis_params).set(
            {
                "system:time_start": img.get("system:time_start"),
                "system:date": img.get("system:date"),
            }
        )
    )

    if overlay_data is not None:
        col = add_overlay(
            col, overlay_data, overlay_color, overlay_width, overlay_opacity
        )

    video_args = {}
    video_args["dimensions"] = dimensions
    video_args["region"] = region
    video_args["framesPerSecond"] = frames_per_second
    video_args["crs"] = crs
    video_args["min"] = 0
    video_args["max"] = 255

    # if crs is not None:
    #     video_args["crs"] = crs

    if "palette" in vis_params or len(bands) > 1:
        video_args["bands"] = ["vis-red", "vis-green", "vis-blue"]
    else:
        video_args["bands"] = ["vis-gray"]

    if dimensions > 768:
        count = col.size().getInfo()
        basename = os.path.basename(out_gif)[:-4]
        names = [
            os.path.join(
                out_dir, f"{basename}_{str(i+1).zfill(int(len(str(count))))}.jpg"
            )
            for i in range(count)
        ]
        get_image_collection_thumbnails(
            col,
            out_dir,
            vis_params={
                "min": 0,
                "max": 255,
                "bands": video_args["bands"],
            },
            dimensions=dimensions,
            names=names,
        )
        make_gif(
            names,
            out_gif,
            fps=frames_per_second,
            loop=loop,
            mp4=False,
            clean_up=True,
        )
    else:
        download_ee_video(col, video_args, out_gif)

    if title is not None and isinstance(title, str):
        add_text_to_gif(
            out_gif,
            out_gif,
            xy=title_xy,
            text_sequence=title,
            font_type=font_type,
            font_size=font_size,
            font_color=font_color,
            add_progress_bar=add_progress_bar,
            progress_bar_color=progress_bar_color,
            progress_bar_height=progress_bar_height,
            duration=1000 / frames_per_second,
            loop=loop,
        )
    if add_text:
        if text_sequence is None:
            text_sequence = col.aggregate_array("system:date").getInfo()
        add_text_to_gif(
            out_gif,
            out_gif,
            xy=text_xy,
            text_sequence=text_sequence,
            font_type=font_type,
            font_size=font_size,
            font_color=font_color,
            add_progress_bar=add_progress_bar,
            progress_bar_color=progress_bar_color,
            progress_bar_height=progress_bar_height,
            duration=1000 / frames_per_second,
            loop=loop,
        )
    if add_colorbar:
        colorbar = save_colorbar(
            None,
            colorbar_width,
            colorbar_height,
            vis_params["min"],
            vis_params["max"],
            vis_params["palette"],
            label=colorbar_label,
            label_size=colorbar_label_size,
            label_weight=colorbar_label_weight,
            tick_size=colorbar_tick_size,
            bg_color=colorbar_bg_color,
            orientation=colorbar_orientation,
            dpi=colorbar_dpi,
            show_colorbar=False,
        )
        add_image_to_gif(out_gif, out_gif, colorbar, colorbar_xy, colorbar_size)

    if os.path.exists(out_gif):
        reduce_gif_size(out_gif)

    if mp4:
        out_mp4 = out_gif.replace(".gif", ".mp4")
        gif_to_mp4(out_gif, out_mp4)

    return out_gif


def naip_timeseries(roi=None, start_year=2003, end_year=2021, RGBN=False):
    """Creates NAIP annual timeseries

    Args:
        roi (object, optional): An ee.Geometry representing the region of interest. Defaults to None.
        start_year (int, optional): Starting year for the timeseries. Defaults to 2003.
        end_year (int, optional): Ending year for the timeseries. Defaults to 2021.
        RGBN (bool, optional): Whether to retrieve 4-band NAIP imagery only.
    Returns:
        object: An ee.ImageCollection representing annual NAIP imagery.
    """
    try:

        def get_annual_NAIP(year):
            try:
                collection = ee.ImageCollection("USDA/NAIP/DOQQ")
                if roi is not None:
                    collection = collection.filterBounds(roi)
                start_date = ee.Date.fromYMD(year, 1, 1)
                end_date = ee.Date.fromYMD(year, 12, 31)
                naip = collection.filterDate(start_date, end_date)
                if RGBN:
                    naip = naip.filter(ee.Filter.listContains("system:band_names", "N"))
                if roi is not None:
                    if isinstance(roi, ee.Geometry):
                        image = ee.Image(ee.ImageCollection(naip).mosaic().clip(roi))
                    elif isinstance(roi, ee.FeatureCollection):
                        image = ee.Image(
                            ee.ImageCollection(naip).mosaic().clipToCollection(roi)
                        )
                else:
                    image = ee.Image(ee.ImageCollection(naip).mosaic())
                return image.set(
                    {
                        "system:time_start": ee.Date(start_date).millis(),
                        "system:time_end": ee.Date(end_date).millis(),
                        "empty": naip.size().eq(0),
                    }
                )
            except Exception as e:
                raise Exception(e)

        years = ee.List.sequence(start_year, end_year)
        collection = ee.ImageCollection(years.map(get_annual_NAIP))
        return collection.filterMetadata("empty", "equals", 0)

    except Exception as e:
        raise Exception(e)


def naip_timelapse(
    region,
    start_year=2003,
    end_year=2021,
    out_gif=None,
    bands=None,
    palette=None,
    vis_params=None,
    dimensions=768,
    frames_per_second=3,
    crs="EPSG:3857",
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
    title=None,
    title_xy=("2%", "90%"),
    add_text=True,
    text_xy=("2%", "2%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="white",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    loop=0,
    mp4=False,
):
    """Create a timelapse from NAIP imagery.

    Args:
        region (ee.Geometry): The region to use to filter the collection of images. It must be an ee.Geometry object. Defaults to None.
        start_year (int | str, optional): The start year of the timeseries. It must be formatted like this: 'YYYY'. Defaults to 2003.
        end_year (int | str, optional): The end year of the timeseries. It must be formatted like this: 'YYYY'. Defaults to 2021.
        out_gif (str): The output gif file path. Defaults to None.
        bands (list, optional): A list of band names to use in the timelapse. Defaults to None.
        palette (list, optional): A list of colors to render a single-band image in the timelapse. Defaults to None.
        vis_params (dict, optional): A dictionary of visualization parameters to use in the timelapse. Defaults to None. See more at https://developers.google.com/earth-engine/guides/image_visualization.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.
        crs (str, optional): The coordinate reference system to use. Defaults to "EPSG:3857".
        overlay_data (int, str, list, optional): Administrative boundary to be drawn on the timelapse. Defaults to None.
        overlay_color (str, optional): Color for the overlay data. Can be any color name or hex color code. Defaults to 'black'.
        overlay_width (int, optional): Width of the overlay. Defaults to 1.
        overlay_opacity (float, optional): Opacity of the overlay. Defaults to 1.0.
        title (str, optional): The title of the timelapse. Defaults to None.
        title_xy (tuple, optional): Lower left corner of the title. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        add_text (bool, optional): Whether to add animated text to the timelapse. Defaults to True.
        title_xy (tuple, optional): Lower left corner of the text sequency. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        text_sequence (int, str, list, optional): Text to be drawn. It can be an integer number, a string, or a list of strings. Defaults to None.
        font_type (str, optional): Font type. Defaults to "arial.ttf".
        font_size (int, optional): Font size. Defaults to 20.
        font_color (str, optional): Font color. It can be a string (e.g., 'red'), rgb tuple (e.g., (255, 127, 0)), or hex code (e.g., '#ff00ff').  Defaults to '#000000'.
        add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
        loop (int, optional): Controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.
        mp4 (bool, optional): Whether to create an mp4 file. Defaults to False.

    Returns:
        str: File path to the timelapse gif.
    """

    try:
        collection = ee.ImageCollection("USDA/NAIP/DOQQ")
        start_date = str(start_year) + "-01-01"
        end_date = str(end_year) + "-12-31"
        frequency = "year"
        reducer = "median"
        date_format = "YYYY"

        if bands is not None and isinstance(bands, list) and "N" in bands:
            collection = collection.filter(
                ee.Filter.listContains("system:band_names", "N")
            )

        return create_timelapse(
            collection,
            start_date,
            end_date,
            region,
            bands,
            frequency,
            reducer,
            date_format,
            out_gif,
            palette,
            vis_params,
            dimensions,
            frames_per_second,
            crs,
            overlay_data,
            overlay_color,
            overlay_width,
            overlay_opacity,
            title,
            title_xy,
            add_text,
            text_xy,
            text_sequence,
            font_type,
            font_size,
            font_color,
            add_progress_bar,
            progress_bar_color,
            progress_bar_height,
            loop=loop,
            mp4=mp4,
        )

    except Exception as e:
        raise Exception(e)


def sentinel2_timeseries(
    roi=None,
    start_year=2015,
    end_year=2021,
    start_date="01-01",
    end_date="12-31",
    apply_fmask=True,
    frequency="year",
    date_format=None,
):
    """Generates an annual Sentinel 2 ImageCollection. This algorithm is adapted from https://gist.github.com/jdbcode/76b9ac49faf51627ebd3ff988e10adbc. A huge thank you to Justin Braaten for sharing his fantastic work.
       Images include both level 1C and level 2A imagery.
    Args:

        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 2015.
        end_year (int, optional): Ending year for the timelapse. Defaults to 2021.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '01-01'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '12-31'.
        apply_fmask (bool, optional): Whether to apply Fmask (Function of mask) for automated clouds, cloud shadows, snow, and water masking.
        frequency (str, optional): Frequency of the timelapse. Defaults to 'year'.
        date_format (str, optional): Format of the date. Defaults to None.

    Returns:
        object: Returns an ImageCollection containing annual Sentinel 2 images.
    """
    ################################################################################

    ################################################################################
    # Input and output parameters.
    import re

    # import datetime

    if roi is None:
        # roi = ee.Geometry.Polygon(
        #     [[[-180, -80],
        #       [-180, 80],
        #         [180, 80],
        #         [180, -80],
        #         [-180, -80]]], None, False)
        roi = ee.Geometry.Polygon(
            [
                [
                    [-115.471773, 35.892718],
                    [-115.471773, 36.409454],
                    [-114.271283, 36.409454],
                    [-114.271283, 35.892718],
                    [-115.471773, 35.892718],
                ]
            ],
            None,
            False,
        )

    if not isinstance(roi, ee.Geometry):

        try:
            roi = roi.geometry()
        except Exception as e:
            print("Could not convert the provided roi to ee.Geometry")
            print(e)
            return

    # Adjusts longitudes less than -180 degrees or greater than 180 degrees.
    geojson = ee_to_geojson(roi)
    geojson = adjust_longitude(geojson)
    roi = ee.Geometry(geojson)

    feq_dict = {
        "year": "YYYY",
        "month": "YYYY-MM",
        "quarter": "YYYY-MM",
    }

    if date_format is None:
        date_format = feq_dict[frequency]

    if frequency not in feq_dict:
        raise ValueError("frequency must be year, quarter, or month.")

    ################################################################################
    # Setup vars to get dates.
    if isinstance(start_year, int) and (start_year >= 2015) and (start_year <= 2021):
        pass
    else:
        print("The start year must be an integer >= 2015.")
        return

    if isinstance(end_year, int) and (end_year >= 2015) and (end_year <= 2021):
        pass
    else:
        print("The end year must be an integer <= 2021.")
        return

    if re.match("[0-9]{2}\-[0-9]{2}", start_date) and re.match(
        "[0-9]{2}\-[0-9]{2}", end_date
    ):
        pass
    else:
        print("The start data and end date must be month-day, such as 06-10, 09-20")
        return

    try:
        datetime.datetime(int(start_year), int(start_date[:2]), int(start_date[3:5]))
        datetime.datetime(int(end_year), int(end_date[:2]), int(end_date[3:5]))
    except Exception as e:
        raise ValueError("The input dates are invalid.")

    try:
        start_test = datetime.datetime(
            int(start_year), int(start_date[:2]), int(start_date[3:5])
        )
        end_test = datetime.datetime(
            int(end_year), int(end_date[:2]), int(end_date[3:5])
        )
        if start_test > end_test:
            raise ValueError("Start date must be prior to end date")
    except Exception as e:
        raise Exception(e)

    def days_between(d1, d2):
        d1 = datetime.datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)

    n_days = days_between(
        str(start_year) + "-" + start_date, str(start_year) + "-" + end_date
    )
    start_month = int(start_date[:2])
    start_day = int(start_date[3:5])
    # start_date = str(start_year) + "-" + start_date
    # end_date = str(end_year) + "-" + end_date

    # # Define a collection filter by date, bounds, and quality.
    # def colFilter(col, aoi):  # , startDate, endDate):
    #     return(col.filterBounds(aoi))

    # Get Sentinel 2 collections, both Level-1C (top of atmophere) and Level-2A (surface reflectance)
    MSILCcol = ee.ImageCollection("COPERNICUS/S2")
    MSI2Acol = ee.ImageCollection("COPERNICUS/S2_SR")

    # Define a collection filter by date, bounds, and quality.
    def colFilter(col, roi, start_date, end_date):
        return col.filterBounds(roi).filterDate(start_date, end_date)
        # .filter('CLOUD_COVER < 5')
        # .filter('GEOMETRIC_RMSE_MODEL < 15')
        # .filter('IMAGE_QUALITY == 9 || IMAGE_QUALITY_OLI == 9'))

    # Function to get and rename bands of interest from MSI
    def renameMSI(img):
        return img.select(
            ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12", "QA60"],
            [
                "Blue",
                "Green",
                "Red",
                "Red Edge 1",
                "Red Edge 2",
                "Red Edge 3",
                "NIR",
                "Red Edge 4",
                "SWIR1",
                "SWIR2",
                "QA60",
            ],
        )

    # Add NBR for LandTrendr segmentation.

    def calcNbr(img):
        return img.addBands(
            img.normalizedDifference(["NIR", "SWIR2"]).multiply(-10000).rename("NBR")
        ).int16()

    # Define function to mask out clouds and cloud shadows in images.
    # Use CFmask band included in USGS Landsat SR image product.

    def fmask(img):
        cloudOpaqueBitMask = 1 << 10
        cloudCirrusBitMask = 1 << 11
        qa = img.select("QA60")
        mask = (
            qa.bitwiseAnd(cloudOpaqueBitMask)
            .eq(0)
            .And(qa.bitwiseAnd(cloudCirrusBitMask).eq(0))
        )
        return img.updateMask(mask)

    # Define function to prepare MSI images.
    def prepMSI(img):
        orig = img
        img = renameMSI(img)
        if apply_fmask:
            img = fmask(img)
        return ee.Image(img.copyProperties(orig, orig.propertyNames())).resample(
            "bicubic"
        )

    # Get annual median collection.
    def getAnnualComp(y):
        startDate = ee.Date.fromYMD(
            ee.Number(y), ee.Number(start_month), ee.Number(start_day)
        )
        endDate = startDate.advance(ee.Number(n_days), "day")

        # Filter collections and prepare them for merging.
        MSILCcoly = colFilter(MSILCcol, roi, startDate, endDate).map(prepMSI)
        MSI2Acoly = colFilter(MSI2Acol, roi, startDate, endDate).map(prepMSI)

        # Merge the collections.
        col = MSILCcoly.merge(MSI2Acoly)

        yearImg = col.median()
        nBands = yearImg.bandNames().size()
        yearImg = ee.Image(ee.Algorithms.If(nBands, yearImg, dummyImg))
        return calcNbr(yearImg).set(
            {
                "year": y,
                "system:time_start": startDate.millis(),
                "nBands": nBands,
                "system:date": ee.Date(startDate).format(date_format),
            }
        )

    # Get quarterly median collection.
    def getQuarterlyComp(startDate):
        startDate = ee.Date(startDate)
        endDate = startDate.advance(3, "month")

        # Filter collections and prepare them for merging.
        MSILCcoly = colFilter(MSILCcol, roi, startDate, endDate).map(prepMSI)
        MSI2Acoly = colFilter(MSI2Acol, roi, startDate, endDate).map(prepMSI)

        # Merge the collections.
        col = MSILCcoly.merge(MSI2Acoly)

        yearImg = col.median()
        nBands = yearImg.bandNames().size()
        yearImg = ee.Image(ee.Algorithms.If(nBands, yearImg, dummyImg))
        return calcNbr(yearImg).set(
            {
                "system:time_start": startDate.millis(),
                "nBands": nBands,
                "system:date": ee.Date(startDate).format(date_format),
            }
        )

    # Get monthly median collection.
    def getMonthlyComp(startDate):
        startDate = ee.Date(startDate)
        endDate = startDate.advance(1, "month")

        # Filter collections and prepare them for merging.
        MSILCcoly = colFilter(MSILCcol, roi, startDate, endDate).map(prepMSI)
        MSI2Acoly = colFilter(MSI2Acol, roi, startDate, endDate).map(prepMSI)

        # Merge the collections.
        col = MSILCcoly.merge(MSI2Acoly)

        yearImg = col.median()
        nBands = yearImg.bandNames().size()
        yearImg = ee.Image(ee.Algorithms.If(nBands, yearImg, dummyImg))
        return calcNbr(yearImg).set(
            {
                "system:time_start": startDate.millis(),
                "nBands": nBands,
                "system:date": ee.Date(startDate).format(date_format),
            }
        )

    ################################################################################

    # Make a dummy image for missing years.
    bandNames = ee.List(
        [
            "Blue",
            "Green",
            "Red",
            "Red Edge 1",
            "Red Edge 2",
            "Red Edge 3",
            "NIR",
            "Red Edge 4",
            "SWIR1",
            "SWIR2",
            "QA60",
        ]
    )
    fillerValues = ee.List.repeat(0, bandNames.size())
    dummyImg = ee.Image.constant(fillerValues).rename(bandNames).selfMask().int16()

    # ################################################################################
    # # Get a list of years
    # years = ee.List.sequence(start_year, end_year)

    # ################################################################################
    # # Make list of annual image composites.
    # imgList = years.map(getAnnualComp)

    if frequency == "year":
        years = ee.List.sequence(start_year, end_year)
        imgList = years.map(getAnnualComp)
    elif frequency == "quarter":
        quarters = date_sequence(
            str(start_year) + "-01-01", str(end_year) + "-12-31", "quarter", date_format
        )
        imgList = quarters.map(getQuarterlyComp)
    elif frequency == "month":
        months = date_sequence(
            str(start_year) + "-01-01", str(end_year) + "-12-31", "month", date_format
        )
        imgList = months.map(getMonthlyComp)

    # Convert image composite list to collection
    imgCol = ee.ImageCollection.fromImages(imgList)

    imgCol = imgCol.map(lambda img: img.clip(roi))

    return imgCol


def landsat_timeseries(
    roi=None,
    start_year=1984,
    end_year=2021,
    start_date="06-10",
    end_date="09-20",
    apply_fmask=True,
    frequency="year",
    date_format=None,
):
    """Generates an annual Landsat ImageCollection. This algorithm is adapted from https://gist.github.com/jdbcode/76b9ac49faf51627ebd3ff988e10adbc. A huge thank you to Justin Braaten for sharing his fantastic work.

    Args:
        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 1984.
        end_year (int, optional): Ending year for the timelapse. Defaults to 2021.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '06-10'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '09-20'.
        apply_fmask (bool, optional): Whether to apply Fmask (Function of mask) for automated clouds, cloud shadows, snow, and water masking.
        frequency (str, optional): Frequency of the timelapse. Defaults to 'year'.
        date_format (str, optional): Format of the date. Defaults to None.
    Returns:
        object: Returns an ImageCollection containing annual Landsat images.
    """

    ################################################################################
    # Input and output parameters.
    import re

    # import datetime

    if roi is None:
        roi = ee.Geometry.Polygon(
            [
                [
                    [-115.471773, 35.892718],
                    [-115.471773, 36.409454],
                    [-114.271283, 36.409454],
                    [-114.271283, 35.892718],
                    [-115.471773, 35.892718],
                ]
            ],
            None,
            False,
        )

    if not isinstance(roi, ee.Geometry):

        try:
            roi = roi.geometry()
        except Exception as e:
            print("Could not convert the provided roi to ee.Geometry")
            print(e)
            return

    feq_dict = {
        "year": "YYYY",
        "month": "YYYY-MM",
        "quarter": "YYYY-MM",
    }

    if date_format is None:
        date_format = feq_dict[frequency]

    if frequency not in feq_dict:
        raise ValueError("frequency must be year, quarter, or month.")

    ################################################################################

    # Setup vars to get dates.
    if isinstance(start_year, int) and (start_year >= 1984) and (start_year < 2021):
        pass
    else:
        print("The start year must be an integer >= 1984.")
        return

    if isinstance(end_year, int) and (end_year > 1984) and (end_year <= 2021):
        pass
    else:
        print("The end year must be an integer <= 2021.")
        return

    if re.match("[0-9]{2}\-[0-9]{2}", start_date) and re.match(
        "[0-9]{2}\-[0-9]{2}", end_date
    ):
        pass
    else:
        print("The start date and end date must be month-day, such as 06-10, 09-20")
        return

    try:
        datetime.datetime(int(start_year), int(start_date[:2]), int(start_date[3:5]))
        datetime.datetime(int(end_year), int(end_date[:2]), int(end_date[3:5]))
    except Exception as e:
        print("The input dates are invalid.")
        raise Exception(e)

    def days_between(d1, d2):
        d1 = datetime.datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)

    n_days = days_between(
        str(start_year) + "-" + start_date, str(start_year) + "-" + end_date
    )
    start_month = int(start_date[:2])
    start_day = int(start_date[3:5])
    # start_date = str(start_year) + "-" + start_date
    # end_date = str(end_year) + "-" + end_date

    # # Define a collection filter by date, bounds, and quality.
    # def colFilter(col, aoi):  # , startDate, endDate):
    #     return(col.filterBounds(aoi))

    # Landsat collection preprocessingEnabled
    # Get Landsat surface reflectance collections for OLI, ETM+ and TM sensors.
    LC08col = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR")
    LE07col = ee.ImageCollection("LANDSAT/LE07/C01/T1_SR")
    LT05col = ee.ImageCollection("LANDSAT/LT05/C01/T1_SR")
    LT04col = ee.ImageCollection("LANDSAT/LT04/C01/T1_SR")

    # Define a collection filter by date, bounds, and quality.
    def colFilter(col, roi, start_date, end_date):
        return col.filterBounds(roi).filterDate(start_date, end_date)
        # .filter('CLOUD_COVER < 5')
        # .filter('GEOMETRIC_RMSE_MODEL < 15')
        # .filter('IMAGE_QUALITY == 9 || IMAGE_QUALITY_OLI == 9'))

    # Function to get and rename bands of interest from OLI.
    def renameOli(img):
        return img.select(
            ["B2", "B3", "B4", "B5", "B6", "B7", "pixel_qa"],
            ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "pixel_qa"],
        )

    # Function to get and rename bands of interest from ETM+.
    def renameEtm(img):
        return img.select(
            ["B1", "B2", "B3", "B4", "B5", "B7", "pixel_qa"],
            ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "pixel_qa"],
        )

    # Add NBR for LandTrendr segmentation.
    def calcNbr(img):
        return img.addBands(
            img.normalizedDifference(["NIR", "SWIR2"]).multiply(-10000).rename("NBR")
        ).int16()

    # Define function to mask out clouds and cloud shadows in images.
    # Use CFmask band included in USGS Landsat SR image product.
    def fmask(img):
        cloudShadowBitMask = 1 << 3
        cloudsBitMask = 1 << 5
        qa = img.select("pixel_qa")
        mask = (
            qa.bitwiseAnd(cloudShadowBitMask)
            .eq(0)
            .And(qa.bitwiseAnd(cloudsBitMask).eq(0))
        )
        return img.updateMask(mask)

    # Define function to prepare OLI images.
    def prepOli(img):
        orig = img
        img = renameOli(img)
        if apply_fmask:
            img = fmask(img)
        return ee.Image(img.copyProperties(orig, orig.propertyNames())).resample(
            "bicubic"
        )

    # Define function to prepare ETM+ images.
    def prepEtm(img):
        orig = img
        img = renameEtm(img)
        if apply_fmask:
            img = fmask(img)
        return ee.Image(img.copyProperties(orig, orig.propertyNames())).resample(
            "bicubic"
        )

    # Get annual median collection.
    def getAnnualComp(y):
        startDate = ee.Date.fromYMD(
            ee.Number(y), ee.Number(start_month), ee.Number(start_day)
        )
        endDate = startDate.advance(ee.Number(n_days), "day")

        # Filter collections and prepare them for merging.
        LC08coly = colFilter(LC08col, roi, startDate, endDate).map(prepOli)
        LE07coly = colFilter(LE07col, roi, startDate, endDate).map(prepEtm)
        LT05coly = colFilter(LT05col, roi, startDate, endDate).map(prepEtm)
        LT04coly = colFilter(LT04col, roi, startDate, endDate).map(prepEtm)

        # Merge the collections.
        col = LC08coly.merge(LE07coly).merge(LT05coly).merge(LT04coly)

        yearImg = col.median()
        nBands = yearImg.bandNames().size()
        yearImg = ee.Image(ee.Algorithms.If(nBands, yearImg, dummyImg))
        return calcNbr(yearImg).set(
            {
                "year": y,
                "system:time_start": startDate.millis(),
                "nBands": nBands,
                "system:date": ee.Date(startDate).format(date_format),
            }
        )

    # Get monthly median collection.
    def getMonthlyComp(startDate):

        startDate = ee.Date(startDate)
        endDate = startDate.advance(1, "month")

        # Filter collections and prepare them for merging.
        LC08coly = colFilter(LC08col, roi, startDate, endDate).map(prepOli)
        LE07coly = colFilter(LE07col, roi, startDate, endDate).map(prepEtm)
        LT05coly = colFilter(LT05col, roi, startDate, endDate).map(prepEtm)
        LT04coly = colFilter(LT04col, roi, startDate, endDate).map(prepEtm)

        # Merge the collections.
        col = LC08coly.merge(LE07coly).merge(LT05coly).merge(LT04coly)

        monthImg = col.median()
        nBands = monthImg.bandNames().size()
        monthImg = ee.Image(ee.Algorithms.If(nBands, monthImg, dummyImg))
        return calcNbr(monthImg).set(
            {
                "system:time_start": startDate.millis(),
                "nBands": nBands,
                "system:date": ee.Date(startDate).format(date_format),
            }
        )

    # Get quarterly median collection.
    def getQuarterlyComp(startDate):

        startDate = ee.Date(startDate)

        endDate = startDate.advance(3, "month")

        # Filter collections and prepare them for merging.
        LC08coly = colFilter(LC08col, roi, startDate, endDate).map(prepOli)
        LE07coly = colFilter(LE07col, roi, startDate, endDate).map(prepEtm)
        LT05coly = colFilter(LT05col, roi, startDate, endDate).map(prepEtm)
        LT04coly = colFilter(LT04col, roi, startDate, endDate).map(prepEtm)

        # Merge the collections.
        col = LC08coly.merge(LE07coly).merge(LT05coly).merge(LT04coly)

        quarter = col.median()
        nBands = quarter.bandNames().size()
        quarter = ee.Image(ee.Algorithms.If(nBands, quarter, dummyImg))
        return calcNbr(quarter).set(
            {
                "system:time_start": startDate.millis(),
                "nBands": nBands,
                "system:date": ee.Date(startDate).format(date_format),
            }
        )

    ################################################################################

    # Make a dummy image for missing years.
    bandNames = ee.List(["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "pixel_qa"])
    fillerValues = ee.List.repeat(0, bandNames.size())
    dummyImg = ee.Image.constant(fillerValues).rename(bandNames).selfMask().int16()

    # ################################################################################
    # # Get a list of years
    # years = ee.List.sequence(start_year, end_year)

    # ################################################################################
    # # Make list of annual image composites.
    # imgList = years.map(getAnnualComp)

    if frequency == "year":
        years = ee.List.sequence(start_year, end_year)
        imgList = years.map(getAnnualComp)
    elif frequency == "quarter":
        quarters = date_sequence(
            str(start_year) + "-01-01", str(end_year) + "-12-31", "quarter", date_format
        )
        imgList = quarters.map(getQuarterlyComp)
    elif frequency == "month":
        months = date_sequence(
            str(start_year) + "-01-01", str(end_year) + "-12-31", "month", date_format
        )
        imgList = months.map(getMonthlyComp)

    # Convert image composite list to collection
    imgCol = ee.ImageCollection.fromImages(imgList)

    imgCol = imgCol.map(
        lambda img: img.clip(roi).set({"coordinates": roi.coordinates()})
    )

    return imgCol

    # ################################################################################
    # # Run LandTrendr.
    # lt = ee.Algorithms.TemporalSegmentation.LandTrendr(
    #     timeSeries=imgCol.select(['NBR', 'SWIR1', 'NIR', 'Green']),
    #     maxSegments=10,
    #     spikeThreshold=0.7,
    #     vertexCountOvershoot=3,
    #     preventOneYearRecovery=True,
    #     recoveryThreshold=0.5,
    #     pvalThreshold=0.05,
    #     bestModelProportion=0.75,
    #     minObservationsNeeded=6)

    # ################################################################################
    # # Get fitted imagery. This starts export tasks.
    # def getYearStr(year):
    #     return(ee.String('yr_').cat(ee.Algorithms.String(year).slice(0,4)))

    # yearsStr = years.map(getYearStr)

    # r = lt.select(['SWIR1_fit']).arrayFlatten([yearsStr]).toShort()
    # g = lt.select(['NIR_fit']).arrayFlatten([yearsStr]).toShort()
    # b = lt.select(['Green_fit']).arrayFlatten([yearsStr]).toShort()

    # for i, c in zip([r, g, b], ['r', 'g', 'b']):
    #     descr = 'mamore-river-'+c
    #     name = 'users/user/'+descr
    #     print(name)
    #     task = ee.batch.Export.image.toAsset(
    #     image=i,
    #     region=roi.getInfo()['coordinates'],
    #     assetId=name,
    #     description=descr,
    #     scale=30,
    #     crs='EPSG:3857',
    #     maxPixels=1e13)
    #     task.start()


def modis_timeseries(
    asset_id="MODIS/006/MOD13A2",
    band_name=None,
    roi=None,
    start_year=2001,
    end_year=2021,
    start_date="01-01",
    end_date="12-31",
):
    """Generates a Monthly MODIS ImageCollection.
    Args:
        asset_id (str, optional): The asset id the MODIS ImageCollection.
        band_name (str, optional): The band name of the image to use.
        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 1984.
        end_year (int, optional): Ending year for the timelapse. Defaults to 2020.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '06-10'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '09-20'.
    Returns:
        object: Returns an ImageCollection containing month MODIS images.
    """

    try:
        collection = ee.ImageCollection(asset_id)
        if band_name is None:
            band_name = collection.first().bandNames().getInfo()[0]
        collection = collection.select(band_name)
        if roi is not None:
            if isinstance(roi, ee.Geometry):
                collection = ee.ImageCollection(
                    collection.map(lambda img: img.clip(roi))
                )
            elif isinstance(roi, ee.FeatureCollection):
                collection = ee.ImageCollection(
                    collection.map(lambda img: img.clipToCollection(roi))
                )

        start = str(start_year) + "-" + start_date
        end = str(end_year) + "-" + end_date

        seq = date_sequence(start, end, "month")

        def monthly_modis(start_d):

            end_d = ee.Date(start_d).advance(1, "month")
            return ee.Image(collection.filterDate(start_d, end_d).mean())

        images = ee.ImageCollection(seq.map(monthly_modis))
        return images

    except Exception as e:
        raise Exception(e)


def landsat_timelapse(
    roi=None,
    out_gif=None,
    start_year=1984,
    end_year=2021,
    start_date="06-10",
    end_date="09-20",
    bands=["NIR", "Red", "Green"],
    vis_params=None,
    dimensions=768,
    frames_per_second=5,
    crs="EPSG:3857",
    apply_fmask=True,
    nd_bands=None,
    nd_threshold=0,
    nd_palette=["black", "blue"],
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
    frequency="year",
    date_format=None,
    title=None,
    title_xy=("2%", "90%"),
    add_text=True,
    text_xy=("2%", "2%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="white",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    loop=0,
    mp4=False,
):
    """Generates a Landsat timelapse GIF image. This function is adapted from https://emaprlab.users.earthengine.app/view/lt-gee-time-series-animator. A huge thank you to Justin Braaten for sharing his fantastic work.

    Args:
        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        out_gif (str, optional): File path to the output animated GIF. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 1984.
        end_year (int, optional): Ending year for the timelapse. Defaults to 2021.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '06-10'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '09-20'.
        bands (list, optional): Three bands selected from ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']. Defaults to ['NIR', 'Red', 'Green'].
        vis_params (dict, optional): Visualization parameters. Defaults to None.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 5.
        crs (str, optional): The coordinate reference system to use. Defaults to "EPSG:3857".
        apply_fmask (bool, optional): Whether to apply Fmask (Function of mask) for automated clouds, cloud shadows, snow, and water masking.
        nd_bands (list, optional): A list of names specifying the bands to use, e.g., ['Green', 'SWIR1']. The normalized difference is computed as (first − second) / (first + second). Note that negative input values are forced to 0 so that the result is confined to the range (-1, 1).
        nd_threshold (float, optional): The threshold for extacting pixels from the normalized difference band.
        nd_palette (list, optional): The color palette to use for displaying the normalized difference band.
        overlay_data (int, str, list, optional): Administrative boundary to be drawn on the timelapse. Defaults to None.
        overlay_color (str, optional): Color for the overlay data. Can be any color name or hex color code. Defaults to 'black'.
        overlay_width (int, optional): Line width of the overlay. Defaults to 1.
        overlay_opacity (float, optional): Opacity of the overlay. Defaults to 1.0.
        frequency (str, optional): Frequency of the timelapse. Defaults to 'year'.
        date_format (str, optional): Date format for the timelapse. Defaults to None.
        title (str, optional): The title of the timelapse. Defaults to None.
        title_xy (tuple, optional): Lower left corner of the title. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        add_text (bool, optional): Whether to add animated text to the timelapse. Defaults to True.
        title_xy (tuple, optional): Lower left corner of the text sequency. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        text_sequence (int, str, list, optional): Text to be drawn. It can be an integer number, a string, or a list of strings. Defaults to None.
        font_type (str, optional): Font type. Defaults to "arial.ttf".
        font_size (int, optional): Font size. Defaults to 20.
        font_color (str, optional): Font color. It can be a string (e.g., 'red'), rgb tuple (e.g., (255, 127, 0)), or hex code (e.g., '#ff00ff').  Defaults to '#000000'.
        add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
        loop (int, optional): Controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.
        mp4 (bool, optional): Whether to convert the GIF to MP4. Defaults to False.

    Returns:
        str: File path to the output GIF image.
    """

    if roi is None:
        roi = ee.Geometry.Polygon(
            [
                [
                    [-115.471773, 35.892718],
                    [-115.471773, 36.409454],
                    [-114.271283, 36.409454],
                    [-114.271283, 35.892718],
                    [-115.471773, 35.892718],
                ]
            ],
            None,
            False,
        )
    elif isinstance(roi, ee.Feature) or isinstance(roi, ee.FeatureCollection):
        roi = roi.geometry()
    elif isinstance(roi, ee.Geometry):
        pass
    else:
        raise ValueError("The provided roi is invalid. It must be an ee.Geometry")

    if out_gif is None:
        out_gif = temp_file_path(".gif")
    elif not out_gif.endswith(".gif"):
        raise ValueError("The output file must end with .gif")
    else:
        out_gif = os.path.abspath(out_gif)
    out_dir = os.path.dirname(out_gif)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    allowed_bands = ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "pixel_qa"]

    if len(bands) == 3 and all(x in allowed_bands for x in bands):
        pass
    else:
        raise Exception(
            "You can only select 3 bands from the following: {}".format(
                ", ".join(allowed_bands)
            )
        )

    if nd_bands is not None:
        if len(nd_bands) == 2 and all(x in allowed_bands[:-1] for x in nd_bands):
            pass
        else:
            raise Exception(
                "You can only select two bands from the following: {}".format(
                    ", ".join(allowed_bands[:-1])
                )
            )

    try:

        if vis_params is None:
            vis_params = {}
            vis_params["bands"] = bands
            vis_params["min"] = 0
            vis_params["max"] = 4000
            vis_params["gamma"] = [1, 1, 1]
        raw_col = landsat_timeseries(
            roi,
            start_year,
            end_year,
            start_date,
            end_date,
            apply_fmask,
            frequency,
            date_format,
        )

        col = raw_col.select(bands).map(
            lambda img: img.visualize(**vis_params).set(
                {
                    "system:time_start": img.get("system:time_start"),
                    "system:date": img.get("system:date"),
                }
            )
        )
        if overlay_data is not None:
            col = add_overlay(
                col, overlay_data, overlay_color, overlay_width, overlay_opacity
            )

        if dimensions > 768:
            count = col.size().getInfo()
            basename = os.path.basename(out_gif)[:-4]
            names = [
                os.path.join(
                    out_dir, f"{basename}_{str(i+1).zfill(int(len(str(count))))}.jpg"
                )
                for i in range(count)
            ]
            get_image_collection_thumbnails(
                col,
                out_dir,
                vis_params={
                    "min": 0,
                    "max": 255,
                    "bands": ["vis-red", "vis-green", "vis-blue"],
                },
                dimensions=dimensions,
                names=names,
            )
            make_gif(
                names,
                out_gif,
                fps=frames_per_second,
                loop=loop,
                mp4=False,
                clean_up=True,
            )

        else:
            video_args = vis_params.copy()
            video_args["dimensions"] = dimensions
            video_args["region"] = roi
            video_args["framesPerSecond"] = frames_per_second
            video_args["crs"] = crs
            video_args["bands"] = ["vis-red", "vis-green", "vis-blue"]
            video_args["min"] = 0
            video_args["max"] = 255

            download_ee_video(col, video_args, out_gif)

        if os.path.exists(out_gif):

            if title is not None and isinstance(title, str):
                add_text_to_gif(
                    out_gif,
                    out_gif,
                    xy=title_xy,
                    text_sequence=title,
                    font_type=font_type,
                    font_size=font_size,
                    font_color=font_color,
                    add_progress_bar=add_progress_bar,
                    progress_bar_color=progress_bar_color,
                    progress_bar_height=progress_bar_height,
                    duration=1000 / frames_per_second,
                    loop=loop,
                )
            if add_text:
                if text_sequence is None:
                    text_sequence = col.aggregate_array("system:date").getInfo()
                add_text_to_gif(
                    out_gif,
                    out_gif,
                    xy=text_xy,
                    text_sequence=text_sequence,
                    font_type=font_type,
                    font_size=font_size,
                    font_color=font_color,
                    add_progress_bar=add_progress_bar,
                    progress_bar_color=progress_bar_color,
                    progress_bar_height=progress_bar_height,
                    duration=1000 / frames_per_second,
                    loop=loop,
                )

        if nd_bands is not None:
            nd_images = landsat_ts_norm_diff(
                raw_col, bands=nd_bands, threshold=nd_threshold
            )
            out_nd_gif = out_gif.replace(".gif", "_nd.gif")
            landsat_ts_norm_diff_gif(
                nd_images,
                out_gif=out_nd_gif,
                vis_params=None,
                palette=nd_palette,
                dimensions=dimensions,
                frames_per_second=frames_per_second,
            )

        if os.path.exists(out_gif):
            reduce_gif_size(out_gif)

        if mp4:
            out_mp4 = out_gif.replace(".gif", ".mp4")
            gif_to_mp4(out_gif, out_mp4)

        return out_gif

    except Exception as e:
        raise Exception(e)


def sentinel2_timelapse(
    roi=None,
    out_gif=None,
    start_year=2015,
    end_year=2021,
    start_date="06-10",
    end_date="09-20",
    bands=["NIR", "Red", "Green"],
    vis_params=None,
    dimensions=768,
    frames_per_second=5,
    crs="EPSG:3857",
    apply_fmask=True,
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
    frequency="year",
    date_format=None,
    title=None,
    title_xy=("2%", "90%"),
    add_text=True,
    text_xy=("2%", "2%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="white",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    loop=0,
    mp4=False,
):
    """Generates a Sentinel-2 timelapse GIF image. This function is adapted from https://emaprlab.users.earthengine.app/view/lt-gee-time-series-animator. A huge thank you to Justin Braaten for sharing his fantastic work.

    Args:
        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        out_gif (str, optional): File path to the output animated GIF. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 2015.
        end_year (int, optional): Ending year for the timelapse. Defaults to 2021.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '06-10'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '09-20'.
        bands (list, optional): Three bands selected from ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2', 'Red Edge 1', 'Red Edge 2', 'Red Edge 3', 'Red Edge 4']. Defaults to ['NIR', 'Red', 'Green'].
        vis_params (dict, optional): Visualization parameters. Defaults to None.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.
        crs (str, optional): Coordinate reference system. Defaults to 'EPSG:3857'.
        apply_fmask (bool, optional): Whether to apply Fmask (Function of mask) for automated clouds, cloud shadows, snow, and water masking.
        overlay_data (int, str, list, optional): Administrative boundary to be drawn on the timelapse. Defaults to None.
        overlay_color (str, optional): Color for the overlay data. Can be any color name or hex color code. Defaults to 'black'.
        overlay_width (int, optional): Line width of the overlay. Defaults to 1.
        overlay_opacity (float, optional): Opacity of the overlay. Defaults to 1.0.
        frequency (str, optional): Frequency of the timelapse. Defaults to 'year'.
        date_format (str, optional): Date format for the timelapse. Defaults to None.
        title (str, optional): The title of the timelapse. Defaults to None.
        title_xy (tuple, optional): Lower left corner of the title. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        add_text (bool, optional): Whether to add animated text to the timelapse. Defaults to True.
        title_xy (tuple, optional): Lower left corner of the text sequency. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        text_sequence (int, str, list, optional): Text to be drawn. It can be an integer number, a string, or a list of strings. Defaults to None.
        font_type (str, optional): Font type. Defaults to "arial.ttf".
        font_size (int, optional): Font size. Defaults to 20.
        font_color (str, optional): Font color. It can be a string (e.g., 'red'), rgb tuple (e.g., (255, 127, 0)), or hex code (e.g., '#ff00ff').  Defaults to '#000000'.
        add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
        loop (int, optional): Controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.
        mp4 (bool, optional): Whether to convert the GIF to MP4. Defaults to False.

    Returns:
        str: File path to the output GIF image.
    """

    if roi is None:
        roi = ee.Geometry.Polygon(
            [
                [
                    [-115.471773, 35.892718],
                    [-115.471773, 36.409454],
                    [-114.271283, 36.409454],
                    [-114.271283, 35.892718],
                    [-115.471773, 35.892718],
                ]
            ],
            None,
            False,
        )
    elif isinstance(roi, ee.Feature) or isinstance(roi, ee.FeatureCollection):
        roi = roi.geometry()
    elif isinstance(roi, ee.Geometry):
        pass
    else:
        print("The provided roi is invalid. It must be an ee.Geometry")
        return

    if out_gif is None:
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        filename = "s2_ts_" + random_string() + ".gif"
        out_gif = os.path.join(out_dir, filename)
    elif not out_gif.endswith(".gif"):
        print("The output file must end with .gif")
        return
    else:
        out_gif = os.path.abspath(out_gif)
        out_dir = os.path.dirname(out_gif)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    allowed_bands = [
        "Blue",
        "Green",
        "Red",
        "Red Edge 1",
        "Red Edge 2",
        "Red Edge 3",
        "NIR",
        "Red Edge 4",
        "SWIR1",
        "SWIR2",
        "QA60",
    ]

    if len(bands) == 3 and all(x in allowed_bands for x in bands):
        pass
    else:
        raise Exception(
            "You can only select 3 bands from the following: {}".format(
                ", ".join(allowed_bands)
            )
        )

    try:

        if vis_params is None:
            vis_params = {}
            vis_params["bands"] = bands
            vis_params["min"] = 0
            vis_params["max"] = 4000
            vis_params["gamma"] = [1, 1, 1]
        col = sentinel2_timeseries(
            roi,
            start_year,
            end_year,
            start_date,
            end_date,
            apply_fmask,
            frequency,
            date_format,
        )

        col = col.select(bands).map(
            lambda img: img.visualize(**vis_params).set(
                {
                    "system:time_start": img.get("system:time_start"),
                    "system:date": img.get("system:date"),
                }
            )
        )
        if overlay_data is not None:
            col = add_overlay(
                col, overlay_data, overlay_color, overlay_width, overlay_opacity
            )

        if dimensions > 768:
            count = col.size().getInfo()
            basename = os.path.basename(out_gif)[:-4]
            names = [
                os.path.join(
                    out_dir, f"{basename}_{str(i+1).zfill(int(len(str(count))))}.jpg"
                )
                for i in range(count)
            ]
            get_image_collection_thumbnails(
                col,
                out_dir,
                vis_params={
                    "min": 0,
                    "max": 255,
                    "bands": ["vis-red", "vis-green", "vis-blue"],
                },
                dimensions=dimensions,
                names=names,
            )
            make_gif(
                names,
                out_gif,
                fps=frames_per_second,
                loop=loop,
                mp4=False,
                clean_up=True,
            )
        else:

            video_args = vis_params.copy()
            video_args["dimensions"] = dimensions
            video_args["region"] = roi
            video_args["framesPerSecond"] = frames_per_second
            video_args["crs"] = crs
            video_args["bands"] = ["vis-red", "vis-green", "vis-blue"]
            video_args["min"] = 0
            video_args["max"] = 255

            download_ee_video(col, video_args, out_gif)

        if os.path.exists(out_gif):
            if title is not None and isinstance(title, str):
                add_text_to_gif(
                    out_gif,
                    out_gif,
                    xy=title_xy,
                    text_sequence=title,
                    font_type=font_type,
                    font_size=font_size,
                    font_color=font_color,
                    add_progress_bar=add_progress_bar,
                    progress_bar_color=progress_bar_color,
                    progress_bar_height=progress_bar_height,
                    duration=1000 / frames_per_second,
                    loop=loop,
                )
            if add_text:
                if text_sequence is None:
                    text_sequence = col.aggregate_array("system:date").getInfo()
                add_text_to_gif(
                    out_gif,
                    out_gif,
                    xy=text_xy,
                    text_sequence=text_sequence,
                    font_type=font_type,
                    font_size=font_size,
                    font_color=font_color,
                    add_progress_bar=add_progress_bar,
                    progress_bar_color=progress_bar_color,
                    progress_bar_height=progress_bar_height,
                    duration=1000 / frames_per_second,
                    loop=loop,
                )

        if os.path.exists(out_gif):
            reduce_gif_size(out_gif)

        if mp4:
            out_mp4 = out_gif.replace(".gif", ".mp4")
            gif_to_mp4(out_gif, out_mp4)

        return out_gif

    except Exception as e:
        print(e)


def landsat_ts_norm_diff(collection, bands=["Green", "SWIR1"], threshold=0):
    """Computes a normalized difference index based on a Landsat timeseries.

    Args:
        collection (ee.ImageCollection): A Landsat timeseries.
        bands (list, optional): The bands to use for computing normalized difference. Defaults to ['Green', 'SWIR1'].
        threshold (float, optional): The threshold to extract features. Defaults to 0.

    Returns:
        ee.ImageCollection: An ImageCollection containing images with values greater than the specified threshold.
    """
    nd_images = collection.map(
        lambda img: img.normalizedDifference(bands)
        .gt(threshold)
        .copyProperties(img, img.propertyNames())
    )
    return nd_images


def landsat_ts_norm_diff_gif(
    collection,
    out_gif=None,
    vis_params=None,
    palette=["black", "blue"],
    dimensions=768,
    frames_per_second=10,
    mp4=False,
):
    """[summary]

    Args:
        collection (ee.ImageCollection): The normalized difference Landsat timeseires.
        out_gif (str, optional): File path to the output animated GIF. Defaults to None.
        vis_params (dict, optional): Visualization parameters. Defaults to None.
        palette (list, optional): The palette to use for visualizing the timelapse. Defaults to ['black', 'blue']. The first color in the list is the background color.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.
        mp4 (bool, optional): If True, the output gif will be converted to mp4. Defaults to False.

    Returns:
        str: File path to the output animated GIF.
    """
    coordinates = ee.Image(collection.first()).get("coordinates")
    roi = ee.Geometry.Polygon(coordinates, None, False)

    if out_gif is None:
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        filename = "landsat_ts_nd_" + random_string() + ".gif"
        out_gif = os.path.join(out_dir, filename)
    elif not out_gif.endswith(".gif"):
        raise Exception("The output file must end with .gif")

    bands = ["nd"]
    if vis_params is None:
        vis_params = {}
        vis_params["bands"] = bands
        vis_params["palette"] = palette

    video_args = vis_params.copy()
    video_args["dimensions"] = dimensions
    video_args["region"] = roi
    video_args["framesPerSecond"] = frames_per_second
    video_args["crs"] = "EPSG:3857"

    if "bands" not in video_args.keys():
        video_args["bands"] = bands

    download_ee_video(collection, video_args, out_gif)

    if os.path.exists(out_gif):
        reduce_gif_size(out_gif)

    if mp4:
        out_mp4 = out_gif.replace(".gif", ".mp4")
        gif_to_mp4(out_gif, out_mp4)


def goes_timeseries(
    start_date="2021-10-24T14:00:00",
    end_date="2021-10-25T01:00:00",
    data="GOES-17",
    scan="full_disk",
    region=None,
    show_night=[False, "a_mode"],
):
    """Create a time series of GOES data. The code is adapted from Justin Braaten's code: https://code.earthengine.google.com/57245f2d3d04233765c42fb5ef19c1f4.
    Credits to Justin Braaten. See also https://jstnbraaten.medium.com/goes-in-earth-engine-53fbc8783c16

    Args:
        start_date (str, optional): The start date of the time series. Defaults to "2021-10-24T14:00:00".
        end_date (str, optional): The end date of the time series. Defaults to "2021-10-25T01:00:00".
        data (str, optional): The GOES satellite data to use. Defaults to "GOES-17".
        scan (str, optional): The GOES scan to use. Defaults to "full_disk".
        region (ee.Geometry, optional): The region of interest. Defaults to None.
        show_night (list, optional): Show the clouds at night through [True, "a_mode"] o [True, "b_mode"].  Defaults to [False, "a_mode"]
    Raises:
        ValueError: The data must be either GOES-16 or GOES-17.
        ValueError: The scan must be either full_disk, conus, or mesoscale.

    Returns:
        ee.ImageCollection: GOES timeseries.
    """

    if data not in ["GOES-16", "GOES-17"]:
        raise ValueError("The data must be either GOES-16 or GOES-17.")

    if scan.lower() not in ["full_disk", "conus", "mesoscale"]:
        raise ValueError("The scan must be either full_disk, conus, or mesoscale.")

    scan_types = {
        "full_disk": "MCMIPF",
        "conus": "MCMIPC",
        "mesoscale": "MCMIPM",
    }

    col = ee.ImageCollection(f"NOAA/GOES/{data[-2:]}/{scan_types[scan.lower()]}")

    if region is None:
        region = ee.Geometry.Polygon(
            [
                [
                    [-159.5954379282731, 60.40883060191719],
                    [-159.5954379282731, 24.517881970830725],
                    [-114.2438754282731, 24.517881970830725],
                    [-114.2438754282731, 60.40883060191719],
                ]
            ],
            None,
            False,
        )

    # Applies scaling factors.
    def applyScaleAndOffset(img):
        def getFactorImg(factorNames):
            factorList = img.toDictionary().select(factorNames).values()
            return ee.Image.constant(factorList)

        scaleImg = getFactorImg(["CMI_C.._scale"])
        offsetImg = getFactorImg(["CMI_C.._offset"])
        scaled = img.select("CMI_C..").multiply(scaleImg).add(offsetImg)
        return img.addBands(**{"srcImg": scaled, "overwrite": True})

    # Adds a synthetic green band.
    def addGreenBand(img):
        green = img.expression(
            "CMI_GREEN = 0.45 * red + 0.10 * nir + 0.45 * blue",
            {
                "blue": img.select("CMI_C01"),
                "red": img.select("CMI_C02"),
                "nir": img.select("CMI_C03"),
            },
        )
        return img.addBands(green)

    # Show at clouds at night (a-mode)
    def showNighta(img):
        # Make normalized infrared
        IR_n = img.select('CMI_C13').unitScale(ee.Number(90), ee.Number(313))
        IR_n = IR_n.expression(
            "ir_p = (1 -IR_n)/1.4",
            {
                "IR_n": IR_n.select('CMI_C13'),
            },
        )

        # Add infrared to rgb bands
        R_ir = img.select('CMI_C02').max(IR_n)
        G_ir = img.select('CMI_GREEN').max(IR_n)
        B_ir = img.select('CMI_C01').max(IR_n)

        return img.addBands([R_ir, G_ir, B_ir], overwrite=True)

    # Show at clouds at night (b-mode)
    def showNightb(img):
        night = img.select('CMI_C03').unitScale(0, 0.016).subtract(1).multiply(-1)

        cmi11 = img.select('CMI_C11').unitScale(100, 310)
        cmi13 = img.select('CMI_C13').unitScale(100, 300)
        cmi15 = img.select('CMI_C15').unitScale(100, 310)
        iNight = cmi15.addBands([cmi13, cmi11]).clamp(0, 1).subtract(1).multiply(-1)

        iRGBNight = iNight.visualize(
            **{"min": 0, "max": 1, "gamma": 1.4}).updateMask(night)

        iRGB = img.visualize(
            **{"bands": ['CMI_C02', 'CMI_C03', 'CMI_C01'], "min": 0.15, "max": 1, "gamma": 1.4})
        return iRGB.blend(iRGBNight).set("system:time_start", img.get("system:time_start"))

    # Scales select bands for visualization.
    def scaleForVis(img):
        return (
            img.select(["CMI_C01", "CMI_GREEN", "CMI_C02", "CMI_C03", "CMI_C05"])
            .resample("bicubic")
            .log10()
            .interpolate([-1.6, 0.176], [0, 1], "clamp")
            .unmask(0)
            .set("system:time_start", img.get("system:time_start"))
        )

    # Wraps previous functions.
    def processForVis(img):
        if show_night[0]:
            if show_night[1] == "a_mode":
                return scaleForVis(showNighta(addGreenBand(applyScaleAndOffset(img))))

            else:
                return showNightb(applyScaleAndOffset(img))

        else:
            return scaleForVis(addGreenBand(applyScaleAndOffset(img)))

    return col.filterDate(start_date, end_date).map(processForVis)


def goes_fire_timeseries(
    start_date="2020-09-05T15:00",
    end_date="2020-09-06T02:00",
    data="GOES-17",
    scan="full_disk",
    region=None,
    merge=True,
):
    """Create a time series of GOES Fire data. The code is adapted from Justin Braaten's code: https://code.earthengine.google.com/8a083a7fb13b95ad4ba148ed9b65475e.
    Credits to Justin Braaten. See also https://jstnbraaten.medium.com/goes-in-earth-engine-53fbc8783c16

    Args:
        start_date (str, optional): The start date of the time series. Defaults to "2020-09-05T15:00".
        end_date (str, optional): The end date of the time series. Defaults to "2020-09-06T02:00".
        data (str, optional): The GOES satellite data to use. Defaults to "GOES-17".
        scan (str, optional): The GOES scan to use. Defaults to "full_disk".
        region (ee.Geometry, optional): The region of interest. Defaults to None.
        merge (bool, optional): Whether to merge the fire timeseries with GOES CMI timeseries. Defaults to True.

    Raises:
        ValueError: The data must be either GOES-16 or GOES-17.
        ValueError: The scan must be either full_disk or conus.

    Returns:
        ee.ImageCollection: GOES fire timeseries.
    """

    if data not in ["GOES-16", "GOES-17"]:
        raise ValueError("The data must be either GOES-16 or GOES-17.")

    if scan.lower() not in ["full_disk", "conus"]:
        raise ValueError("The scan must be either full_disk or conus.")

    scan_types = {
        "full_disk": "FDCF",
        "conus": "FDCC",
    }

    if region is None:
        region = ee.Geometry.BBox(-123.17, 36.56, -118.22, 40.03)

    # Get the fire/hotspot characterization dataset.
    col = ee.ImageCollection(f"NOAA/GOES/{data[-2:]}/{scan_types[scan.lower()]}")
    fdcCol = col.filterDate(start_date, end_date)

    # Identify fire-detected pixels of medium to high confidence.
    fireMaskCodes = [10, 30, 11, 31, 12, 32, 13, 33, 14, 34, 15, 35]
    confVals = [1.0, 1.0, 0.9, 0.9, 0.8, 0.8, 0.5, 0.5, 0.3, 0.3, 0.1, 0.1]
    defaultConfVal = 0

    def fdcVis(img):
        confImg = img.remap(fireMaskCodes, confVals, defaultConfVal, "Mask")
        return (
            confImg.gte(0.3)
            .selfMask()
            .set("system:time_start", img.get("system:time_start"))
        )

    fdcVisCol = fdcCol.map(fdcVis)
    if not merge:
        return fdcVisCol
    else:
        geosVisCol = goes_timeseries(start_date, end_date, data, scan, region)
        # Join the fire collection to the CMI collection.
        joinFilter = ee.Filter.equals(
            **{"leftField": "system:time_start", "rightField": "system:time_start"}
        )
        joinedCol = ee.Join.saveFirst("match").apply(geosVisCol, fdcVisCol, joinFilter)

        def overlayVis(img):
            cmi = ee.Image(img).visualize(
                **{
                    "bands": ["CMI_C02", "CMI_GREEN", "CMI_C01"],
                    "min": 0,
                    "max": 0.8,
                    "gamma": 0.8,
                }
            )
            fdc = ee.Image(img.get("match")).visualize(
                **{"palette": ["ff5349"], "min": 0, "max": 1, "opacity": 0.7}
            )
            return cmi.blend(fdc).set("system:time_start", img.get("system:time_start"))

        cmiFdcVisCol = ee.ImageCollection(joinedCol.map(overlayVis))
        return cmiFdcVisCol


def goes_timelapse(
    out_gif,
    start_date="2021-10-24T14:00:00",
    end_date="2021-10-25T01:00:00",
    data="GOES-17",
    scan="full_disk",
    region=None,
    dimensions=768,
    framesPerSecond=10,
    date_format="YYYY-MM-dd HH:mm",
    xy=("3%", "3%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="#ffffff",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    loop=0,
    crs=None,
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
    mp4=False,
    **kwargs,
):
    """Create a timelapse of GOES data. The code is adapted from Justin Braaten's code: https://code.earthengine.google.com/57245f2d3d04233765c42fb5ef19c1f4.
    Credits to Justin Braaten. See also https://jstnbraaten.medium.com/goes-in-earth-engine-53fbc8783c16

    Args:
        out_gif (str): The file path to save the gif.
        start_date (str, optional): The start date of the time series. Defaults to "2021-10-24T14:00:00".
        end_date (str, optional): The end date of the time series. Defaults to "2021-10-25T01:00:00".
        data (str, optional): The GOES satellite data to use. Defaults to "GOES-17".
        scan (str, optional): The GOES scan to use. Defaults to "full_disk".
        region (ee.Geometry, optional): The region of interest. Defaults to None.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.
        date_format (str, optional): The date format to use. Defaults to "YYYY-MM-dd HH:mm".
        xy (tuple, optional): Top left corner of the text. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        text_sequence (int, str, list, optional): Text to be drawn. It can be an integer number, a string, or a list of strings. Defaults to None.
        font_type (str, optional): Font type. Defaults to "arial.ttf".
        font_size (int, optional): Font size. Defaults to 20.
        font_color (str, optional): Font color. It can be a string (e.g., 'red'), rgb tuple (e.g., (255, 127, 0)), or hex code (e.g., '#ff00ff').  Defaults to '#000000'.
        add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.        loop (int, optional): controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.
        crs (str, optional): The coordinate reference system to use, e.g., "EPSG:3857". Defaults to None.
        overlay_data (int, str, list, optional): Administrative boundary to be drawn on the timelapse. Defaults to None.
        overlay_color (str, optional): Color for the overlay data. Can be any color name or hex color code. Defaults to 'black'.
        overlay_width (int, optional): Line width of the overlay. Defaults to 1.
        overlay_opacity (float, optional): Opacity of the overlay. Defaults to 1.0.
        mp4 (bool, optional): Whether to save the animation as an mp4 file. Defaults to False.
    Raises:
        Exception: Raise exception.
    """

    try:

        bands = ["CMI_C02", "CMI_GREEN", "CMI_C01"]
        visParams = {
            "bands": bands,
            "min": 0,
            "max": 0.8,
        }
        col = goes_timeseries(start_date, end_date, data, scan, region)
        col = col.select(bands).map(
            lambda img: img.visualize(**visParams).set(
                {
                    "system:time_start": img.get("system:time_start"),
                }
            )
        )
        if overlay_data is not None:
            col = add_overlay(
                col, overlay_data, overlay_color, overlay_width, overlay_opacity
            )

        if region is None:
            region = ee.Geometry.Polygon(
                [
                    [
                        [-159.5954, 60.4088],
                        [-159.5954, 24.5178],
                        [-114.2438, 24.5178],
                        [-114.2438, 60.4088],
                    ]
                ],
                None,
                False,
            )

        if crs is None:
            crs = col.first().projection()

        videoParams = {
            "bands": ["vis-red", "vis-green", "vis-blue"],
            "min": 0,
            "max": 255,
            "dimensions": dimensions,
            "framesPerSecond": framesPerSecond,
            "region": region,
            "crs": crs,
        }

        if text_sequence is None:
            text_sequence = image_dates(col, date_format=date_format).getInfo()

        download_ee_video(col, videoParams, out_gif)

        if os.path.exists(out_gif):

            add_text_to_gif(
                out_gif,
                out_gif,
                xy,
                text_sequence,
                font_type,
                font_size,
                font_color,
                add_progress_bar,
                progress_bar_color,
                progress_bar_height,
                duration=1000 / framesPerSecond,
                loop=loop,
            )

            try:
                reduce_gif_size(out_gif)
            except Exception as _:
                pass

            if mp4:
                out_mp4 = out_gif.replace(".gif", ".mp4")
                gif_to_mp4(out_gif, out_mp4)

    except Exception as e:
        raise Exception(e)


def goes_fire_timelapse(
    out_gif,
    start_date="2020-09-05T15:00",
    end_date="2020-09-06T02:00",
    data="GOES-17",
    scan="full_disk",
    region=None,
    dimensions=768,
    framesPerSecond=10,
    date_format="YYYY-MM-dd HH:mm",
    xy=("3%", "3%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="#ffffff",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    loop=0,
    crs=None,
    overlay_data=None,
    overlay_color="#000000",
    overlay_width=1,
    overlay_opacity=1.0,
    mp4=False,
    **kwargs,
):
    """Create a timelapse of GOES fire data. The code is adapted from Justin Braaten's code: https://code.earthengine.google.com/8a083a7fb13b95ad4ba148ed9b65475e.
    Credits to Justin Braaten. See also https://jstnbraaten.medium.com/goes-in-earth-engine-53fbc8783c16

    Args:
        out_gif (str): The file path to save the gif.
        start_date (str, optional): The start date of the time series. Defaults to "2021-10-24T14:00:00".
        end_date (str, optional): The end date of the time series. Defaults to "2021-10-25T01:00:00".
        data (str, optional): The GOES satellite data to use. Defaults to "GOES-17".
        scan (str, optional): The GOES scan to use. Defaults to "full_disk".
        region (ee.Geometry, optional): The region of interest. Defaults to None.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.
        date_format (str, optional): The date format to use. Defaults to "YYYY-MM-dd HH:mm".
        xy (tuple, optional): Top left corner of the text. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        text_sequence (int, str, list, optional): Text to be drawn. It can be an integer number, a string, or a list of strings. Defaults to None.
        font_type (str, optional): Font type. Defaults to "arial.ttf".
        font_size (int, optional): Font size. Defaults to 20.
        font_color (str, optional): Font color. It can be a string (e.g., 'red'), rgb tuple (e.g., (255, 127, 0)), or hex code (e.g., '#ff00ff').  Defaults to '#000000'.
        add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
        loop (int, optional): controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.
        crs (str, optional): The coordinate reference system to use, e.g., "EPSG:3857". Defaults to None.
        overlay_data (int, str, list, optional): Administrative boundary to be drawn on the timelapse. Defaults to None.
        overlay_color (str, optional): Color for the overlay data. Can be any color name or hex color code. Defaults to 'black'.
        overlay_width (int, optional): Width of the overlay. Defaults to 1.
        overlay_opacity (float, optional): Opacity of the overlay. Defaults to 1.0.
        mp4 (bool, optional): Whether to convert the GIF to MP4. Defaults to False.

    Raises:
        Exception: Raise exception.
    """

    try:

        if region is None:
            region = ee.Geometry.BBox(-123.17, 36.56, -118.22, 40.03)

        col = goes_fire_timeseries(start_date, end_date, data, scan, region)
        if overlay_data is not None:
            col = add_overlay(
                col, overlay_data, overlay_color, overlay_width, overlay_opacity
            )

        # visParams = {
        #     "bands": ["CMI_C02", "CMI_GREEN", "CMI_C01"],
        #     "min": 0,
        #     "max": 0.8,
        #     "dimensions": dimensions,
        #     "framesPerSecond": framesPerSecond,
        #     "region": region,
        #     "crs": col.first().projection(),
        # }

        if crs is None:
            crs = col.first().projection()

        cmiFdcVisParams = {
            "dimensions": dimensions,
            "framesPerSecond": framesPerSecond,
            "region": region,
            "crs": crs,
        }

        if text_sequence is None:
            text_sequence = image_dates(col, date_format=date_format).getInfo()

        download_ee_video(col, cmiFdcVisParams, out_gif)

        if os.path.exists(out_gif):

            add_text_to_gif(
                out_gif,
                out_gif,
                xy,
                text_sequence,
                font_type,
                font_size,
                font_color,
                add_progress_bar,
                progress_bar_color,
                progress_bar_height,
                duration=1000 / framesPerSecond,
                loop=loop,
            )

            try:
                reduce_gif_size(out_gif)
            except Exception as _:
                pass

            if mp4:
                out_mp4 = out_gif.replace(".gif", ".mp4")
                gif_to_mp4(out_gif, out_mp4)

    except Exception as e:
        raise Exception(e)


def modis_ndvi_doy_ts(
    data="Terra", band="NDVI", start_date=None, end_date=None, region=None
):
    """Create MODIS NDVI timeseries. The source code is adapted from https://developers.google.com/earth-engine/tutorials/community/modis-ndvi-time-series-animation.

    Args:
        data (str, optional): Either "Terra" or "Aqua". Defaults to "Terra".
        band (str, optional): Either the "NDVI" or "EVI" band. Defaults to "NDVI".
        start_date (str, optional): The start date used to filter the image collection, e.g., "2013-01-01". Defaults to None.
        end_date (str, optional): The end date used to filter the image collection. Defaults to None.
        region (ee.Geometry, optional): The geometry used to filter the image collection. Defaults to None.

    Returns:
        ee.ImageCollection: The MODIS NDVI time series.
    """
    if data not in ["Terra", "Aqua"]:
        raise Exception("data must be 'Terra' or 'Aqua'.")

    if band not in ["NDVI", "EVI"]:
        raise Exception("band must be 'NDVI' or 'EVI'.")

    if region is not None:
        if isinstance(region, ee.Geometry) or isinstance(region, ee.FeatureCollection):
            pass
        else:
            raise Exception("region must be an ee.Geometry or ee.FeatureCollection.")

    if data == "Terra":
        col = ee.ImageCollection("MODIS/006/MOD13A2").select(band)
    else:
        col = ee.ImageCollection("MODIS/006/MYD13A2").select(band)

    if (start_date is not None) and (end_date is not None):
        col = col.filterDate(start_date, end_date)

    def set_doy(img):
        doy = ee.Date(img.get("system:time_start")).getRelative("day", "year")
        return img.set("doy", doy)

    col = col.map(set_doy)

    # Get a collection of distinct images by 'doy'.
    distinctDOY = col.filterDate("2013-01-01", "2014-01-01")

    # Define a filter that identifies which images from the complete
    # collection match the DOY from the distinct DOY collection.
    filter = ee.Filter.equals(**{"leftField": "doy", "rightField": "doy"})

    # Define a join.
    join = ee.Join.saveAll("doy_matches")

    # Apply the join and convert the resulting FeatureCollection to an
    # ImageCollection.
    joinCol = ee.ImageCollection(join.apply(distinctDOY, col, filter))

    # Apply median reduction among matching DOY collections.

    def match_doy(img):
        doyCol = ee.ImageCollection.fromImages(img.get("doy_matches"))
        return doyCol.reduce(ee.Reducer.median())

    comp = joinCol.map(match_doy)

    if region is not None:
        return comp.map(lambda img: img.clip(region))
    else:
        return comp


def modis_ndvi_timelapse(
    out_gif,
    data="Terra",
    band="NDVI",
    start_date=None,
    end_date=None,
    region=None,
    dimensions=768,
    framesPerSecond=10,
    crs="EPSG:3857",
    xy=("3%", "3%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="#ffffff",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    loop=0,
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
    mp4=False,
    **kwargs,
):
    """Create MODIS NDVI timelapse. The source code is adapted from https://developers.google.com/earth-engine/tutorials/community/modis-ndvi-time-series-animation.

    Args:
        out_gif (str): The output gif file path.
        data (str, optional): Either "Terra" or "Aqua". Defaults to "Terra".
        band (str, optional): Either the "NDVI" or "EVI" band. Defaults to "NDVI".
        start_date (str, optional): The start date used to filter the image collection, e.g., "2013-01-01". Defaults to None.
        end_date (str, optional): The end date used to filter the image collection. Defaults to None.
        region (ee.Geometry, optional): The geometry used to filter the image collection. Defaults to None.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.
        crs (str, optional): The coordinate reference system to use. Defaults to "EPSG:3857".
        xy (tuple, optional): Top left corner of the text. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        text_sequence (int, str, list, optional): Text to be drawn. It can be an integer number, a string, or a list of strings. Defaults to None.
        font_type (str, optional): Font type. Defaults to "arial.ttf".
        font_size (int, optional): Font size. Defaults to 20.
        font_color (str, optional): Font color. It can be a string (e.g., 'red'), rgb tuple (e.g., (255, 127, 0)), or hex code (e.g., '#ff00ff').  Defaults to '#000000'.
        add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
        loop (int, optional): controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.
        overlay_data (int, str, list, optional): Administrative boundary to be drawn on the timelapse. Defaults to None.
        overlay_color (str, optional): Color for the overlay data. Can be any color name or hex color code. Defaults to 'black'.
        overlay_width (int, optional): Width of the overlay. Defaults to 1.
        overlay_opacity (float, optional): Opacity of the overlay. Defaults to 1.0.
        mp4 (bool, optional): Whether to convert the output gif to mp4. Defaults to False.

    """

    if region is None:
        region = ee.Geometry.Polygon(
            [
                [
                    [-18.6983, 38.1446],
                    [-18.6983, -36.1630],
                    [52.2293, -36.1630],
                    [52.2293, 38.1446],
                ]
            ],
            None,
            False,
        )

    try:
        col = modis_ndvi_doy_ts(data, band, start_date, end_date, region)

        # Define RGB visualization parameters.
        visParams = {
            "min": 0.0,
            "max": 9000.0,
            "palette": [
                "FFFFFF",
                "CE7E45",
                "DF923D",
                "F1B555",
                "FCD163",
                "99B718",
                "74A901",
                "66A000",
                "529400",
                "3E8601",
                "207401",
                "056201",
                "004C00",
                "023B01",
                "012E01",
                "011D01",
                "011301",
            ],
        }

        # Create RGB visualization images for use as animation frames.
        rgbVis = col.map(lambda img: img.visualize(**visParams).clip(region))

        if overlay_data is not None:
            rgbVis = add_overlay(
                rgbVis,
                overlay_data,
                overlay_color,
                overlay_width,
                overlay_opacity,
                region,
            )

        # Define GIF visualization arguments.
        videoArgs = {
            "region": region,
            "dimensions": dimensions,
            "crs": crs,
            "framesPerSecond": framesPerSecond,
        }

        download_ee_video(rgbVis, videoArgs, out_gif)

        if text_sequence is None:
            text = rgbVis.aggregate_array("system:index").getInfo()
            text_sequence = [d.replace("_", "-")[5:] for d in text]

        if os.path.exists(out_gif):

            add_text_to_gif(
                out_gif,
                out_gif,
                xy,
                text_sequence,
                font_type,
                font_size,
                font_color,
                add_progress_bar,
                progress_bar_color,
                progress_bar_height,
                duration=1000 / framesPerSecond,
                loop=loop,
            )

            try:
                reduce_gif_size(out_gif)
            except Exception as _:
                pass

        if mp4:
            out_mp4 = out_gif.replace(".gif", ".mp4")
            gif_to_mp4(out_gif, out_mp4)

    except Exception as e:
        raise Exception(e)


def modis_ocean_color_timeseries(
    satellite,
    start_date,
    end_date,
    region=None,
    bands=None,
    frequency="year",
    reducer="median",
    drop_empty=True,
    date_format=None,
):
    """Creates a ocean color timeseries from MODIS. https://developers.google.com/earth-engine/datasets/catalog/NASA_OCEANDATA_MODIS-Aqua_L3SMI

    Args:
        satellite (str): The satellite to use, can be either "Terra" or "Aqua".
        start_date (str): The start date of the timeseries. It must be formatted like this: 'YYYY-MM-dd'.
        end_date (str): The end date of the timeseries. It must be formatted like this: 'YYYY-MM-dd'.
        region (ee.Geometry, optional): The region to use to filter the collection of images. It must be an ee.Geometry object. Defaults to None.
        bands (list, optional): The list of bands to use to create the timeseries. It must be a list of strings. Defaults to None.
        frequency (str, optional): The frequency of the timeseries. It must be one of the following: 'year', 'month', 'day'. Defaults to 'year'.
        reducer (str, optional):  The reducer to use to reduce the collection of images to a single value. It can be one of the following: 'median', 'mean', 'min', 'max', 'variance', 'sum'. Defaults to 'median'.
        drop_empty (bool, optional): Whether to drop empty images from the timeseries. Defaults to True.
        date_format (str, optional): A pattern, as described at http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html. Defaults to 'YYYY-MM-dd'.

    Returns:
        ee.ImageCollection: The timeseries.
    """

    if satellite not in ["Terra", "Aqua"]:
        raise Exception("Satellite must be 'Terra' or 'Aqua'.")

    allowed_frequency = ["year", "quarter", "month", "week", "day"]
    if frequency not in allowed_frequency:
        raise Exception(
            "Frequency must be one of the following: {}".format(allowed_frequency)
        )

    if region is not None:
        if isinstance(region, ee.Geometry) or isinstance(region, ee.FeatureCollection):
            pass
        else:
            raise Exception("region must be an ee.Geometry or ee.FeatureCollection.")

    col = ee.ImageCollection(f"NASA/OCEANDATA/MODIS-{satellite}/L3SMI").filterDate(
        start_date, end_date
    )

    ts = create_timeseries(
        col,
        start_date,
        end_date,
        region,
        bands,
        frequency,
        reducer,
        drop_empty,
        date_format,
    )

    return ts


def modis_ocean_color_timelapse(
    satellite,
    start_date,
    end_date,
    region=None,
    bands=None,
    frequency="year",
    reducer="median",
    date_format=None,
    out_gif=None,
    palette="coolwarm",
    vis_params=None,
    dimensions=768,
    frames_per_second=5,
    crs="EPSG:3857",
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
    title=None,
    title_xy=("2%", "90%"),
    add_text=True,
    text_xy=("2%", "2%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="white",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    add_colorbar=True,
    colorbar_width=6.0,
    colorbar_height=0.4,
    colorbar_label="Sea Surface Temperature (°C)",
    colorbar_label_size=12,
    colorbar_label_weight="normal",
    colorbar_tick_size=10,
    colorbar_bg_color="white",
    colorbar_orientation="horizontal",
    colorbar_dpi="figure",
    colorbar_xy=None,
    colorbar_size=(300, 300),
    loop=0,
    mp4=False,
):
    """Creates a ocean color timelapse from MODIS. https://developers.google.com/earth-engine/datasets/catalog/NASA_OCEANDATA_MODIS-Aqua_L3SMI

    Args:
        satellite (str): The satellite to use, can be either "Terra" or "Aqua".
        start_date (str): The start date of the timeseries. It must be formatted like this: 'YYYY-MM-dd'.
        end_date (str): The end date of the timeseries. It must be formatted like this: 'YYYY-MM-dd'.
        region (ee.Geometry, optional): The region to use to filter the collection of images. It must be an ee.Geometry object. Defaults to None.
        bands (list, optional): A list of band names to use in the timelapse. Defaults to None.
        frequency (str, optional): The frequency of the timeseries. It must be one of the following: 'year', 'month', 'day', 'hour', 'minute', 'second'. Defaults to 'year'.
        reducer (str, optional):  The reducer to use to reduce the collection of images to a single value. It can be one of the following: 'median', 'mean', 'min', 'max', 'variance', 'sum'. Defaults to 'median'.
        drop_empty (bool, optional): Whether to drop empty images from the timeseries. Defaults to True.
        date_format (str, optional): A pattern, as described at http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html. Defaults to 'YYYY-MM-dd'.
        out_gif (str): The output gif file path. Defaults to None.
        palette (list, optional): A list of colors to render a single-band image in the timelapse. Defaults to None.
        vis_params (dict, optional): A dictionary of visualization parameters to use in the timelapse. Defaults to None. See more at https://developers.google.com/earth-engine/guides/image_visualization.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.
        crs (str, optional): The coordinate reference system to use. Defaults to "EPSG:3857".
        overlay_data (int, str, list, optional): Administrative boundary to be drawn on the timelapse. Defaults to None.
        overlay_color (str, optional): Color for the overlay data. Can be any color name or hex color code. Defaults to 'black'.
        overlay_width (int, optional): Width of the overlay. Defaults to 1.
        overlay_opacity (float, optional): Opacity of the overlay. Defaults to 1.0.
        title (str, optional): The title of the timelapse. Defaults to None.
        title_xy (tuple, optional): Lower left corner of the title. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        add_text (bool, optional): Whether to add animated text to the timelapse. Defaults to True.
        title_xy (tuple, optional): Lower left corner of the text sequency. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        text_sequence (int, str, list, optional): Text to be drawn. It can be an integer number, a string, or a list of strings. Defaults to None.
        font_type (str, optional): Font type. Defaults to "arial.ttf".
        font_size (int, optional): Font size. Defaults to 20.
        font_color (str, optional): Font color. It can be a string (e.g., 'red'), rgb tuple (e.g., (255, 127, 0)), or hex code (e.g., '#ff00ff').  Defaults to '#000000'.
        add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
        add_colorbar (bool, optional): Whether to add a colorbar to the timelapse. Defaults to False.
        colorbar_width (float, optional): Width of the colorbar. Defaults to 6.0.
        colorbar_height (float, optional): Height of the colorbar. Defaults to 0.4.
        colorbar_label (str, optional): Label for the colorbar. Defaults to None.
        colorbar_label_size (int, optional): Font size for the colorbar label. Defaults to 12.
        colorbar_label_weight (str, optional): Font weight for the colorbar label. Defaults to 'normal'.
        colorbar_tick_size (int, optional): Font size for the colorbar ticks. Defaults to 10.
        colorbar_bg_color (str, optional): Background color for the colorbar, can be color like "white", "black". Defaults to None.
        colorbar_orientation (str, optional): Orientation of the colorbar. Defaults to 'horizontal'.
        colorbar_dpi (str, optional): DPI for the colorbar, can be numbers like 100, 300. Defaults to 'figure'.
        colorbar_xy (tuple, optional): Lower left corner of the colorbar. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        colorbar_size (tuple, optional): Size of the colorbar. It can be formatted like this: (300, 300). Defaults to (300, 300).
        loop (int, optional): Controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.
        mp4 (bool, optional): Whether to create an mp4 file. Defaults to False.

    Returns:
        str: File path to the timelapse gif.
    """
    collection = modis_ocean_color_timeseries(
        satellite, start_date, end_date, region, bands, frequency, reducer, date_format
    )

    if bands is None:
        bands = ["sst"]

    if len(bands) == 1 and palette is None:
        palette = "coolwarm"

    if region is None:
        region = ee.Geometry.BBox(-99.755133, 18.316722, -79.761194, 31.206929)

    out_gif = create_timelapse(
        collection,
        start_date,
        end_date,
        region,
        bands,
        frequency,
        reducer,
        date_format,
        out_gif,
        palette,
        vis_params,
        dimensions,
        frames_per_second,
        crs,
        overlay_data,
        overlay_color,
        overlay_width,
        overlay_opacity,
        title,
        title_xy,
        add_text,
        text_xy,
        text_sequence,
        font_type,
        font_size,
        font_color,
        add_progress_bar,
        progress_bar_color,
        progress_bar_height,
        add_colorbar,
        colorbar_width,
        colorbar_height,
        colorbar_label,
        colorbar_label_size,
        colorbar_label_weight,
        colorbar_tick_size,
        colorbar_bg_color,
        colorbar_orientation,
        colorbar_dpi,
        colorbar_xy,
        colorbar_size,
        loop,
        mp4,
    )

    return out_gif
