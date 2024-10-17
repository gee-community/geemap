"""This module contains functions for interacting with AI models.
    The Genie class source code is adapted from the ee_genie.ipynb at <https://bit.ly/3YEm7B6>.
    Credit to the original author Simon Ilyushchenko (<https://github.com/simonff>).
    The DataExplorer class source code is adapted from <https://bit.ly/48cE24D>.
    Credit to the original author Renee Johnston (<https://github.com/raj02006>)
"""

# Standard library imports
import io
import json
import math
import os
import time
from concurrent import futures
from contextlib import redirect_stdout
import dataclasses
import datetime
import logging
import re
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import uuid

import numpy as np
import pandas as pd

import PIL
import requests

import ee
import typing_extensions
import ipywidgets as widgets
from ipyleaflet import LayerException
from jinja2 import Template
from IPython.display import HTML, Javascript, display

try:

    import vertexai
    import google.generativeai as genai
    import google.ai.generativelanguage as glm
    import google.api_core
    from google.cloud import storage
    from google.api_core import exceptions as google_exceptions
    from vertexai.preview.language_models import TextEmbeddingModel
    from langchain.embeddings.base import Embeddings
    from langchain.indexes import VectorstoreIndexCreator
    from langchain.schema import Document
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.vectorstores.base import VectorStore
    from langchain.indexes.vectorstore import VectorStoreIndexWrapper
    from langchain_core.language_models.base import BaseLanguageModel
except ImportError:
    print("Please install the required packages.")
    print("pip install 'geemap[ai]'")

# Third-party imports
import iso8601
import tenacity
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .geemap import Map, get_env_var, js_snippet_to_py, ee_initialize, temp_file_path

# Google Colab-specific imports (only if you're working in Google Colab)
if "google.colab" in sys.modules:
    from google.colab import output, data_table, syntax


