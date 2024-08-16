import io
import json
import math
import os
import time

import numpy as np
import PIL
import requests

import ee
import ipywidgets as widgets
from IPython.display import display, HTML
from typing import Optional
from .common import get_api_key, temp_file_path
from .geemap import Map, ee_initialize

try:
    from google.cloud import storage

    import google.generativeai as genai
    import google.ai.generativelanguage as glm
    import google.api_core
except ImportError:
    print("Please install the required packages.")
    print("pip install google-cloud-storage google-generativeai google-api-core")


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
            project = get_api_key("EE_PROJECT_ID") or get_api_key("GOOGLE_PROJECT_ID")
        if project is None:
            raise ValueError(
                "Please provide a valid project ID via the 'project' parameter."
            )

        if google_api_key is None:
            google_api_key = get_api_key("GOOGLE_API_KEY")
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
