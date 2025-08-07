import ee
import geoai
from .coreutils import *
import geedim as gd
import numpy as np
import rasterio
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import redirect_stdout, redirect_stderr
import os
import io
import tempfile
import logging
import warnings
import threading

def _detect_image(
    image,
    model_path,
    scale,
    segment_fn,  
    segment_args: dict,
    num_thread=None,
    bands=None,
    window_size=512,
    overlap=256,
    confidence_threshold=0.5,
    batch_size=4,
    num_channels=3,
    num_classes=2,
    min_area=0,
    max_tile_size=None,
    max_tile_dim=None,
    **kwargs
):
    """
    Perform object detection on an Earth Engine image using a deep learning model.

    This function splits a large Earth Engine image into smaller tiles, runs a deep learning object detection model on each tile,
    and vectorizes the prediction masks. The final output is a ee.FeatureCollection object.

    Args:
        image (ee.Image): The Earth Engine image to analyze.
        model_path (str): Path to the PyTorch model file (.pth) used for inference.
        scale (float, optional): Resample image(s) to this pixel scale (size) (m).  Where image bands have different scales,
            all are resampled to this scale.  Defaults to the minimum scale of image bands.
        segment_fn (Callable): A segmentation post-processing function that processes the model's raw output.
        segment_args (dict): A dictionary of keyword arguments to pass to the segmentation function.
        num_threads (int, optional): Number of tiles to download concurrently.  Defaults to a sensible auto value.    
        bands (list, optional): A list of band names to use in the timelapse.
        window_size (int): Size of sliding window for inference.
        overlap (int): Overlap between adjacent windows.
        confidence_threshold (float): Confidence threshold for predictions (0-1).
        batch_size (int): Batch size for inference.
        num_channels (int): Number of channels in the input image and model.
        num_classes (int, optional): Number of classes in the model output. Default is 2.
        min_area (float): Minimum polygon area in square map units to keep.
        max_tile_size: int, optional
            Maximum tile size (MB).  If None, defaults to the Earth Engine download size limit (32 MB).
        max_tile_dim: int, optional
            Maximum tile width/height (pixels).  If None, defaults to Earth Engine download limit (10000).
        **kwargs: Additional arguments passed to object_detection.

    Returns:
        ee.FeatureCollection: A FeatureCollection containing vectorized object detection results, reprojected to WGS84.
    
    Note:
        This function relies on the `geedim`, `rasterio`, and `geoai` packages for tiling, downloading, inference,
        and raster-to-vector conversion. Ensure the Earth Engine image is processed and scaled appropriately before passing to this function.
    """
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    warnings.filterwarnings("ignore", category=UserWarning, module="rasterio._env")
    logging.getLogger('rasterio').setLevel(logging.ERROR)

    out_lock = threading.Lock()

    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as temp_merged, \
        tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as temp_mask, \
        tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as temp_geojson:

        merged_path = temp_merged.name
        masks_path = temp_mask.name
        output_path = temp_geojson.name

        if not isinstance(bands, list):
            bands = image.bandNames().getInfo()

        if not isinstance(image, ee.Image):
            raise ValueError("image must be an ee.Image.")

        max_threads = num_thread or min(10, (os.cpu_count() or 1))

        baseImg = gd.download.BaseImage(image)

        if kwargs.get('set_nodata') is None:
            kwargs['set_nodata'] = True
        if kwargs.get('crs') is None:
            kwargs['crs'] = "EPSG:4326"
        if kwargs.get('region') is None:
            kwargs['region'] = image.geometry().bounds()
        if kwargs.get('epsilon') is None:
            kwargs['epsilon'] = 0.2
        if kwargs.get('min_segments') is None:
            kwargs['min_segments'] = 4
        if kwargs.get('area_tolerance') is None:
            kwargs['area_tolerance'] = 0.7
        if kwargs.get('detect_triangles') is None:
            kwargs['detect_triangles'] = True



        exp_img, profile = baseImg._prepare_for_download(
            set_nodata=kwargs['set_nodata'],
            crs=kwargs['crs'],
            scale=scale,
            region=kwargs['region']
        )
        print(exp_img.shape)
        tile_shape, num_tiles = exp_img._get_tile_shape(max_tile_size=max_tile_size, max_tile_dim=max_tile_dim)
        tiles_list = list(exp_img._tiles(tile_shape))

        dtype_size = np.dtype(exp_img.dtype).itemsize
        tile_height, tile_width = tile_shape
        tile_pixel_size = tile_height * tile_width * exp_img.count * dtype_size
        raw_download_size = tile_pixel_size * len(tiles_list)

        bar = tqdm(
            desc="🧩 Processing tiles", total=raw_download_size,
            bar_format='{desc}: |{bar}| {n_fmt}/{total_fmt} (raw) [{percentage:5.1f}%] in {elapsed:>5s} (eta: {remaining:>5s})',
            dynamic_ncols=True, unit_scale=True, unit='B'
        )

        with rasterio.Env(GDAL_NUM_THREADS='ALL_CPUs', GTIFF_FORCE_RGBA=False):
            with rasterio.open(merged_path, "w", **profile) as out_ds:

                def process_tile(tile):
                    try:
                        tile_array = tile.download(session=gd.utils.retry_session(),bar=bar)
                        with out_lock:
                            out_ds.write(tile_array, window=tile.window)
                        return True
                    except Exception as e:
                        return False

                with ThreadPoolExecutor(max_workers=max_threads) as executor:
                    futures = [executor.submit(process_tile, tile) for tile in tiles_list]
                    for future in as_completed(futures):
                        future.result()
        bar.close()
        segment_fn(
            input_path=merged_path,
            output_path=masks_path,
            model_path=model_path,
            window_size=window_size,
            overlap=overlap,
            confidence_threshold=confidence_threshold,
            batch_size=batch_size,
            num_channels=num_channels,
            num_classes=num_classes,
            **segment_args
        )

        def silent(func, *args, **kwargs):
            f = io.StringIO()
            with redirect_stdout(f), redirect_stderr(f):
                return func(*args, **kwargs)
            
        gdf = silent(
            geoai.orthogonalize,
            masks_path,output_path,
            min_area=min_area,
            epsilon=kwargs['epsilon'],
            min_segments=kwargs['min_segments'],
            area_tolerance=kwargs['area_tolerance'],
            detect_triangles=kwargs['detect_triangles']
        )
            
        gdf = geoai.add_geometric_properties(gdf)
        gdf_wgs84 = gdf.to_crs(epsg=4326)
        geojson_dict = gdf_wgs84.__geo_interface__

        for path in [merged_path, masks_path, output_path]:
            try:
                os.remove(path)
            except Exception as e:
                logging.warning(f"Failed to remove {path}: {e}")

        return geojson_to_ee(geojson_dict)
    