class Genie(widgets.VBox):
    """A widget for interacting with the Genie AI model.

    The source code is adapted from the ee_genie.ipynb at <https://bit.ly/3YEm7B6>.
    Credit to the original author Simon Ilyushchenko (<https://github.com/simonff>).

    Args:
        project (Optional[str], optional): Google Cloud project ID. Defaults to None.
        google_api_key (Optional[str], optional): Google API key. Defaults to None.
        gemini_model (str, optional): The Gemini model to use. Defaults to "gemini-1.5-flash".
            For a list of available models, see https://bit.ly/4fKfXW7.
        target_score (float, optional): The target score for the model. Defaults to 0.8.
        widget_height (str, optional): The height of the widget. Defaults to "600px".
        initialize_ee (bool, optional): Whether to initialize Earth Engine. Defaults to True.

    Raises:
        ValueError: If the project ID or Google API key is not provided.
    """

    def __init__(
        self,
        project: Optional[str] = None,
        google_api_key: Optional[str] = None,
        gemini_model: str = "gemini-1.5-flash",
        target_score: float = 0.8,
        widget_height: str = "600px",
        initialize_ee: bool = True,
    ) -> None:
        # Initialization

        if project is None:
            project = get_env_var("EE_PROJECT_ID") or get_env_var("GOOGLE_PROJECT_ID")
        if project is None:
            raise ValueError(
                "Please provide a valid project ID via the 'project' parameter."
            )

        if google_api_key is None:
            google_api_key = get_env_var("GOOGLE_API_KEY")
        if google_api_key is None:
            raise ValueError(
                "Please provide a valid Google API key via the 'google_api_key' parameter."
            )

        if initialize_ee:
            ee_initialize(project=project)

        genai.configure(api_key=google_api_key)
        storage_client = storage.Client(project=project)
        bucket = storage_client.get_bucket("earthengine-stac")

        # Score to aim for (on the 0-1 scale). The exact meaning of what "score" means
        # is left to the LLM.

        # Count of analysis rounds

        self.iteration = 1
        self.map_dirty = False

        m = Map()
        m.add("layer_manager")
        self.map = m

        analysis_model = None

        image_model = genai.GenerativeModel(gemini_model)

        # UI widget definitions

        # We define the widgets early because some functions will write to the debug
        # and/or chat panels.

        command_input = widgets.Text(
            value="show a whole continent Australia DEM visualization using a palette that captures the elevation range",
            # value='show NYC',
            # value='show an area with many center pivot irrigation circles',
            # value='show a fire scar',
            # value='show an open pit mine',
            # value='a sea port',
            # value='flood consequences',
            # value='show an interesting modis composite with the relevant visualization and analyze it over Costa Rica',
            description="❓",
            layout=widgets.Layout(width="100%", height="50px"),
        )

        command_output = widgets.Label(
            value="Last command will be here",
        )

        status_label = widgets.Textarea(
            value="LLM response will be here",
            layout=widgets.Layout(width="50%", height="100px"),
        )

        # widget_height = "600px"
        debug_output = widgets.Output(
            layout={
                "border": "1px solid black",
                "height": widget_height,
                "overflow": "scroll",
                "width": "500px",
                "padding": "5px",
            }
        )
        with debug_output:
            print("DEBUG COLUMN\n")

        logo = requests.get(
            "https://drive.usercontent.google.com/download?id=1zE6G_nxXa3G5N0G_32jEhzdum2kMDfNY&export=view&authuser=0"
        ).content

        image_widget = widgets.Image(value=logo, format="png", width=400, height=600)

        chat_output = widgets.Output(
            layout={
                "border": "1px solid black",
                "height": "600px",
                "overflow": "scroll",
                "width": "300px",
            }
        )

        with chat_output:
            print("CHAT COLUMN\n")

        # Simple functions that LLM will call

        def set_center(x: float, y: float, zoom: int) -> str:
            """Sets the map center to the given coordinates and zoom level and
            returns instructions on what to do next."""
            with debug_output:
                print(f"SET_CENTER({x}, {y}, {zoom})\n")
            m.set_center(x, y)
            m.zoom = zoom
            # global map_dirty
            self.map_dirty = True
            return (
                "Do not call any more functions in this request to let geemap bounds "
                "update. Wait for user input."
            )

        def add_image_layer(image_id: str) -> str:
            """Adds to the map center an ee.Image with the given id
            and returns status message (success or failure)."""
            m.clear()
            command_output.value = f"add_image_layer('{image_id}')"
            m.addLayer(ee.Image(image_id))
            return "success"

        def get_dataset_description(dataset_id: str) -> str:
            """Fetches JSON STAC description for the given Earth Engine dataset id."""
            with debug_output:
                print(f"LOOKING UP {dataset_id}\n")
            parent = dataset_id.split("/")[0]

            # Get the blob (file)
            path = (
                os.path.join("catalog", parent, dataset_id.replace("/", "_")) + ".json"
            )
            blob = bucket.blob(path)

            if not blob.exists():
                return "dataset file not found: " + path

            file_contents = blob.download_as_string().decode()
            return file_contents

        def get_image(image_url: str) -> bytes:
            """Fetches from Earth Engine the content of the given URL as bytes."""
            response = requests.get(image_url)

            if response.status_code == 200:
                image_widget.value = response.content
                return response.content
            else:
                error_message = f"Error downloading image: {response}"
                try:
                    error_details = (
                        json.loads(response.content.decode())
                        .get("error", {})
                        .get("message")
                    )
                    if error_details:
                        error_message += f" - {error_details}"
                except json.JSONDecodeError:
                    pass
                with debug_output:
                    print(error_message)
                raise ValueError("URL %s causes %s" % (image_url, error_message))

        def show_layer(python_code: str) -> str:
            """Execute the given Earth Engine Python client code and add the result to
            the map. Returns the status message (success or error message)."""
            m.layers = m.layers[:2]
            while '\\"' in python_code:
                python_code = python_code.replace('\\"', '"')
            command_output.value = f"show_layer('{python_code}')"
            with debug_output:
                print(f"IMAGE:\n {python_code}\n")
            try:
                locals = {}
                exec(f"import ee; im = {python_code}", {}, locals)
                m.addLayer(locals["im"])
            except Exception as e:
                with debug_output:
                    print(f"ERROR: {e}")
                return str(e)
            return "success"

        def inner_monologue(thoughts: str) -> str:
            """Sends the current thinking of the LLM model to the user so that they are
            aware of what the model is thinking between function calls."""
            with debug_output:
                print(f"THOUGHTS:\n {thoughts}\n")
            return "success"

        # Functions for textual analysis of images

        def _lat_lon_to_tile(lon, lat, zoom_level):
            # Convert latitude and longitude to Mercator coordinates
            x_merc = (lon + 180) / 360
            y_merc = (
                1
                - math.log(
                    math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))
                )
                / math.pi
            ) / 2

            # Calculate number of tiles
            n = 2**zoom_level

            # Convert to tile coordinates
            X = int(x_merc * n)
            Y = int(y_merc * n)

            return X, Y

        def analyze_image(additional_instructions: str = "") -> str:
            """Returns GenAI image analysis describing the current map image.
            Optional additional instructions might be passed to target the analysis
            more precisely.
            """
            # global map_dirty
            if self.map_dirty:
                print("MAP DIRTY")
                return (
                    "Map is not ready. Stop further processing and ask for user input"
                )

            try:
                return _analyze_image(additional_instructions)
            except ValueError as e:
                return str(e)

        def _analyze_image(additional_instructions: str = "") -> str:
            # bounds = m.bounds
            # s, w = bounds[0]
            # n, e = bounds[1]
            # zoom = int(m.zoom)

            # min_tile_x, max_tile_y = _lat_lon_to_tile(w, s, zoom)
            # max_tile_x, min_tile_y = _lat_lon_to_tile(e, n, zoom)
            # min_tile_x = max(0, min_tile_x)
            # max_tile_x = min(2**zoom - 1, max_tile_x)
            # min_tile_y = max(0, min_tile_y)
            # max_tile_y = min(2**zoom - 1, max_tile_y)

            # with debug_output:
            #     if additional_instructions:
            #         print(f"RUNNING IMAGE ANALYSIS: {additional_instructions}...\n")
            #     else:
            #         print("RUNNING IMAGE ANALYSIS...\n")

            # layers = list(m.ee_layer_dict.values())
            # if not layers:
            #     return "No data layers loaded"
            # url_template = layers[-1]["ee_layer"].url
            # tile_width = 256
            # tile_height = 256
            # image_width = (max_tile_x - min_tile_x + 1) * tile_width
            # image_height = (max_tile_y - min_tile_y + 1) * tile_height

            # # Create a new blank image
            # image = PIL.Image.new("RGB", (image_width, image_height))

            # for y in range(min_tile_y, max_tile_y + 1):
            #     for x in range(min_tile_x, max_tile_x + 1):
            #         tile_url = str.format(url_template, x=x, y=y, z=zoom)
            #         # print(tile_url)
            #         tile_img = PIL.Image.open(io.BytesIO(get_image(tile_url)))

            #         offset_x = (x - min_tile_x) * tile_width
            #         offset_y = (y - min_tile_y) * tile_height
            #         image.paste(tile_img, (offset_x, offset_y))

            # width, height = image.size
            # num_bands = len(image.getbands())

            with debug_output:
                if additional_instructions:
                    print(f"RUNNING IMAGE ANALYSIS: {additional_instructions}...\n")
                else:
                    print("RUNNING IMAGE ANALYSIS...\n")

            layers = list(m.ee_layer_dict.values())
            if not layers:
                return "No data layers loaded"
            image_temp_file = temp_file_path(extension="jpg")
            layer_name = layers[-1]["ee_layer"].name
            m.layer_to_image(layer_name, output=image_temp_file, scale=m.get_scale())
            image = PIL.Image.open(image_temp_file)

            image_array = np.array(image)
            image_min = np.min(image_array)
            image_max = np.max(image_array)

            file = open(image_temp_file, "rb")
            image_widget.value = file.read()
            file.close()

            # Skip an LLM call when we can simply tell that something is wrong.
            # (Also, LLMs might hallucinate on uniform images.)
            if image_min == image_max:
                return (
                    f"The image tile has a single uniform color with value "
                    f"{image_min}."
                )

            query = """You are an objective, precise overhead imagery analyst.
        Describe what the provided map tile depicts in terms of:

        1. The colors, textures, and patterns visible in the image.
        2. The spatial distribution, shape, and extent of distinct features or regions.
        3. Any notable contrasts, boundaries, or gradients between different areas.

        Avoid making assumptions about the specific geographic location, time period,
        or cause of the observed features. Focus solely on the literal contents of the
        image itself. Clearly indicate which features look natural, which look human-made,
        and which look like image artifacts. (Eg, a completely straight blue line
        is unlikely to be a river.)

        If the image is ambiguous or unclear, state so directly. Do not speculate or
        hypothesize beyond what is directly visible.

        If the image is of mostly the same color (white, gray, or black) with little
        contrast, just report that and do not describe the features.

        Use clear, concise language. Avoid subjective interpretations or analogies.
        Organize your response into structured paragraphs.
        """
            if additional_instructions:
                query += additional_instructions
            req = {
                "parts": [
                    {"text": query},
                    {"inline_data": image},
                ]
            }
            image_response = image_model.generate_content(req)
            try:
                with debug_output:
                    print(f"ANALYSIS RESULT: {image_response.text}\n")
                return image_response.text
            except ValueError as e:
                with debug_output:
                    print(f"UNEXPECTED IMAGE RESPONSE: {e}")
                    print(image_response)
                breakpoint()

        # Function for scoring how well image analysis corresponds to the user query.

        # Note that we ask for the score outside of the main agent chat to keep
        # the scoring more objective.

        scoring_system_prompt = """
        After looking at the user query and the map tile analysis, start
        your answer with a number between 0 and 1 indicating how relevant
        the image is as an answer to the query. (0=irrelevant, 1=perfect answer)

        Make sure you have enough justification to definitively declare the analysis
        relevant - it's better to give a false negative than a false positive. However,
        the image analysis identifies specific matching landmarks (eg, the
        the outlines of Manhattan island for a request to show NYC), believe it.

        Do not assume  too much (eg, that the presence of green doesn't by itself mean the
        image shows forest); attempt to find multiple (at least three) independent
        lines of evidence before declaring victory and cite all these lines of evidence
        in your response.

        Be very, very skeptical - look for specific features that match only the query
        and nothing else (eg, if the query looks for a river, a completely straight blue
        line is unlikely to be a river). Think about what size the features are based on
        the zoom level and whether this size matches the feature size expected from
        first principles.

        If there is ambiguity or uncertainty, express it in your analysis and
        lower the score accordingly. If the image analysis is inconclusive, try zooming
        out to make sure you are looking at the right spot. Do not reduce the score if
        the analysis does not mention visualization parameters - they are just given for
        your reference. The image might show an area slightly larger than requested -
        this is okay, do not reduce the score on this account.
        """

        def score_response(
            query: str, visualization_parameters: str, analysis: str
        ) -> str:
            """Returns how well the given analysis describes a map tile returned for
            the given query. The analysis starts with a number between 0 and 1.

            Arguments:
            query: user-specified query
            visualization_parameters: description of the bands used and visualization
                parameters applied to the map tile
            analysis: the textual description of the map tile
            """
            with debug_output:
                print(f"VIZ PARAMS: {visualization_parameters}\n")
            question = f"""For user query {query} please score the following analysis:
            {analysis}. The answer must start with a number between 0 and 1."""
            if visualization_parameters:
                question += f"""Do not assume that common bands or visualization
                parameters should have been used, as the visualization used the
                following parameters: {visualization_parameters}"""

            result = analysis_model.ask(question)
            # global iteration
            with debug_output:
                print(f"SCORE #{self.iteration}:\n {result}\n")
            try:
                self.iteration += 1
            except Exception as e:
                with debug_output:
                    print(f"UNEXPECTED SCORE RESPONSE: {e}")
            return result

        # Main prompt for the agent

        system_prompt = f"""
        The client is running in a Python notebook with a geemap Map displayed.
        When composing Python code, do not use getMapId - just return the single-line
        layer definition like 'ee.Image("USGS/SRTMGL1_003")' that we will pass to
        Map.addLayer(). Do not escape quotation marks in Python code.

        Be sure to use Python, not Javascript, syntax for keyword parameters in
        Python code (that is, "function(arg=value)") Using the provided functions,
        respond to the user command following below (or respond why it's not possible).
        If you get an Earth Engine error, attempt to fix it and then try again.

        Before you choose a dataset, think about what kind of dataset would be most
        suitable for the query. Also think about what zoom level would be suitable for
        the query, keeping in mind that for high-resolution image collections higher
        zoom levels are better to speed up tile loading.

        Once you have chosen a dataset, read its description using the provided function
        to see what spatial and temporal range it covers, what bands it has, as well as
        to find the recommended visualization parameters. Explain using the inner
        monlogue function why you chose a specific dataset, zoom level and map location.

        Prefer mosaicing image collections using the mosaic() function, don't get
        individual images from collections via
        'first()'. Choose a tile size and zoom level that will ensure the
        tile has enough pixels in it to avoid graininess, but not so many
        that processing becomes very expensive. Do not use wide date ranges
        with collections that have many images, but remember that Landsat and
        Sentinel-2 have revisit period of several days. Do not use sample
        locations - try to come up with actual locations that are relevant to
        the request.

        Use Landsat Collection 2, not Landsat Collection 1 ids. If you are getting
        repeated errors when filtering by a time range, read the dataset description
        to confirm that the dataset has data for the selected range.

        Important: after using the set_center() function, just say that you have called
        this function and wait for the user to hit enter, after which you should
        continue answering the original request. This will make sure the map is updated
        on the client side.

        Once the map is updated and the user told you to proceed, call the analyze_image
        function() to describe the image for the same location that will be shown in
        geemap. If you pass additional instructions to analyze_image(), do not disclose
        what the image is supposed to be to discourage hallucinations - you can only tell
        the analysis function to pay attention to specific areas (eg, center or top left)
        or shapes (eg, a line at the bottom) in the image. You can also tell the analysis
        function about the chosen bands, color palette and min/max visualization
        parameters, if any, to help it interpret the colors correctly. If the image
        turns out to be uniform in color with no features,
        use min/max visualization parameters to enhance contrast.

        Frequently call the inner_monologue() functions to tell the user about your
        current thought process. This is a good time to reflect if you have been running
        into repeated errors of the same kind, and if so, to try a different approach.

        When you are done, call the score_response() function to evaluate the analysis.
        You can also tell the scoring function about the chosen bands, color palette
        and min/max visualization parameters, if any. If the analysis score is below
        {target_score},
        keep trying to find and show a better image. You might have to change the dataset,
        map location, zoom level, date range, bands, or other parameters - think about
        what went wrong in the previous attempt and make the change that's most likely
        to improve the score.
        """

        # Class for LLM chat with function calling

        gemini_tools = [
            set_center,
            show_layer,
            analyze_image,
            inner_monologue,
            get_dataset_description,
            score_response,
        ]

        class Gemini:
            """Gemini LLM."""

            def __init__(
                self, system_prompt, tools=None, model_name="gemini-1.5-pro-latest"
            ):
                if not tools:
                    tools = []
                self._text_model = genai.GenerativeModel(
                    model_name=model_name, tools=tools
                )

                initial_messages = glm.Content(
                    role="model", parts=[glm.Part(text=system_prompt)]
                )
                self._chat_proxy = self._text_model.start_chat(
                    history=initial_messages, enable_automatic_function_calling=True
                )

            def ask(self, question, temperature=0):
                while True:
                    condition = ""
                    try:
                        sleep_duration = 10
                        response = self._text_model.generate_content(
                            question + condition
                        )
                        return response.text
                    except genai.types.generation_types.StopCandidateException as e:
                        if (
                            glm.Candidate.FinishReason.RECITATION
                            == e.args[0].finish_reason
                        ):
                            condition = (
                                "Previous attempt returned a RECITATION error. "
                                "Rephrase the answer to avoid it."
                            )
                        with chat_output:
                            command_input.description = "🆁"
                        time.sleep(1)
                        with chat_output:
                            command_input.description = "🤔"
                        continue
                    except (
                        google.api_core.exceptions.TooManyRequests,
                        google.api_core.exceptions.DeadlineExceeded,
                    ):
                        with debug_output:
                            command_input.description = "💤"
                        time.sleep(sleep_duration)
                        continue
                    except ValueError as e:
                        with debug_output:
                            print(f"Response {response} led to error: {e}")
                        breakpoint()
                        i = 1

            def chat(self, question: str, temperature=0) -> str:
                """Adds a question to the ongoing chat session."""
                # Always delay a bit to reduce the chance for rate-limiting errors.
                time.sleep(1)
                condition = ""
                sleep_duration = 10
                while True:
                    response = ""
                    try:
                        response = self._chat_proxy.send_message(
                            question + condition,
                            generation_config={
                                "temperature": temperature,
                                # Use a generous but limited output size to encourage in-depth
                                # replies.
                                "max_output_tokens": 5000,
                            },
                        )
                        if not response.parts:
                            raise ValueError(
                                "Cannot get analysis with reason"
                                f" {response.candidates[0].finish_reason.name}, terminating"
                            )
                    except genai.types.generation_types.StopCandidateException as e:
                        if (
                            glm.Candidate.FinishReason.RECITATION
                            == e.args[0].finish_reason
                        ):
                            condition = (
                                "Previous attempt returned a RECITATION error. "
                                "Rephrase the answer to avoid it."
                            )
                        with chat_output:
                            command_input.description = "🆁"
                        time.sleep(1)
                        with chat_output:
                            command_input.description = "🤔"
                        continue
                    except (
                        google.api_core.exceptions.TooManyRequests,
                        google.api_core.exceptions.DeadlineExceeded,
                    ):
                        with debug_output:
                            command_input.description = "💤"
                        time.sleep(10)
                        continue
                    try:
                        return response.text
                    except ValueError as e:
                        with debug_output:
                            print(f"Response {response} led to the error {e}")

        model = Gemini(system_prompt, gemini_tools, model_name=gemini_model)
        analysis_model = Gemini(scoring_system_prompt, model_name=gemini_model)

        # UI functions

        def set_cursor_waiting():
            js_code = """
            document.querySelector('body').style.cursor = 'wait';
            """
            display(HTML(f"<script>{js_code}</script>"))

        def set_cursor_default():
            js_code = """
            document.querySelector('body').style.cursor = 'default';
            """
            display(HTML(f"<script>{js_code}</script>"))

        def on_submit(widget):
            # global map_dirty
            self.map_dirty = False
            command_input.description = "❓"
            command = widget.value
            if not command:
                command = "go on"
            with chat_output:
                print("> " + command + "\n")
            if command != "go on":
                with debug_output:
                    print("> " + command + "\n")
            widget.value = ""
            set_cursor_waiting()
            command_input.description = "🤔"
            response = model.chat(command, temperature=0)
            if self.map_dirty:
                command_input.description = "🙏"
            else:
                command_input.description = "❓"
            set_cursor_default()
            response = response.strip()
            if not response:
                response = "<EMPTY RESPONSE, HIT ENTER>"
            with chat_output:
                print(response + "\n")
            command_input.value = ""

        command_input.on_submit(on_submit)

        # UI layout

        # Arrange the chat history and input in a vertical box
        chat_ui = widgets.VBox(
            [image_widget, chat_output],
            layout=widgets.Layout(width="420px", height=widget_height),
        )

        chat_output.layout = widgets.Layout(
            width="400px"
        )  # Fixed width for the left control
        m.layout = widgets.Layout(flex="1 1 auto", height=widget_height)

        table = widgets.HBox(
            [chat_ui, debug_output, m], layout=widgets.Layout(align_items="flex-start")
        )

        message_widget = widgets.Output()
        with message_widget:
            print("❓ = waiting for user input")
            print("🙏 = waiting for user to hit enter after calling set_center()")
            print("🤔 = thinking")
            print("💤 = sleeping due to retries")
            print("🆁 = Gemini recitation error")

        super().__init__(
            [table, command_input, message_widget], layout={"overflow": "hidden"}
        )