def detect_instance_segmentation(
    image,
    model_path,
    scale,
    num_thread=None,
    bands=None,
    window_size=512,
    overlap=256,
    confidence_threshold=0.5,
    batch_size=4,
    num_channels=3,
    num_classes=2,
    min_area=0,
    max_tile_size=None,
    max_tile_dim=None,
    **kwargs
):
    """
    Perform instance segmentation on an Earth Engine image using a pre-trained Mask R-CNN model.

    Args:
        image: ee.Image object.
        model_path: Path to the trained model.
        scale: Resolution in meters.
        num_threads: Number of tiles to download concurrently.  Defaults to a sensible auto value.    
        bands: List of image bands to use.
        window_size: Size of the sliding window in pixels .
        overlap: Overlap between windows in pixels.
        confidence_threshold: Minimum confidence to retain detections.
        batch_size: Batch size for inference .
        num_channels: Number of input channels.
        num_classes: Number of output classes.
        min_area: Minimum area of detected object to keep .
        max_tile_size: Maximum tile size in MB.
        max_tile_dim: Maximum tile dimension in pixels.
    """
    return _detect_image(
        image=image,
        model_path=model_path,
        scale=scale,
        segment_fn=geoai.instance_segmentation,
        segment_args={}, 
        num_thread=num_thread,
        bands=bands,
        window_size=window_size,
        overlap=overlap,
        confidence_threshold=confidence_threshold,
        batch_size=batch_size,
        num_channels=num_channels,
        num_classes=num_classes,
        min_area=min_area,
        max_tile_size=max_tile_size,
        max_tile_dim=max_tile_dim,
        **kwargs
    )

def detect_semantic_segmentation(
    image,
    model_path,
    scale,
    architecture="unet",
    encoder_name="resnet34",
    num_thread=None,
    bands=None,
    window_size=512,
    overlap=256,
    confidence_threshold=0.5,
    batch_size=4,
    num_channels=3,
    num_classes=2,
    min_area=0,
    max_tile_size=None,
    max_tile_dim=None,
    device=None,
    quiet=False,
    **kwargs
):
    """
    Perform semantic segmentation on an Earth Engine image.

    Args:
        image: ee.Image object.
        model_path: Path to the trained model.
        scale: Resolution in meters.
        architecture: Model architecture used for training.
        encoder_name: Encoder backbone name used for training.
        num_threads: Number of tiles to download concurrently.  Defaults to a sensible auto value.    
        bands: List of image bands to use.
        window_size: Size of the sliding window in pixels.
        overlap: Overlap between windows in pixels.
        confidence_threshold: Minimum confidence to retain detection.
        batch_size: Batch size for inference.
        num_channels: Number of input channels.
        num_classes: Number of output classe.
        max_tile_size: Maximum tile size in MB.
        max_tile_dim: Maximum tile dimension in pixels.
        device: Device to run inference on.
        quiet: If True, suppress progress bar. Defaults to False.
        **kwargs: Additional arguments.
    """
    return _detect_image(
        image=image,
        model_path=model_path,
        scale=scale,
        segment_fn=geoai.semantic_segmentation,
        segment_args={
            "architecture": architecture,
            "encoder_name": encoder_name,
            "device": device,
            "quiet": quiet,
            **kwargs
        },
        num_thread=num_thread,
        bands=bands,
        window_size=window_size,
        overlap=overlap,
        confidence_threshold=confidence_threshold,
        batch_size=batch_size,
        num_channels=num_channels,
        num_classes=num_classes,
        min_area=min_area,
        max_tile_size=max_tile_size,
        max_tile_dim=max_tile_dim,
        **kwargs
    )