def matches_interval(
    collection_interval: Tuple[datetime.datetime, datetime.datetime],
    query_interval: Tuple[datetime.datetime, datetime.datetime],
) -> bool:
    """Checks if the collection's datetime interval matches the query datetime interval.

    Args:
        collection_interval (Tuple[datetime.datetime, datetime.datetime]):
            Temporal interval of the collection.
        query_interval (Tuple[datetime.datetime, datetime.datetime]): A tuple
            with the query interval start and end.

    Returns:
        bool: True if the datetime interval matches, False otherwise.
    """
    start_query, end_query = query_interval
    start_collection, end_collection = collection_interval
    if end_collection is None:
        # End date should always be set in STAC JSON files, but just in case...
        end_collection = datetime.datetime.now(tz=datetime.UTC)
    return end_query > start_collection and start_query <= end_collection


def matches_datetime(
    collection_interval: Tuple[datetime.datetime, Optional[datetime.datetime]],
    query_datetime: datetime.datetime,
) -> bool:
    """Checks if the collection's datetime interval matches the query datetime.

    Args:
        collection_interval (Tuple[datetime.datetime, Optional[datetime.datetime]]):
            Temporal interval of the collection.
        query_datetime (datetime.datetime): A datetime coming from a query.

    Returns:
        bool: True if the datetime interval matches, False otherwise.
    """
    if collection_interval[1] is None:
        # End date should always be set in STAC JSON files, but just in case...
        end_date = datetime.datetime.now(tz=datetime.UTC)
    else:
        end_date = collection_interval[1]
    return collection_interval[0] <= query_datetime <= end_date


@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_fixed(1),
    retry=tenacity.retry_if_exception_type(LayerException),
    # before_sleep=lambda retry_state: print(f"LayerException occurred. Retrying in 1 seconds... (Attempt {retry_state.attempt_number}/3)")
)
def run_ee_code(code: str, ee: Any, geemap_instance: Map) -> None:
    """Executes Earth Engine Python code within the context of a geemap instance.

    Args:
        code (str): The Earth Engine Python code to execute.
        ee (Any): The Earth Engine module.
        geemap_instance (Map): The geemap instance.

    Raises:
        Exception: Re-raises any exception encountered during code execution.
    """
    try:
        # geemap appears to have some stray print statements.
        _ = io.StringIO()
        with redirect_stdout(_):
            # Note that sometimes the geemap code uses both 'Map' and 'm' to refer to a map instance.
            exec(code, {"ee": ee, "Map": geemap_instance, "m": geemap_instance})
    except Exception:
        # Re-raise the exception with the original traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        raise exc_value.with_traceback(exc_traceback)


@dataclasses.dataclass
class BBox:
    """Class representing a lat/lon bounding box."""

    west: float
    south: float
    east: float
    north: float

    def is_global(self) -> bool:
        """Checks if the bounding box is global.

        Returns:
            bool: True if the bounding box is global, False otherwise.
        """
        return (
            self.west == -180
            and self.south == -90
            and self.east == 180
            and self.north == 90
        )

    @classmethod
    def from_list(cls, bbox_list: List[float]) -> "BBox":
        """Constructs a BBox from a list of four numbers [west, south, east, north].

        Args:
            bbox_list (List[float]): List of four numbers representing the bounding box.

        Returns:
            BBox: The constructed BBox object.

        Raises:
            ValueError: If the coordinates are not in the correct order.
        """
        if bbox_list[0] > bbox_list[2]:
            raise ValueError(
                "The smaller (west) coordinate must be listed first in a bounding box"
                f" corner list. Found {bbox_list}"
            )
        if bbox_list[1] > bbox_list[3]:
            raise ValueError(
                "The smaller (south) coordinate must be listed first in a bounding"
                f" box corner list. Found {bbox_list}"
            )
        return cls(bbox_list[0], bbox_list[1], bbox_list[2], bbox_list[3])

    def to_list(self) -> List[float]:
        """Converts the BBox to a list of four numbers [west, south, east, north].

        Returns:
            List[float]: List of four numbers representing the bounding box.
        """
        return [self.west, self.south, self.east, self.north]

    def intersects(self, query_bbox: "BBox") -> bool:
        """Checks if this bbox intersects with the query bbox.

        Doesn't handle bboxes extending past the antimeridian.

        Args:
            query_bbox (BBox): Bounding box from the query.

        Returns:
            bool: True if the two bounding boxes intersect, False otherwise.
        """
        return (
            query_bbox.west < self.east
            and query_bbox.east > self.west
            and query_bbox.south < self.north
            and query_bbox.north > self.south
        )


class Collection:
    """A simple wrapper for a STAC Collection.."""

    stac_json: dict[str, Any]

    def __init__(self, stac_json: Dict[str, Any]) -> None:
        """Initializes the Collection.

        Args:
            stac_json (Dict[str, Any]): The STAC JSON of the collection.
        """
        self.stac_json = stac_json
        if stac_json.get("gee:status") == "deprecated":
            # Set the STAC 'deprecated' field that we don't set in the jsonnet files
            stac_json["deprecated"] = True

    def __getitem__(self, item: str) -> Any:
        """Gets an item from the STAC JSON.

        Args:
            item (str): The key of the item to get.

        Returns:
            Any: The value of the item.
        """
        return self.stac_json[item]

    def get(self, item: str, default: Optional[Any] = None) -> Optional[Any]:
        """Matches dict's get by returning None if there is no item.

        Args:
            item (str): The key of the item to get.
            default (Optional[Any]): The default value to return if the item is not found. Defaults to None.

        Returns:
            Optional[Any]: The value of the item or the default value.
        """
        return self.stac_json.get(item, default)

    def public_id(self) -> str:
        """Gets the public ID of the collection.

        Returns:
            str: The public ID of the collection.
        """
        return self["id"]

    def hyphen_id(self) -> str:
        """Gets the hyphenated ID of the collection.

        Returns:
            str: The hyphenated ID of the collection.
        """
        return self["id"].replace("/", "_")

    def get_dataset_type(self) -> str:
        """Gets the dataset type of the collection.

        Returns:
            str: The dataset type of the collection.
        """
        return self["gee:type"]

    def is_deprecated(self) -> bool:
        """Checks if the collection is deprecated or has a successor.

        Returns:
            bool: True if the collection is deprecated or has a successor, False otherwise.
        """
        if self.get("deprecated", False):
            logging.info("Skipping deprecated collection: %s", self.public_id())
            return True

    def datetime_interval(
        self,
    ) -> Iterable[Tuple[datetime.datetime, Optional[datetime.datetime]]]:
        """Returns datetime objects representing temporal extents.

        Returns:
            Iterable[Tuple[datetime.datetime, Optional[datetime.datetime]]]:
                An iterable of tuples representing temporal extents.

        Raises:
            ValueError: If the temporal interval start is not found.
        """
        for stac_interval in self.stac_json["extent"]["temporal"]["interval"]:
            if not stac_interval[0]:
                raise ValueError(
                    "Expected a non-empty temporal interval start for "
                    + self.public_id()
                )
            start_date = iso8601.parse_date(stac_interval[0])
            if stac_interval[1] is not None:
                end_date = iso8601.parse_date(stac_interval[1])
            else:
                end_date = None
            yield (start_date, end_date)

    def start(self) -> datetime.datetime:
        """Gets the start datetime of the collection.

        Returns:
            datetime.datetime: The start datetime of the collection.
        """
        return list(self.datetime_interval())[0][0]

    def start_str(self) -> str:
        """Gets the start datetime of the collection as a string.

        Returns:
            str: The start datetime of the collection as a string.
        """
        if not self.start():
            return ""
        return self.start().strftime("%Y-%m-%d")

    def end(self) -> Optional[datetime.datetime]:
        """Gets the end datetime of the collection.

        Returns:
            Optional[datetime.datetime]: The end datetime of the collection.
        """
        return list(self.datetime_interval())[0][1]

    def end_str(self) -> str:
        """Gets the end datetime of the collection as a string.

        Returns:
            str: The end datetime of the collection as a string.
        """
        if not self.end():
            return ""
        return self.end().strftime("%Y-%m-%d")

    def bbox_list(self) -> Sequence[BBox]:
        """Gets the bounding boxes of the collection.

        Returns:
            Sequence[BBox]: A sequence of bounding boxes.
        """
        if "extent" not in self.stac_json:
            # Assume global if nothing listed.
            return (BBox(-180, -90, 180, 90),)
        return tuple(
            [BBox.from_list(x) for x in self.stac_json["extent"]["spatial"]["bbox"]]
        )

    def bands(self) -> List[Dict[str, Any]]:
        """Gets the bands of the collection.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing the bands.
        """
        summaries = self.stac_json.get("summaries")
        if not summaries:
            return []
        return summaries.get("eo:bands", [])

    def spatial_resolution_m(self) -> float:
        """Gets the spatial resolution of the collection in meters.

        Returns:
            float: The spatial resolution of the collection in meters.
        """
        summaries = self.stac_json.get("summaries")
        if not summaries:
            return -1
        if summaries.get("gsd"):
            return summaries.get("gsd")[0]

        # Fallback for cases where the stac does not follow convention.
        gsd_lst = re.findall(r'"gsd": (\d+)', json.dumps(self.stac_json))

        if len(gsd_lst) > 0:
            return float(gsd_lst[0])

        return -1

    def temporal_resolution_str(self) -> str:
        """Gets the temporal resolution of the collection as a string.

        Returns:
            str: The temporal resolution of the collection as a string.
        """
        interval_dict = self.stac_json.get("gee:interval")
        if not interval_dict:
            return ""
        return f"{interval_dict['interval']} {interval_dict['unit']}"

    def python_code(self) -> str:
        """Gets the Python code sample for the collection.

        Returns:
            str: The Python code sample for the collection.
        """
        code = self.stac_json.get("code")
        if not code:
            return ""

        return code.get("py_code")

    def set_python_code(self, code: str) -> None:
        """Sets the Python code sample for the collection.

        Args:
            code (str): The Python code sample to set.
        """
        if not code:
            self.stac_json["code"] = {"js_code": "", "py_code": code}

        self.stac_json["code"]["py_code"] = code

    def set_js_code(self, code: str) -> None:
        """Sets the JavaScript code sample for the collection.

        Args:
            code (str): The JavaScript code sample to set.
        """
        if not code:
            return ""
        js_code = self.stac_json.get("code").get("js_code")
        self.stac_json["code"] = {"js_code": "", "py_code": code}

    def image_preview_url(self) -> str:
        """Gets the URL of the preview image for the collection.

        Returns:
            str: The URL of the preview image for the collection.

        Raises:
            ValueError: If no preview image is found.
        """
        for link in self.stac_json["links"]:
            if (
                "rel" in link
                and link["rel"] == "preview"
                and link["type"] == "image/png"
            ):
                return link["href"]
        raise ValueError(f"No preview image found for {id}")

    def catalog_url(self) -> str:
        """Gets the URL of the catalog for the collection.

        Returns:
            str: The URL of the catalog for the collection.
        """
        links = self.stac_json["links"]
        for link in links:
            if "rel" in link and link["rel"] == "catalog":
                return link["href"]

            # Ideally there would be a 'catalog' link but sometimes there isn't.
            base_url = "https://developers.google.com/earth-engine/datasets/catalog/"
            if link["href"].startswith(base_url):
                return link["href"].split("#")[0]

        logging.warning(f"No catalog link found for {self.public_id()}")
        return ""


# @title class CollectionList()
class CollectionList(Sequence[Collection]):
    """List of stac.Collections; can be filtered to return a smaller sublist."""

    _collections = Sequence[Collection]

    def __init__(self, collections: Sequence[Collection]):
        self._collections = tuple(collections)

    def __iter__(self):
        return iter(self._collections)

    def __getitem__(self, index):
        return self._collections[index]

    def __len__(self):
        return len(self._collections)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CollectionList):
            return self._collections == other._collections
        return False

    def __hash__(self) -> int:
        return hash(self._collections)

    def filter_by_ids(self, ids: Iterable[str]):
        """Returns a sublist with only the collections matching the given ids."""
        return self.__class__([c for c in self._collections if c.public_id() in ids])

    def filter_by_datetime(
        self,
        query_datetime: datetime.datetime,
    ):
        """Returns a sublist with the time interval matching the given time."""
        result = []
        for collection in self._collections:
            for datetime_interval in collection.datetime_interval():
                if matches_datetime(datetime_interval, query_datetime):
                    result.append(collection)
                    break
        return self.__class__(result)

    def filter_by_interval(
        self,
        query_interval: tuple[datetime.datetime, datetime.datetime],
    ):
        """Returns a sublist with the time interval matching the given interval."""
        result = []
        for collection in self._collections:
            for datetime_interval in collection.datetime_interval():
                if matches_interval(datetime_interval, query_interval):
                    result.append(collection)
                    break
        return self.__class__(result)

    def filter_by_bounding_box_list(self, query_bbox: BBox):
        """Returns a sublist with the bbox matching the given bbox."""
        result = []
        for collection in self._collections:
            for collection_bbox in collection.bbox_list():
                if collection_bbox.intersects(query_bbox):
                    result.append(collection)
                    break
        return self.__class__(result)

    def filter_by_bounding_box(self, query_bbox: BBox):
        """Returns a sublist with the bbox matching the given bbox."""
        result = []
        for collection in self._collections:
            for collection_bbox in collection.bbox_list():
                if collection_bbox.intersects(query_bbox):
                    result.append(collection)
                    break
        return self.__class__(result)

    def start_str(self) -> datetime.datetime:
        return self.start().strftime("%Y-%m-%d")

    def sort_by_spatial_resolution(self, reverse=False):
        """
        Sorts the collections based on their spatial resolution.
        Collections with spatial_resolution_m() == -1 are pushed to the end.

        Args:
            reverse (bool): If True, sort in descending order (highest resolution first).
                            If False (default), sort in ascending order (lowest resolution first).

        Returns:
            CollectionList: A new CollectionList instance with sorted collections.
        """

        def sort_key(collection):
            resolution = collection.spatial_resolution_m()
            if resolution == -1:
                return float("inf") if not reverse else float("-inf")
            return resolution

        sorted_collections = sorted(self._collections, key=sort_key, reverse=reverse)
        return self.__class__(sorted_collections)

    def limit(self, n: int):
        """
        Returns a new CollectionList containing the first n entries.

        Args:
            n (int): The number of entries to include in the new list.

        Returns:
            CollectionList: A new CollectionList instance with at most n collections.
        """
        return self.__class__(self._collections[:n])

    def to_df(self):
        """Converts a collection list to a dataframe with a select set of fields."""

        rows = []
        for col in self._collections:
            # Remove text in parens in dataset name.
            short_title = re.sub(r"\([^)]*\)", "", col.get("title")).strip()

            row = {
                "id": col.public_id(),
                "name": short_title,
                "temp_res": col.temporal_resolution_str(),
                "spatial_res_m": col.spatial_resolution_m(),
                "earliest": col.start_str(),
                "latest": col.end_str(),
                "url": col.catalog_url(),
            }
            rows.append(row)
        return pd.DataFrame(rows)


class Catalog:
    """Class containing all collections in the EE STAC catalog."""

    collections: CollectionList

    def __init__(self, storage_client: storage.Client) -> None:
        """Initializes the Catalog with collections loaded from Google Cloud Storage.

        Args:
            storage_client (storage.Client): The Google Cloud Storage client.
        """
        self.collections = CollectionList(self._load_collections(storage_client))

    def get_collection(self, id: str) -> Collection:
        """Returns the collection with the given id.

        Args:
            id (str): The ID of the collection.

        Returns:
            Collection: The collection with the given ID.

        Raises:
            ValueError: If no collection with the given ID is found.
        """
        col = self.collections.filter_by_ids([id])
        if len(col) == 0:
            raise ValueError(f"No collection with id {id}")
        return col[0]

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(5),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        retry=tenacity.retry_if_exception_type(
            (
                google_exceptions.GoogleAPICallError,
                google_exceptions.RetryError,
                ConnectionError,
            )
        ),
        before_sleep=lambda retry_state: print(
            f"Error occurred: {str(retry_state.outcome.exception())}\n"
            f"Retrying in {retry_state.next_action.sleep} seconds... "
            f"(Attempt {retry_state.attempt_number}/3)"
        ),
    )
    def _read_file(self, file_blob: storage.Blob) -> Collection:
        """Reads the contents of a file from the specified bucket.

        Args:
            file_blob (storage.Blob): The blob representing the file.

        Returns:
            Collection: The collection created from the file contents.
        """
        file_contents = file_blob.download_as_string().decode()
        return Collection(json.loads(file_contents))

    def _read_files(self, file_blobs: List[storage.Blob]) -> List[Collection]:
        """Processes files in parallel.

        Args:
            file_blobs (List[storage.Blob]): The list of file blobs.

        Returns:
            List[Collection]: The list of collections created from the file contents.
        """
        collections = []
        with futures.ThreadPoolExecutor(max_workers=10) as executor:
            file_futures = [
                executor.submit(self._read_file, file_blob) for file_blob in file_blobs
            ]
            for future in file_futures:
                collections.append(future.result())
        return collections

    def _load_collections(self, storage_client: storage.Client) -> Sequence[Collection]:
        """Loads all EE STAC JSON files from GCS, with datetimes as objects.

        Args:
            storage_client (storage.Client): The Google Cloud Storage client.

        Returns:
            Sequence[Collection]: A tuple of collections loaded from the files.
        """
        bucket = storage_client.get_bucket("earthengine-stac")
        files = [
            x
            for x in bucket.list_blobs(prefix="catalog/")
            if x.name.endswith(".json")
            and not x.name.endswith("/catalog.json")
            and not x.name.endswith("/units.json")
        ]
        logging.warning("Found %d files, loading...", len(files))
        collections = self._read_files(files)

        code_samples_dict = self._load_all_code_samples(storage_client)

        res = []
        for c in collections:
            if c.is_deprecated():
                continue
            c.stac_json["code"] = code_samples_dict.get(c.hyphen_id())
            res.append(c)
        logging.warning("Loaded %d collections (skipping deprecated ones)", len(res))
        # Returning a tuple for immutability.
        return tuple(res)

    def _load_all_code_samples(
        self, storage_client: storage.Client
    ) -> Dict[str, Dict[str, str]]:
        """Loads js + py example scripts from GCS into dict keyed by dataset ID.

        Args:
            storage_client (storage.Client): The Google Cloud Storage client.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary mapping dataset IDs to their code samples.
        """

        # Get json file from GCS bucket
        # 'gs://earthengine-catalog/catalog/example_scripts.json'
        bucket = storage_client.get_bucket("earthengine-catalog")
        blob = bucket.blob("catalog/example_scripts.json")
        file_contents = blob.download_as_string().decode()
        data = json.loads(file_contents)

        # Flatten json to get a map from ID (using '_' rather than '/') to code
        # sample.
        all_datasets_by_provider = data[0]["contents"]
        code_samples_dict = {}
        for provider in all_datasets_by_provider:
            for dataset in provider["contents"]:
                js_code = dataset["code"]
                py_code = self._make_python_code_sample(js_code)

                code_samples_dict[dataset["name"]] = {
                    "js_code": js_code,
                    "py_code": py_code,
                }

        return code_samples_dict

    def _make_python_code_sample(self, js_code: str) -> str:
        """Converts EE JS code into python.

        Args:
            js_code (str): The JavaScript code to convert.

        Returns:
            str: The converted Python code.
        """

        # geemap appears to have some stray print statements.
        _ = io.StringIO()
        with redirect_stdout(_):
            code_list = js_snippet_to_py(
                js_code,
                add_new_cell=False,
                import_ee=False,
                import_geemap=False,
                show_map=False,
            )
        return "".join(code_list)


# @title Embeddings classes and helper methods


class PrecomputedEmbeddings(Embeddings):
    """Class for handling precomputed embeddings."""

    def __init__(self, embeddings_dict: Dict[str, List[float]]) -> None:
        """Initializes the PrecomputedEmbeddings.

        Args:
            embeddings_dict (Dict[str, List[float]]): A dictionary mapping texts to their embeddings.
        """
        self.embeddings_dict = embeddings_dict
        self.model = TextEmbeddingModel.from_pretrained("google/text-embedding-004")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embeds a list of documents.

        Args:
            texts (List[str]): The list of texts to embed.

        Returns:
            List[List[float]]: The list of embeddings.
        """
        return [self.embeddings_dict[text] for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """Embeds a query text.

        Args:
            text (str): The query text to embed.

        Returns:
            List[float]: The embedding of the query text.
        """
        embeddings = self.model.get_embeddings([text])
        return embeddings[0].values


def make_langchain_index(embeddings_df: pd.DataFrame) -> VectorStoreIndexWrapper:
    """Creates an index from a dataframe of precomputed embeddings.

    Args:
        embeddings_df (pd.DataFrame): The dataframe containing precomputed embeddings.

    Returns:
        VectorStoreIndexWrapper: The vector store index wrapper.
    """
    # Create a dictionary mapping texts to their embeddings
    embeddings_dict = dict(zip(embeddings_df["id"], embeddings_df["embedding"]))

    # Create our custom embeddings class
    precomputed_embeddings = PrecomputedEmbeddings(embeddings_dict)

    # Create Langchain Document objects
    documents = []
    for index, row in embeddings_df.iterrows():
        page_content = row["id"]
        metadata = {"summary": row["summary"], "name": row["name"]}
        documents.append(Document(page_content=page_content, metadata=metadata))

    # Create the VectorstoreIndexCreator
    index_creator = VectorstoreIndexCreator(embedding=precomputed_embeddings)

    # Create the index
    return index_creator.from_documents(documents)


# Wrap Langchain embeddings in our own EE dataset wrapper
class EarthEngineDatasetIndex:
    """Class for indexing and searching Earth Engine datasets."""

    index: VectorStoreIndexWrapper
    vectorstore: VectorStore
    data_catalog: Catalog
    llm: BaseLanguageModel

    def __init__(self, data_catalog, index, llm):
        """Initializes the EarthEngineDatasetIndex.

        Args:
            data_catalog (Catalog): The data catalog containing the datasets.
            index (VectorStoreIndexWrapper): The vector store index wrapper.
            llm (BaseLanguageModel): The language model for query processing.
        """
        self.index = index
        self.data_catalog = data_catalog
        self.vectorstore = index.vectorstore
        self.llm = llm

    @tenacity.retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(
            (requests.exceptions.RequestException, ConnectionError)
        ),
    )
    def find_top_matches(
        self,
        query: str,
        results: int = 10,
        threshold: float = 0.7,
        bounding_box: Optional[List[float]] = None,
        temporal_interval: Optional[Tuple[datetime.datetime, datetime.datetime]] = None,
    ) -> CollectionList:
        """Retrieve relevant datasets from the Earth Engine data catalog.

        Args:
            query (str): The kind of data being searched for, e.g., 'population'.
            results (int): The number of datasets to return. Defaults to 10.
            threshold (float): The maximum dot product between the query and catalog embeddings.
                Defaults to 0.7.
            bounding_box (Optional[List[float]]): The spatial bounding box for the query,
                in the format [lon1, lat1, lon2, lon2]. Defaults to None.
            temporal_interval (Optional[Tuple[datetime.datetime, datetime.datetime]]):
            Temporal constraints as a tuple of datetime objects. Defaults to None.

        Returns:
            CollectionList: A list of collections that match the query.
        """
        similar_docs = self.index.vectorstore.similarity_search_with_score(
            query, llm=self.llm, k=results
        )
        dataset_ids = [doc[0].page_content for doc in similar_docs]
        datasets = self.data_catalog.collections.filter_by_ids(dataset_ids)
        return datasets

    @tenacity.retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(
            (requests.exceptions.RequestException, ConnectionError)
        ),
    )
    def find_top_matches_with_score_df(
        self,
        query: str,
        results: int = 20,
        threshold: float = 0.7,
        bounding_box: Optional[List[float]] = None,
        temporal_interval: Optional[Tuple[datetime.datetime, datetime.datetime]] = None,
    ) -> pd.DataFrame:
        """Retrieve relevant datasets and their match scores as a DataFrame.

        Args:
            query (str): The kind of data being searched for, e.g., 'population'.
            results (int): The number of datasets to return. Defaults to 20.
            threshold (float): The maximum dot product between the query and catalog embeddings.
                Defaults to 0.7.
            bounding_box (Optional[List[float]]): The spatial bounding box for the query,
                in the format [lon1, lat1, lon2, lon2]. Defaults to None.
            temporal_interval (Optional[Tuple[datetime.datetime, datetime.datetime]]):
                Temporal constraints as a tuple of datetime objects. Defaults to None.

        Returns:
            pd.DataFrame: A DataFrame containing the dataset IDs and their match scores.
        """
        scores_df = self.ids_to_match_scores_df(
            query, results, bounding_box, temporal_interval
        )
        dataset_ids = scores_df["id"].tolist()
        col_list = self.data_catalog.collections.filter_by_ids(dataset_ids)
        collection_df = col_list.to_df()
        df = pd.merge(collection_df, scores_df, on="id", how="inner")
        return df.sort_values(by="match_score", ascending=False)

    def ids_to_match_scores_df(
        self,
        query: str,
        results: int,
        bounding_box: Optional[List[float]] = None,
        temporal_interval: Optional[Tuple[datetime.datetime, datetime.datetime]] = None,
    ) -> pd.DataFrame:
        """Convert dataset IDs and match scores to a DataFrame.

        Args:
            query (str): The kind of data being searched for, e.g., 'population'.
            results (int): The number of datasets to return.
            bounding_box (Optional[List[float]]): The spatial bounding box for the query,
                in the format [lon1, lat1, lon2, lon2]. Defaults to None.
            temporal_interval (Optional[Tuple[datetime.datetime, datetime.datetime]]):
                Temporal constraints as a tuple of datetime objects. Defaults to None.

        Returns:
            pd.DataFrame: A DataFrame containing the dataset IDs and their match scores.
        """
        similar_docs = self.index.vectorstore.similarity_search_with_score(
            query, llm=self.llm, k=results
        )
        dataset_ids, scores = zip(
            *[(doc[0].page_content, doc[1]) for doc in similar_docs]
        )

        return pd.DataFrame({"id": dataset_ids, "match_score": scores})


def explain_relevance(
    query: str,
    dataset_id: str,
    catalog: Catalog,
    model_name: str = "gemini-1.5-pro-latest",
    stream: bool = False,
) -> str:
    """Prompts LLM to explain the relevance of a dataset to a query.

    Args:
        query (str): The user's query.
        dataset_id (str): The ID of the dataset.
        catalog (Catalog): The catalog containing the dataset.
        model_name (str): The name of the model to use. Defaults to "gemini-1.5-pro-latest".
        stream (bool): Whether to stream the response. Defaults to False.

    Returns:
        str: The explanation of the dataset's relevance to the query.
    """

    stac_json = catalog.get_collection(dataset_id).stac_json
    return explain_relevance_from_stac_json(query, stac_json, model_name, stream)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(
        (requests.exceptions.RequestException, ConnectionError)
    ),
)
def explain_relevance_from_stac_json(
    query: str,
    stac_json: Dict[str, Any],
    model_name: str = "gemini-1.5-pro-latest",
    stream: bool = False,
) -> str:
    """Prompts LLM to explain the relevance of a dataset to a query using its STAC JSON.

    Args:
        query (str): The user's query.
        stac_json (Dict[str, Any]): The STAC JSON of the dataset.
        model_name (str): The name of the model to use. Defaults to "gemini-1.5-pro-latest".
        stream (bool): Whether to stream the response. Defaults to False.

    Returns:
        str: The explanation of the dataset's relevance to the query.
    """
    stac_json_str = json.dumps(stac_json)

    prompt = f"""
  I am an Earth Engine user contemplating using a dataset to support
  my investigation of the following query. Provide a concise, paragraph-long
  summary explaining why this dataset may be a good fit for my use case.
  If it does not seem like an appropriate dataset, say so.
  If relevant, call attention to a max of 3 bands that may be of particular interest.
  Weigh the tradeoffs between temporal and spatial resolution, particularly
  if the original query specifies regions of interest, time periods, or
  frequency of data collection. If I have not specified any
  spatial constraints, do your best based on the nature of their query. For example,
  if I'm wanting to study something small, like buildings, I will likely need good spatial resolution.

  Here is the original query:
  {query}

  Here is the stac json metadata for the dataset:
  {stac_json_str}
  """
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt, stream=stream)
    if stream:
        return response
    return response.text


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(
        (requests.exceptions.RequestException, ConnectionError)
    ),
)
def is_valid_question(question: str, model_name: str = "gemini-1.5-pro-latest") -> bool:
    """Filters out questions that cannot be answered by a dataset search tool.

    Args:
        question (str): The user's question.
        model_name (str): The name of the model to use. Defaults to "gemini-1.5-pro-latest".

    Returns:
        bool: True if the question is valid, False otherwise.
    """

    prompt = f"""
  You are a tool whose job is to determine whether or not the following question
  relates even in a small way to geospatial datasets.  Please provide a single
  word answer either True or False.

  For example, if the original query is "hello" - you should answer False. If
  the original query is "cheese futures" you should still answer True because
  the user could be interested in cheese production, and therefore agricultural
  land where cattle might be raised.

  Here is the original query:
  {question}
  """
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    # Err on the side of returning True
    return response.text.lower().strip() != "false"


class CodeThoughts(typing_extensions.TypedDict):
    code: str
    thoughts: str


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(
        (requests.exceptions.RequestException, ConnectionError)
    ),
)
def fix_ee_python_code(
    code: str, ee: Any, geemap_instance: Map, model_name: str = "gemini-1.5-pro-latest"
) -> str:
    """Asks a model to do ee python code correction in the event of error.

    Args:
        code (str): The Earth Engine Python code to fix.
        ee (Any): The Earth Engine module.
        geemap_instance (Map): The geemap instance.
        model_name (str): The name of the model to use. Defaults to "gemini-1.5-pro-latest".

    Returns:
        str: The corrected Earth Engine Python code.
    """

    def create_error_prompt(code: str, error_msg: str) -> str:
        return f"""
      You are an extremely laconic code correction robot.
      I am attempting to execute the following snippet of python Earth Engine code,
      using a geemap instance:

      ```
        {code}
      ```

      I have encountered the following error, please fix it. In 1-2 sentences,
      explain your debugging thought process in the 'thoughts' field. Note that
      the setOptions method exists only in the ee javascript library. Code
      referencing that method can be removed.

      Include the complete revised code snippet in the code field.
      Do not provide any other comentary in the code field. Do not add any new
      imports to the code snippet.

      {error_msg}
    """

    generation_config = {
        "response_mime_type": "application/json",
        "response_schema": CodeThoughts,
    }

    model = genai.GenerativeModel(model_name, generation_config=generation_config)

    max_attempts = 5
    total_attempts = 0
    broken = True
    while total_attempts < max_attempts and broken:
        try:
            run_ee_code(code, ee, geemap_instance)
            # logging.warning(f'Code success! after {total_attempts} try.')
            return code
        except Exception as e:
            logging.warning("Code execution error, asking Gemini for help.")

            gemini_json_fail = True
            while gemini_json_fail:
                response = model.generate_content(create_error_prompt(code, str(e)))
                try:
                    code_thoughts = json.loads(response.text)
                    gemini_json_fail = False
                except json.JSONDecodeError:
                    pass

            total_attempts += 1

            code = code_thoughts["code"]
            thoughts = code_thoughts["thoughts"]
            logging.warning(f"Gemini thoughts: \n{thoughts}")
            # logging.warning(f'Gemini new code: {code}')
            if total_attempts == max_attempts:
                raise Exception(e)
    logging.warning(f"Failed to fix code after {max_attempts} attempts.")


class DatasetSearchInterface:
    """Interface for searching and displaying Earth Engine datasets."""

    collections: CollectionList
    query: str
    dataset_table: widgets.Widget
    code_output: widgets.Widget
    details_output: widgets.Widget
    map_output: widgets.Widget
    geemap_instance: Map

    # Parent containers for controlling widget visibility.
    details_code_box: widgets.Widget
    map_widget: widgets.Widget

    def __init__(self, query: str, collections: CollectionList) -> None:
        """Initializes the DatasetSearchInterface.

        Args:
            query (str): The search query string.
            collections (CollectionList): The list of dataset collections.
        """

        self.query = query
        self.collections = collections

        # Create the output widgets
        self.code_output = widgets.Output(layout=widgets.Layout(width="50%"))
        self.details_output = widgets.Output(
            layout=widgets.Layout(height="300px", width="100%")
        )

        # Initialize dataset table
        table_html = self._build_table_html(collections)
        self.dataset_table = widgets.HTML(value=table_html)

        _callback_id = "dataset-select" + str(uuid.uuid4())
        output.register_callback(_callback_id, self.update_outputs)
        self._dataset_select_js_code = self._dataset_select_js_code(_callback_id)
        # self._dataset_select_js_code(_callback_id)

        # Initialize map
        self.map_output = widgets.Output(layout=widgets.Layout(width="100%"))
        self.geemap_instance = Map(height="600px", width="100%")

    def display(self):
        """Display the UI in the cell."""
        # Create title and description with Material Design styling
        # title = widgets.HTML(value='<h2 class="main-title">Earth Engine Dataset Explorer</h2>')

        # Wrap outputs in a widget box for border styling
        details_widget = widgets.Box(
            [self.details_output],
            layout=widgets.Layout(
                border="1px solid #E0E0E0", padding="10px", margin="5px", width="100%"
            ),
        )
        code_widget = widgets.Box(
            [self.code_output],
            layout=widgets.Layout(
                border="1px solid #E0E0E0", padding="10px", margin="5px", width="100%"
            ),
        )
        self.map_widget = widgets.Box(
            [self.map_output],
            layout=widgets.Layout(
                border="1px solid #E0E0E0",
                padding="10px",
                margin="5px",
                width="100%",
                height="600x",
            ),
        )

        # Create the vertical box for code and details
        self.details_code_box = widgets.VBox(
            [details_widget, code_widget],
            layout=widgets.Layout(width="50%", height="600px"),
        )

        # Create a horizontal box for map and details/code
        map_details_code_box = widgets.HBox(
            [self.map_widget, self.details_code_box],
            layout=widgets.Layout(
                border="1px solid #E0E0E0", padding="10px", margin="5px"
            ),
        )

        # Create the main layout with Material Design styling
        main_content = widgets.VBox(
            [self.dataset_table, map_details_code_box],
            layout=widgets.Layout(
                width="100%", border="1px solid #E0E0E0", padding="10px", margin="5px"
            ),
        )

        # Add debug panel to the main layout
        main_layout = widgets.VBox(
            [
                # title,
                main_content,
            ],
            layout=widgets.Layout(height="1500px", width="100%", padding="24px"),
        )

        # @title CSS
        # Custom CSS for Material Design styling with enhanced table styling, chat panel, and debug panel
        CSS = syntax.css(
            """
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap');

        body {
            font-family: 'Roboto', sans-serif;
            margin: 0;
            padding: 0;
        }

        .main-title {
            font-size: 24px;
            font-weight: 500;
            color: #212121;
            margin-bottom: 16px;
        }

        .custom-title {
            font-size: 18px;
            font-weight: 500;
            color: #212121;
            margin-bottom: 12px;
        }

        .details-text {
            font-size: 14px;
            color: #616161;
            line-height: 1.5;
        }

        .custom-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 24px;
            font-family: 'Roboto', sans-serif;
        }
        .custom-table th, .custom-table td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #E0E0E0;
        }
        .custom-table th {
            background-color: #F5F5F5;
            font-weight: 500;
            color: #212121;
        }
        .custom-table tr:hover {
            background-color: #E3F2FD;
        }
        .custom-table tr.selected {
            background-color: #BBDEFB;
        }

        /* Ensure borders are visible */
        .jupyter-widgets.widget-box {
            border: 1px solid #E0E0E0 !important;
            overflow: auto;
        }

        /* Make the map span full width */
        .geemap-container {
            width: 100% !important;
            height: 600px !important;
        }

        # Disable table clicks while things are loading
        .disabled {
        pointer-events: none;
        /* You might also want to visually indicate the disabled state */
        opacity: 0.5;
        cursor: default;
        }
        """
        )

        # Display the widget
        display(HTML(f"<style>{CSS}</style>"))
        display(main_layout)
        display(Javascript(self._dataset_select_js_code))

    def _build_table_html(self, collections: CollectionList) -> str:
        """Builds the HTML for the dataset table.

        Args:
            collections (CollectionList): The list of dataset collections.

        Returns:
            str: The HTML string for the dataset table.
        """
        table_html = """
    <table class="custom-table">
        <tr>
            <th>Dataset ID</th>
            <th> Name </th>
            <th>Temporal Resolution</th>
            <th>Spatial Resolution (m)</th>
            <th>Earliest</th>
            <th>Latest</th>
        </tr>
    """
        for dataset in collections:
            table_html += f"""
        <tr data-dataset="{dataset.public_id()}">
            <td>{dataset.public_id()}</td>
            <td>{dataset.get('title')}</td>
            <td>{dataset.temporal_resolution_str()}</td>
            <td>{dataset.spatial_resolution_m()}</td>
            <td>{dataset.start_str()}</td>
            <td>{dataset.end_str()}</td>
        </tr>
        """

        table_html += "</table>"
        return table_html

    def update_outputs(self, selected_dataset: str) -> None:
        """Updates the output widgets based on the selected dataset.

        Args:
            selected_dataset (str): The ID of the selected dataset.
        """
        collection = self.collections.filter_by_ids([selected_dataset])

        if not collection:
            self.details_code_box.layout.visibility = "hidden"
            self.map_widget.layout.visibility = "hidden"
            return

        dataset = collection[0]

        # Clear everything when a new dataset is selected.
        self.map_output.clear_output()
        self.code_output.clear_output()
        self.details_output.clear_output()
        # Clear previous layers. Keep only the base layer
        self.geemap_instance.layers = self.geemap_instance.layers[:1]

        with self.map_output:
            display(HTML("<h3>Loading...</h3>"))
            code = fix_ee_python_code(dataset.python_code(), ee, self.geemap_instance)
            llm_thoughts = explain_relevance_from_stac_json(
                self.query, dataset.stac_json
            )

        # Code and LLM thought content is now fully loaded.
        # We ought to make this asynchronous in another version
        self.map_output.clear_output()

        with self.code_output:
            display(HTML('<div class="custom-title">Earth Engine Code</div>'))
            print(code)

        with self.details_output:
            # display(HTML('<h3>Thinking...</h3>'))
            # self.details_output.clear_output()
            display(HTML('<div class="custom-title">Thoughts with Gemini</div>'))
            print(llm_thoughts)

        with self.map_output:
            display(self.geemap_instance)

        self.details_code_box.layout.visibility = "visible"
        self.map_widget.layout.visibility = "visible"

    def _dataset_select_js_code(self, callback_id: str) -> str:
        """Generates JavaScript code for handling dataset selection.

        Args:
            callback_id (str): The callback ID for the dataset selection.

        Returns:
            str: The JavaScript code as a string.
        """
        return Template(
            syntax.javascript(
                """
    function initializeTableInteraction() {
        const table = document.querySelector('.custom-table');
        if (!table) {
            console.error('Table not found');
            return;
        }

        function selectRow(row) {
            // Remove selection from previously selected row
            const prevSelected = table.querySelector('tr.selected');
            if (prevSelected) prevSelected.classList.remove('selected');

            // Add selection to the new row
            row.classList.add('selected');
            const selectedDataset = row.dataset.dataset;
            console.log('Selected dataset:', selectedDataset);
            google.colab.kernel.invokeFunction('{{callback_id}}', [selectedDataset], {});

        }

        table.addEventListener('click', (event) => {
            const row = event.target.closest('tr');
            if (!row || !row.dataset.dataset) return;
            selectRow(row);
        });

        // Select the first row by default
        const firstRow = table.querySelector('tr[data-dataset]');
        if (firstRow) {
            selectRow(firstRow);
        }
    }

    // Run the initialization function after a short delay to ensure the DOM is ready
    setTimeout(initializeTableInteraction, 1000);
    """
            )
        ).render(callback_id=callback_id)


class DatasetExplorer:
    """A widget for exploring Earth Engine datasets.
    The DataExplorer class source code is adapted from <https://bit.ly/48cE24D>.
    Credit to the original author Renee Johnston (<https://github.com/raj02006>)
    """

    def __init__(
        self,
        project_id: str = "GOOGLE_PROJECT_ID",
        google_api_key: str = "GOOGLE_API_KEY",
        vertex_ai_zone: str = "us-central1",
        model: str = "gemini-1.5-pro",
        embeddings_cloud_path: str = "gs://earthengine-catalog/embeddings/catalog_embeddings.jsonl",
    ) -> None:
        """Initializes the DatasetExplorer.

        Args:
            project_id (str): Google Cloud project ID. Defaults to "GOOGLE_PROJECT_ID".
            google_api_key (str): Google API key. Defaults to "GOOGLE_API_KEY".
            vertex_ai_zone (str): Vertex AI zone. Defaults to "us-central1".
            model (str): Model name for ChatGoogleGenerativeAI. Defaults to "gemini-1.5-pro".
            embeddings_cloud_path (str): Cloud path to the embeddings file.
                Defaults to "gs://earthengine-catalog/embeddings/catalog_embeddings.jsonl".
        """

        # @title Setup
        project_name = get_env_var(project_id)
        if project_name is None:
            project_name = get_env_var("EE_PROJECT_ID")
        if project_name is None:
            raise ValueError("Please provide a Google Cloud project ID.")

        genai.configure(api_key=get_env_var(google_api_key))

        ee.Authenticate()
        ee.Initialize(project=project_name)
        storage_client = storage.Client(project=project_name)
        vertexai.init(project=project_name, location=vertex_ai_zone)

        # Make sure geemap initialized correctly.
        ee_initialize(project=project_name)
        m = Map(draw_ctrl=False)
        m.add("layer_manager")

        catalog = Catalog(storage_client)

        # Pre-built embeddings.
        EMBEDDINGS_CLOUD_PATH = embeddings_cloud_path

        # Copy embeddings from GCS bucket to a local file
        EMBEDDINGS_LOCAL_PATH = "catalog_embeddings.jsonl"

        def load_embeddings(
            gcs_path=EMBEDDINGS_CLOUD_PATH, local_path=EMBEDDINGS_LOCAL_PATH
        ):
            parts = gcs_path.split("/")
            bucket_name = parts[2]
            blob_path = "/".join(parts[3:])
            bucket = storage_client.get_bucket(bucket_name)
            blob = bucket.blob(blob_path)
            blob.download_to_filename(local_path)
            return local_path

        # Load our embeddings data into a dataframe:
        local_path = load_embeddings(EMBEDDINGS_CLOUD_PATH, EMBEDDINGS_LOCAL_PATH)
        embeddings_df = pd.read_json(local_path, lines=True)

        llm = ChatGoogleGenerativeAI(
            model=model, google_api_key=get_env_var(google_api_key)
        )

        local_path = load_embeddings(EMBEDDINGS_CLOUD_PATH, EMBEDDINGS_LOCAL_PATH)
        embeddings_df = pd.read_json(local_path, lines=True)
        langchain_index = make_langchain_index(embeddings_df)

        self.ee_index = EarthEngineDatasetIndex(catalog, langchain_index, llm)

    def show(self, query: Optional[str] = None, **kwargs: Any) -> widgets.VBox:
        """Displays a query interface for searching datasets.

        Args:
            query (Optional[str]): The initial query string. Defaults to None.
            **kwargs (Any): Additional keyword arguments for widget styling.

        Returns:
            widgets.VBox: A VBox containing the query input and output display.
        """

        output.no_vertical_scroll()

        if "style" not in kwargs:
            kwargs["style"] = {"description_width": "initial"}
        if "layout" not in kwargs:
            kwargs["layout"] = widgets.Layout(width="98%")

        def Question(query: str) -> None:
            """Handles the query and displays the dataset search results.

            Args:
                query (str): The query string.
            """
            if not is_valid_question(query):
                print("Invalid question. Please try again.")
                return

            datasets = self.ee_index.find_top_matches(query)
            # datasets = datasets.sort_by_spatial_resolution().limit(5)
            datasets = datasets.limit(7)
            dataset_search = DatasetSearchInterface(query, datasets)
            dataset_search.display()

        if query is None:
            query = "How have global land surface temperatures changed over time?"

        query_widget = widgets.Text(
            value=query,
            placeholder="Type your query here and press Enter",
            description="Query:",
            tooltip="Type your query here and press Enter",
            **kwargs,
        )

        output_widget = widgets.Output()

        display_widget = widgets.VBox([query_widget, output_widget])

        def on_query_change(text: widgets.Text) -> None:
            """Handles the event when the query text is submitted.

            Args:
                text (widgets.Text): The text widget containing the query.
            """
            output_widget.clear_output()
            with output_widget:
                print("Loading ...")
                output_widget.clear_output(wait=True)
                Question(text.value)

        query_widget.on_submit(on_query_change)

        return display_widget
