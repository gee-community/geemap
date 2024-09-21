""" Module for converting Google Earth Engine (GEE) JavaScripts to Python scripts and Jupyter notebooks.
- To convert a GEE JavaScript to Python script:                                       js_to_python(in_file out_file)
- To convert all GEE JavaScripts in a folder recursively to Python scripts:           js_to_python_dir(in_dir, out_dir)
- To convert a GEE Python script to Jupyter notebook:                                 py_to_ipynb(in_file, template_file, out_file)
- To convert all GEE Python scripts in a folder recursively to Jupyter notebooks:     py_to_ipynb_dir(in_dir, template_file, out_dir)
- To execute a Jupyter notebook and save output cells:                                execute_notebook(in_file)
- To execute all Jupyter notebooks in a folder recursively:                           execute_notebook_dir(in_dir)
"""

# *******************************************************************************#
# This module contains extra features of the geemap package.                     #
# The geemap community will maintain the extra features.                         #
# *******************************************************************************#


import os
import re
import shutil
import urllib.request
from collections import deque
from pathlib import Path

import pkg_resources

from .common import *


def find_matching_bracket(lines, start_line_index, start_char_index, matching_char="{"):
    """Finds the position of the matching closing bracket from a list of lines.

    Args:
        lines (list): The input list of lines.
        start_line_index (int): The line index where the starting bracket is located.
        start_char_index (int): The position index of the starting bracket.
        matching_char (str, optional): The starting bracket to search for. Defaults to '{'.

    Returns:
        matching_line_index (int): The line index where the matching closing bracket is located.
        matching_char_index (int): The position index of the matching closing bracket.
    """
    matching_line_index = -1
    matching_char_index = -1

    matching_chars = {"{": "}", "(": ")", "[": "]"}
    if matching_char not in matching_chars.keys():
        print(
            "The matching character must be one of the following: {}".format(
                ", ".join(matching_chars.keys())
            )
        )
        return matching_line_index, matching_char_index

    # Create a deque to use it as a stack.
    d = deque()

    for line_index in range(start_line_index, len(lines)):
        line = lines[line_index]
        # deal with the line where the starting bracket is located.
        if line_index == start_line_index:
            line = lines[line_index][start_char_index:]

        for index, item in enumerate(line):
            # Pops a starting bracket for each closing bracket
            if item == matching_chars[matching_char]:
                d.popleft()
            # Push all starting brackets
            elif item == matching_char:
                d.append(matching_char)

            # If deque becomes empty
            if not d:
                matching_line_index = line_index
                if line_index == start_line_index:
                    matching_char_index = start_char_index + index
                else:
                    matching_char_index = index

                return matching_line_index, matching_char_index

    return matching_line_index, matching_char_index


def format_params(line, sep=":"):
    """Formats keys in a dictionary and adds quotes to the keys.
    For example, {min: 0, max: 10} will result in ('min': 0, 'max': 10)

    Args:
        line (str): A string.
        sep (str, optional): Separator. Defaults to ':'.

    Returns:
        [str]: A string with keys quoted
    """
    # print(line)
    new_line = line
    prefix = ""
    # suffix = ""

    if line.strip().startswith("for"):  # skip for loop
        return line

    # find all occurrences of a substring
    def find_all(a_str, sub):
        start = 0
        while True:
            start = a_str.find(sub, start)
            if start == -1:
                return
            yield start
            start += len(sub)  # use start += 1 to find overlapping matches

    indices = list(find_all(line, sep))
    count = len(indices)

    if "{" in line:
        bracket_index = line.index("{")
        if bracket_index < indices[0]:
            prefix = line[: bracket_index + 1]
            line = line[bracket_index + 1 :]

    if count > 0:
        items = line.split(sep)

        if count == 1:
            for i in range(0, count):
                item = items[i].strip()
                if ('"' not in item) and ("'" not in item):
                    new_item = "'" + item + "'"
                    items[i] = items[i].replace(item, new_item)
            new_line = ":".join(items)
        elif count > 1:
            for i in range(0, count):
                item = items[i]
                if "," in item:
                    subitems = item.split(",")
                    subitem = subitems[-1]
                    if ('"' not in subitem) and ("'" not in subitem):
                        new_subitem = "'" + subitem.strip() + "'"
                        subitems[-1] = subitems[-1].replace(subitem, new_subitem)
                        items[i] = ", ".join(subitems)
                else:
                    if ('"' not in item) and ("'" not in item):
                        new_item = "'" + item.strip() + "'"
                        padding = len(item) - len(item.strip())
                        items[i] = " " * padding + item.replace(item, new_item)

            new_line = ":".join(items)

    return prefix + new_line


def use_math(lines):
    """Checks if an Earth Engine uses Math library

    Args:
        lines (list): An Earth Engine JavaScript.

    Returns:
        [bool]: Returns True if the script contains 'Math.'. For example 'Math.PI', 'Math.pow'
    """
    math_import = False
    for line in lines:
        if "Math." in line:
            math_import = True

    return math_import


def convert_for_loop(line):
    """Converts JavaScript for loop to Python for loop.

    Args:
        line (str): Input JavaScript for loop

    Returns:
        str: Converted Python for loop.
    """
    new_line = ""
    if "var " in line:
        line = line.replace("var ", "")
    start_index = line.index("(")
    end_index = line.index(")")

    prefix = line[:(start_index)]
    suffix = line[(end_index + 1) :]

    params = line[(start_index + 1) : end_index]

    if " in " in params and params.count(";") == 0:
        new_line = prefix + "{}:".format(params) + suffix
        return new_line

    items = params.split("=")
    param_name = items[0].strip()
    items = params.split(";")

    subitems = []

    for item in items:
        subitems.append(item.split(" ")[-1])

    start = subitems[0]
    end = subitems[1]
    step = subitems[2]

    if "++" in step:
        step = 1
    elif "--" in step:
        step = -1

    prefix = line[:(start_index)]
    suffix = line[(end_index + 1) :]
    new_line = (
        prefix
        + "{} in range({}, {}, {}):".format(param_name, start, end, step)
        + suffix
    )

    return new_line


# Removes all indentation from file to reformat indentation for python later
def remove_all_indentation(input_lines):
    """Removes all indentation for reformatting according to python's indentation rules

    Args:
        input_lines (list): List of Earth Engine JavaScrips

    Returns:
        list: Output JavaScript with indentation removed
    """
    output_lines = []
    for _, line in enumerate(input_lines):
        output_lines.append(line.lstrip())
    return output_lines


def check_map_functions(input_lines):
    """Extracts Earth Engine map function

    Args:
        input_lines (list): List of Earth Engine JavaScrips

    Returns:
        list: Output JavaScript with map function
    """
    output_lines = []
    currentNumOfNestedFuncs = 0
    for index, line in enumerate(input_lines):
        if (
            line.strip().endswith(".map(")
            and input_lines[index + 1].strip().replace(" ", "").startswith("function(")
        ) or (
            line.strip().endswith(".map(function(")
            and input_lines[index + 1].strip().replace(" ", "").endswith("{")
        ):
            input_lines[index + 1] = line + input_lines[index + 1]
            continue

        if (
            ".map(function" in line.replace(" ", "")
            or "returnfunction" in line.replace(" ", "")
            or "function(" in line.replace(" ", "")
        ):
            try:
                bracket_index = line.index("{")
                matching_line_index, matching_char_index = find_matching_bracket(
                    input_lines, index, bracket_index
                )

                func_start_index = line.index("function")
                func_name = "func_" + random_string()
                func_header = line[func_start_index:].replace(
                    "function", "function " + func_name
                )
                output_lines.append("\n")
                output_lines.append(func_header)

                currentNumOfNestedFuncs += 1

                new_lines = input_lines[index + 1 : matching_line_index]

                new_lines = check_map_functions(new_lines)

                for sub_index, tmp_line in enumerate(new_lines):
                    output_lines.append(("    " * currentNumOfNestedFuncs) + tmp_line)
                    if "{" in tmp_line:
                        currentNumOfNestedFuncs += 1
                    if "}" in tmp_line:
                        currentNumOfNestedFuncs -= 1
                    input_lines[index + 1 + sub_index] = ""

                currentNumOfNestedFuncs -= 1

                header_line = line[:func_start_index] + func_name
                header_line = header_line.rstrip()

                func_footer = input_lines[matching_line_index][
                    : matching_char_index + 1
                ]
                output_lines.append(func_footer)

                footer_line = input_lines[matching_line_index][
                    matching_char_index + 1 :
                ].strip()
                if footer_line == ")" or footer_line == ");":
                    header_line = header_line + footer_line
                    footer_line = ""

                input_lines[matching_line_index] = footer_line

                output_lines.append(header_line)
                # output_lines.append(footer_line)
            except Exception as e:
                print(
                    f"An error occurred: {e}. The closing curly bracket could not be found in Line {index+1}: {line}. Please reformat the function definition and make sure that both the opening and closing curly brackets appear on the same line as the function keyword. "
                )
        else:
            output_lines.append(line)

    return output_lines


def js_to_python(
    in_file,
    out_file=None,
    use_qgis=True,
    github_repo=None,
    show_map=True,
    import_geemap=False,
    Map="m",
):
    """Converts an Earth Engine JavaScript to Python script.

    Args:
        in_file (str): File path of the input JavaScript.
        out_file (str, optional): File path of the output Python script. Defaults to None.
        use_qgis (bool, optional): Whether to add "from ee_plugin import Map \n" to the output script. Defaults to True.
        github_repo (str, optional): GitHub repo url. Defaults to None.
        show_map (bool, optional): Whether to add "Map" to the output script. Defaults to True.
        import_geemap (bool, optional): Whether to add "import geemap" to the output script. Defaults to False.
        Map (str, optional): The name of the map variable. Defaults to "m".

    Returns:
        list: Python script
    """
    in_file = os.path.abspath(in_file)
    if out_file is None:
        out_file = in_file.replace(".js", ".py")

    root_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isfile(in_file):
        in_file = os.path.join(root_dir, in_file)
    if not os.path.isfile(out_file):
        out_file = os.path.join(root_dir, out_file)

    is_python = False
    # add_github_url = False

    if use_qgis and import_geemap:
        raise Exception(
            "use_qgis and import_geemap cannot be both True. Please set one of them to False."
        )

    import_str = ""
    if use_qgis:
        import_str = "from ee_plugin import Map\n"
    if import_geemap:
        import_str = f"import geemap\n\n{Map} = geemap.Map()\n"

    github_url = ""
    if github_repo is not None:
        github_url = "# GitHub URL: " + github_repo + in_file + "\n\n"

    math_import = False
    math_import_str = ""

    lines = []
    with open(in_file, encoding="utf-8") as f:
        lines = f.readlines()

        math_import = use_math(lines)

        for line in lines:
            line = line.strip()
            if line == "import ee":
                is_python = True

    if math_import:
        math_import_str = "import math\n"

    output = ""

    if is_python:  # only update the GitHub URL if it is already a GEE Python script
        output = github_url + "".join(map(str, lines))
    else:  # deal with JavaScript
        header = github_url + "import ee \n" + math_import_str + import_str
        # function_defs = []
        output = header + "\n"

        with open(in_file, encoding="utf-8") as f:
            lines = f.readlines()

            numIncorrectParameters = 0
            checkNextLineForPrint = False
            shouldCheckForEmptyLines = False
            currentDictionaryScopeDepth = 0
            currentNumOfNestedFuncs = 0

            # We need to remove all spaces from the beginning of each line to accurately format the indentation
            lines = remove_all_indentation(lines)

            # print('Processing {}'.format(in_file))
            lines = check_map_functions(lines)

            for index, line in enumerate(lines):

                if "Map.setOptions" in line:
                    # Regular expression to remove everything after the comma and before ');'
                    line = re.sub(r",[^)]+(?=\);)", "", line)

                if ("/* color" in line) and ("*/" in line):
                    line = (
                        line[: line.index("/*")].lstrip()
                        + line[(line.index("*/") + 2) :]
                    )

                if (
                    ("= function" in line)
                    or ("=function" in line)
                    or line.strip().startswith("function")
                ):
                    try:
                        bracket_index = line.index("{")

                        (
                            matching_line_index,
                            matching_char_index,
                        ) = find_matching_bracket(lines, index, bracket_index)

                        if "func_" not in line:
                            currentNumOfNestedFuncs += 1

                            for sub_index, tmp_line in enumerate(
                                lines[index + 1 : matching_line_index]
                            ):
                                # lines[sub_index] = ('    ' * currentNumOfNestedFuncs) + tmp_line
                                if "{" in tmp_line and "function" not in line:
                                    currentNumOfNestedFuncs += 1
                                if "}" in tmp_line and "function" not in line:
                                    currentNumOfNestedFuncs -= 1
                                lines[index + 1 + sub_index] = (
                                    "    " * currentNumOfNestedFuncs
                                ) + lines[index + 1 + sub_index]

                            currentNumOfNestedFuncs -= 1

                        line = line[:bracket_index] + line[bracket_index + 1 :]
                        if matching_line_index == index:
                            line = (
                                line[:matching_char_index]
                                + line[matching_char_index + 1 :]
                            )
                        else:
                            tmp_line = lines[matching_line_index]
                            lines[matching_line_index] = (
                                tmp_line[:matching_char_index]
                                + tmp_line[matching_char_index + 1 :]
                            )

                    except Exception as e:
                        print(
                            f"An error occurred when processing {in_file}. The closing curly bracket could not be found in Line {index+1}: {line}. Please reformat the function definition and make sure that both the opening and closing curly brackets appear on the same line as the function keyword. "
                        )
                        return

                    line = (
                        line.replace(" = function", "")
                        .replace("=function", "")
                        .replace("function ", "")
                    )
                    if line.lstrip().startswith("//"):
                        line = line.replace("//", "").lstrip()
                        line = (
                            " " * (len(line) - len(line.lstrip()))
                            + "# def "
                            + line.strip()
                            + ":"
                        )
                    else:
                        line = (
                            " " * (len(line) - len(line.lstrip()))
                            + "def "
                            + line.strip()
                            + ":"
                        )
                elif "{" in line and "({" not in line:
                    bracket_index = line.index("{")
                    (
                        matching_line_index,
                        matching_char_index,
                    ) = find_matching_bracket(lines, index, bracket_index)

                    currentNumOfNestedFuncs += 1

                    for sub_index, tmp_line in enumerate(
                        lines[index + 1 : matching_line_index]
                    ):
                        lines[index + 1 + sub_index] = (
                            "    " * currentNumOfNestedFuncs
                        ) + lines[index + 1 + sub_index]
                        if "{" in tmp_line and "if" not in line and "for" not in line:
                            currentNumOfNestedFuncs += 1
                        if "}" in tmp_line and "if" not in line and "for" not in line:
                            currentNumOfNestedFuncs -= 1

                    currentNumOfNestedFuncs -= 1

                    if (matching_line_index == index) and (":" in line):
                        pass
                    elif (
                        ("for (" in line)
                        or ("for(" in line)
                        or ("if (" in line)
                        or ("if(" in line)
                    ):
                        if "if" not in line:
                            line = convert_for_loop(line)
                        else:
                            start_index = line.index("(")
                            end_index = line.index(")")
                            line = "if " + line[start_index:end_index] + "):{"
                        lines[index] = line
                        bracket_index = line.index("{")
                        (
                            matching_line_index,
                            matching_char_index,
                        ) = find_matching_bracket(lines, index, bracket_index)
                        tmp_line = lines[matching_line_index]
                        lines[matching_line_index] = (
                            tmp_line[:matching_char_index]
                            + tmp_line[matching_char_index + 1 :]
                        )
                        line = line.replace("{", "")

                if line is None:
                    line = ""

                line = line.replace("//", "#")
                line = line.replace("var ", "", 1)
                line = line.replace("/*", "#")
                line = line.replace("*/", "#")
                line = line.replace("true", "True").replace("false", "False")
                line = line.replace("null", "None")
                line = line.replace(".or", ".Or")
                line = line.replace(".and", ".And")
                line = line.replace(".not", ".Not")
                line = line.replace("visualize({", "visualize(**{")
                line = line.replace("Math.PI", "math.pi")
                line = line.replace("Math.", "math.")
                line = line.replace("parseInt", "int")
                line = line.replace("NotNull", "notNull")
                line = line.replace("= new", "=")
                line = line.replace("exports.", "")
                line = line.replace("Map.", f"{Map}.")
                line = line.replace(
                    "Export.table.toDrive", "geemap.ee_export_vector_to_drive"
                )
                line = line.replace(
                    "Export.table.toAsset", "geemap.ee_export_vector_to_asset"
                )
                line = line.replace(
                    "Export.image.toAsset", "geemap.ee_export_image_to_asset"
                )
                line = line.replace(
                    "Export.video.toDrive", "geemap.ee_export_video_to_drive"
                )
                line = line.replace("||", "or")
                line = line.replace(r"\****", "#")
                line = line.replace("def =", "_def =")
                line = line.replace(", def, ", ", _def, ")
                line = line.replace("(def, ", "(_def, ")
                line = line.replace(", def)", ", _def)")
                line = line.replace("===", "==")

                # Replaces all javascript operators with python operators
                if "!" in line:
                    try:
                        if (line.replace(" ", ""))[line.find("!") + 1] != "=":
                            line = line.replace("!", "not ")
                    except:
                        print("continue...")

                line = line.rstrip()

                # If the function concat is used, replace it with python's concatenation
                if "concat" in line:
                    line = line.replace(".concat(", "+")
                    line = line.replace(",", "+")
                    line = line.replace(")", "")

                # Checks if an equal sign is at the end of a line. If so, add backslashes
                if shouldCheckForEmptyLines:
                    if line.strip() == "" or "#" in line:
                        if line.strip().endswith("["):
                            line = "["
                            shouldCheckForEmptyLines = False
                        else:
                            line = "\\"
                    else:
                        shouldCheckForEmptyLines = False

                if line.strip().endswith("="):
                    line = line + " \\"
                    shouldCheckForEmptyLines = True

                # Adds getInfo at the end of print statements involving maps
                endOfPrintReplaced = False

                if ("print(" in line and "=" not in line) or checkNextLineForPrint:
                    for i in range(len(line) - 1):
                        if line[len(line) - i - 1] == ")":
                            line = line[: len(line) - i - 1] + ".getInfo())"
                            # print(line)
                            endOfPrintReplaced = True
                            break
                    if endOfPrintReplaced:
                        checkNextLineForPrint = False
                    else:
                        checkNextLineForPrint = True

                # Removes potential commas after imports. Causes tuple type errors
                if line.endswith(","):
                    if "=" in lines[index + 1] and not lines[
                        index + 1
                    ].strip().startswith("'"):
                        line = line[:-1]

                # Changes object argument to individual parameters
                if (
                    line.strip().endswith("({")
                    and not "ee.Dictionary" in line
                    and not ".set(" in line
                    and ".addLayer" not in line
                    and "cast" not in line
                ):
                    line = line.rstrip()[:-1]
                    numIncorrectParameters = numIncorrectParameters + 1

                if numIncorrectParameters > 0:
                    if line.strip().startswith("})"):
                        line = line.replace("})", ")")
                        numIncorrectParameters = numIncorrectParameters - 1
                    else:
                        if currentDictionaryScopeDepth < 1:
                            line = line.replace(": ", "=")
                            line = line.replace(":", " =")

                if "= {" in line and "({" not in line:
                    currentDictionaryScopeDepth += 1

                if "}" in line and currentDictionaryScopeDepth > 0:
                    currentDictionaryScopeDepth -= 1

                # if ".style(" in line and ".style(**" not in line:
                #     line = line.replace(".style(", ".style(**")

                if line.endswith("+"):
                    line = line + " \\"
                elif line.endswith(";"):
                    line = line[:-1]

                if line.lstrip().startswith("*"):
                    line = line.replace("*", "#")

                if (
                    (":" in line)
                    and (not line.strip().startswith("#"))
                    and (not line.strip().startswith("def"))
                    and (not line.strip().startswith("."))
                    and (not line.strip().startswith("if"))
                ):
                    line = format_params(line)

                if (
                    index < (len(lines) - 1)
                    and line.lstrip().startswith("#")
                    and lines[index + 1].lstrip().startswith(".")
                ):
                    line = ""

                if (
                    "#" in line
                    and not line.strip().startswith("#")
                    and not line[line.index("#") - 1] == "'"
                ):
                    line = line[: line.index("#")]

                if line.lstrip().startswith("."):
                    if lines[index - 1].strip().endswith("\\") and lines[
                        index - 1
                    ].strip().startswith("#"):
                        lines[index - 1] = "\\"
                    if "#" in line:
                        line = line[: line.index("#")]
                    output = output.rstrip() + " " + "\\" + "\n" + line + "\n"
                else:
                    output += line + "\n"

    if show_map:
        output += Map

    out_dir = os.path.dirname(out_file)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(output)

    return output


def create_new_cell(contents, replace=False):
    """Create a new cell in Jupyter notebook based on the contents.

    Args:
        contents (str): A string of Python code.
    """
    from IPython.core.getipython import get_ipython

    shell = get_ipython()
    shell.set_next_input(contents, replace=replace)


def js_snippet_to_py(
    in_js_snippet,
    add_new_cell=True,
    import_ee=True,
    import_geemap=False,
    show_map=True,
    Map="m",
):
    """Converts an Earth Engine JavaScript snippet wrapped in triple quotes to Python directly on a Jupyter notebook.

    Args:
        in_js_snippet (str): Earth Engine JavaScript within triple quotes.
        add_new_cell (bool, optional): Whether add the converted Python to a new cell.
        import_ee (bool, optional): Whether to import ee. Defaults to True.
        import_geemap (bool, optional): Whether to import geemap. Defaults to False.
        show_map (bool, optional): Whether to show the map. Defaults to True.
        Map (str, optional): The name of the map variable. Defaults to "m".

    Returns:
        list: A list of Python script.
    """

    in_js = temp_file_path(".js")
    out_py = temp_file_path(".py")

    in_js_snippet = re.sub(
        r"([a-zA-Z0-9_]+)\s*:", r'"\1":', in_js_snippet
    )  # Add quotes around keys

    try:
        with open(in_js, "w") as f:
            f.write(in_js_snippet)
        js_to_python(
            in_js,
            out_file=out_py,
            use_qgis=False,
            show_map=show_map,
            import_geemap=import_geemap,
            Map=Map,
        )

        out_lines = []
        if import_ee:
            out_lines.append("import ee\n")
        # if import_geemap:
        #     out_lines.append("import geemap\n\n")
        #     out_lines.append(f"{Map} = geemap.Map()\n")

        with open(out_py, encoding="utf-8") as f:
            lines = f.readlines()
            for index, line in enumerate(lines):
                if index < (len(lines) - 1):
                    if line.strip() == "import ee":
                        continue

                    next_line = lines[index + 1]
                    if line.strip() == "" and next_line.strip() == "":
                        continue
                    elif ".style(" in line and (".style(**" not in line):
                        line = line.replace(".style(", ".style(**")
                        out_lines.append(line)
                    elif "({" in line:
                        line = line.replace("({", "(**{")
                        out_lines.append(line)
                    else:
                        out_lines.append(line)
                elif index == (len(lines) - 1) and lines[index].strip() != "":
                    out_lines.append(line)

        os.remove(in_js)
        os.remove(out_py)

        if add_new_cell:
            contents = "".join(out_lines).strip()
            create_new_cell(contents)
        else:
            return out_lines

    except Exception as e:
        print(e)


def js_to_python_dir(
    in_dir,
    out_dir=None,
    use_qgis=True,
    github_repo=None,
    import_geemap=False,
    Map="m",
):
    """Converts all Earth Engine JavaScripts in a folder recursively to Python scripts.

    Args:
        in_dir (str): The input folder containing Earth Engine JavaScripts.
        out_dir (str, optional): The output folder containing Earth Engine Python scripts. Defaults to None.
        use_qgis (bool, optional): Whether to add "from ee_plugin import Map \n" to the output script. Defaults to True.
        github_repo (str, optional): GitHub repo url. Defaults to None.
        import_geemap (bool, optional): Whether to add "import geemap" to the output script. Defaults to False.
        Map (str, optional): The name of the map variable. Defaults to "m".
    """
    print("Converting Earth Engine JavaScripts to Python scripts...\n")
    in_dir = os.path.abspath(in_dir)
    if out_dir is None:
        out_dir = in_dir
    elif not os.path.exists(out_dir):
        out_dir = os.path.abspath(out_dir)
        os.makedirs(out_dir)
    else:
        out_dir = os.path.abspath(out_dir)

    files = list(Path(in_dir).rglob("*.js"))

    for index, in_file in enumerate(files):
        print(f"Processing {index + 1}/{len(files)}: {in_file}")
        # if use_qgis:
        #     out_file = os.path.splitext(in_file)[0] + "_qgis.py"
        # else:
        out_file = os.path.splitext(in_file)[0] + "_geemap.py"
        out_file = out_file.replace(in_dir, out_dir)
        js_to_python(
            in_file,
            out_file,
            use_qgis,
            github_repo,
            import_geemap=import_geemap,
            Map=Map,
        )
    # print("Output Python script folder: {}".format(out_dir))


# def dict_key_str(line):

#     keys = """asFloat bands bestEffort bias collection color connectedness crs eeObject eightConnected format gain gamma
#               geometry groupField groupName image iterations kernel labelBand leftField magnitude max maxDistance
#               maxOffset maxPixels maxSize minBucketWidth min name normalize opacity palette patchWidth
#               radius reducer referenceImage region rightField scale selectors shown sigma size source
#               strokeWidth threshold units visParams width""".split()
#     for key in keys:
#         if ":" in line and key in line:
#             line = line.replace(key + ":", "'" + key + "':")
#     return line


def remove_qgis_import(in_file, Map="m"):
    """Removes 'from ee_plugin import Map' from an Earth Engine Python script.

    Args:
        in_file (str): Input file path of the Python script.
        Map (str, optional): The name of the map variable. Defaults to "m".

    Returns:
        list: List of lines  'from ee_plugin import Map' removed.
    """
    in_file = os.path.abspath(in_file)
    start_index = 0
    with open(in_file, encoding="utf-8") as f:
        lines = f.readlines()
        for index, line in enumerate(lines):
            if "from ee_plugin import Map" in line:
                start_index = index

                i = 1
                while True:
                    line_tmp = lines[start_index + i].strip()
                    if line_tmp != "":
                        return lines[start_index + i :]
                    else:
                        i = i + 1
            elif f"{Map} = geemap.Map()" in line:
                return lines[index + 1 :]


def get_js_examples(out_dir=None):
    """Gets Earth Engine JavaScript examples from the geemap package.

    Args:
        out_dir (str, optional): The folder to copy the JavaScript examples to. Defaults to None.

    Returns:
        str: The folder containing the JavaScript examples.
    """
    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    example_dir = os.path.join(pkg_dir, "data")
    js_dir = os.path.join(example_dir, "javascripts")

    files = list(Path(js_dir).rglob("*.js"))
    if out_dir is None:
        out_dir = js_dir
    else:
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        for file in files:
            basename = os.path.basename(file)
            out_path = os.path.join(out_dir, basename)
            shutil.copyfile(file, out_path)

    return out_dir


def get_nb_template(download_latest=False, out_file=None):
    """Get the Earth Engine Jupyter notebook template.

    Args:
        download_latest (bool, optional): If True, downloads the latest notebook template from GitHub. Defaults to False.
        out_file (str, optional): Set the output file path of the notebook template. Defaults to None.

    Returns:
        str: The file path of the template.
    """
    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    example_dir = os.path.join(pkg_dir, "data")
    template_dir = os.path.join(example_dir, "template")
    template_file = os.path.join(template_dir, "template.py")

    if out_file is None:
        out_file = template_file
        return out_file

    if not out_file.endswith(".py"):
        out_file = out_file + ".py"

    if not os.path.exists(os.path.dirname(out_file)):
        os.makedirs(os.path.dirname(out_file))

    if download_latest:
        template_url = "https://raw.githubusercontent.com/gee-community/geemap/master/examples/template/template.py"
        print(f"Downloading the latest notebook template from {template_url}")
        urllib.request.urlretrieve(template_url, out_file)
    elif out_file is not None:
        shutil.copyfile(template_file, out_file)

    return out_file


def template_header(in_template):
    """Extracts header from the notebook template.

    Args:
        in_template (str): Input notebook template file path.

    Returns:
        list: List of lines.
    """
    header = []
    template_lines = []
    header_end_index = 0

    with open(in_template, encoding="utf-8") as f:
        template_lines = f.readlines()
        for index, line in enumerate(template_lines):
            if "## Add Earth Engine Python script" in line:
                header_end_index = index + 6

    header = template_lines[:header_end_index]

    return header


def template_footer(in_template):
    """Extracts footer from the notebook template.

    Args:
        in_template (str): Input notebook template file path.

    Returns:
        list: List of lines.
    """
    footer = []
    template_lines = []
    footer_start_index = 0

    with open(in_template, encoding="utf-8") as f:
        template_lines = f.readlines()
        for index, line in enumerate(template_lines):
            if "## Display the interactive map" in line:
                footer_start_index = index - 2

    footer = ["\n"] + template_lines[footer_start_index:]

    return footer


def py_to_ipynb(
    in_file,
    template_file=None,
    out_file=None,
    github_username=None,
    github_repo=None,
    Map="m",
):
    """Converts Earth Engine Python script to Jupyter notebook.

    Args:
        in_file (str): Input Earth Engine Python script.
        template_file (str): Input Jupyter notebook template.
        out_file (str, optional)): Output Jupyter notebook.
        github_username (str, optional): GitHub username. Defaults to None.
        github_repo (str, optional): GitHub repo name. Defaults to None.
        Map (str, optional): The name of the map variable. Defaults to "m".
    """
    in_file = os.path.abspath(in_file)

    if template_file is None:
        template_file = get_nb_template()

    if out_file is None:
        out_file = os.path.splitext(in_file)[0] + ".ipynb"

    out_py_file = os.path.splitext(out_file)[0] + "_tmp.py"

    out_dir = os.path.dirname(out_file)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    if out_dir == os.path.dirname(in_file):
        out_py_file = os.path.splitext(out_file)[0] + "_tmp.py"

    content = remove_qgis_import(in_file, Map=Map)
    if content[-1].strip() == "Map":
        content = content[:-1]
    header = template_header(template_file)
    footer = template_footer(template_file)

    if (github_username is not None) and (github_repo is not None):
        out_py_path = str(out_file).split("/")
        index = out_py_path.index(github_repo)
        out_py_relative_path = "/".join(out_py_path[index + 1 :])
        out_ipynb_relative_path = out_py_relative_path.replace(".py", ".ipynb")

        new_header = []
        for index, line in enumerate(header):
            if index < 9:  # Change Google Colab and binder URLs
                line = line.replace("giswqs", github_username)
                line = line.replace("geemap", github_repo)
                line = line.replace(
                    "examples/template/template.ipynb", out_ipynb_relative_path
                )
            new_header.append(line)
        header = new_header

    if content is not None:
        out_text = header + content + footer
    else:
        out_text = header + footer

    out_text = out_text[:-1] + [out_text[-1].strip()]

    if not os.path.exists(os.path.dirname(out_py_file)):
        os.makedirs(os.path.dirname(out_py_file))

    with open(out_py_file, "w", encoding="utf-8") as f:
        f.writelines(out_text)

    try:
        # command = 'ipynb-py-convert ' + out_py_file + ' ' + out_file
        command = 'ipynb-py-convert "{}" "{}"'.format(out_py_file, out_file)
        print(os.popen(command).read().rstrip())
        # os.popen(command)
    except Exception as e:
        print("Please install ipynb-py-convert using the following command:\n")
        print("pip install ipynb-py-convert")
        raise Exception(e)

    try:
        os.remove(out_py_file)
    except Exception as e:
        print(e)


def py_to_ipynb_dir(
    in_dir,
    template_file=None,
    out_dir=None,
    github_username=None,
    github_repo=None,
    Map="m",
):
    """Converts Earth Engine Python scripts in a folder recursively to Jupyter notebooks.

    Args:
        in_dir (str): Input folder containing Earth Engine Python scripts.
        out_dir str, optional): Output folder. Defaults to None.
        template_file (str): Input jupyter notebook template file.
        github_username (str, optional): GitHub username. Defaults to None.
        github_repo (str, optional): GitHub repo name. Defaults to None.
        Map (str, optional): The name of the map variable. Defaults to "m".
    """
    print("Converting Earth Engine Python scripts to Jupyter notebooks ...\n")

    in_dir = os.path.abspath(in_dir)
    files = []
    qgis_files = list(Path(in_dir).rglob("*_geemap.py"))
    py_files = list(Path(in_dir).rglob("*.py"))

    files = qgis_files

    # if len(qgis_files) == len(py_files) / 2:
    #     files = qgis_files
    # else:
    #     files = py_files

    if out_dir is None:
        out_dir = in_dir
    elif not os.path.exists(out_dir):
        out_dir = os.path.abspath(out_dir)
        os.makedirs(out_dir)
    else:
        out_dir = os.path.abspath(out_dir)

    for index, file in enumerate(files):
        in_file = str(file)
        out_file = (
            in_file.replace(in_dir, out_dir)
            .replace("_qgis", "")
            .replace(".py", ".ipynb")
        )
        print(f"Processing {index + 1}/{len(files)}: {in_file}")
        py_to_ipynb(in_file, template_file, out_file, github_username, github_repo, Map)


def execute_notebook(in_file):
    """Executes a Jupyter notebook and save output cells

    Args:
        in_file (str): Input Jupyter notebook.
    """
    # command = 'jupyter nbconvert --to notebook --execute ' + in_file + ' --inplace'
    command = 'jupyter nbconvert --to notebook --execute "{}" --inplace'.format(in_file)
    print(os.popen(command).read().rstrip())
    # os.popen(command)


def execute_notebook_dir(in_dir):
    """Executes all Jupyter notebooks in the given directory recursively and save output cells.

    Args:
        in_dir (str): Input folder containing notebooks.
    """
    print("Executing Earth Engine Jupyter notebooks ...\n")

    in_dir = os.path.abspath(in_dir)
    files = list(Path(in_dir).rglob("*.ipynb"))
    count = len(files)
    if files is not None:
        for index, file in enumerate(files):
            in_file = str(file)
            print(f"Processing {index + 1}/{count}: {file} ...")
            execute_notebook(in_file)


def update_nb_header(in_file, github_username=None, github_repo=None):
    """Updates notebook header (binder and Google Colab URLs).

    Args:
        in_file (str): The input Jupyter notebook.
        github_username (str, optional): GitHub username. Defaults to None.
        github_repo (str, optional): GitHub repo name. Defaults to None.
    """
    if github_username is None:
        github_username = "giswqs"
    if github_repo is None:
        github_repo = "geemap"

    index = in_file.index(github_repo)
    file_relative_path = in_file[index + len(github_repo) + 1 :]

    output_lines = []

    with open(in_file, encoding="utf-8") as f:
        lines = f.readlines()
        start_line_index = 2
        start_char_index = lines[start_line_index].index("{")
        matching_line_index, _ = find_matching_bracket(
            lines, start_line_index, start_char_index
        )

        header = lines[:matching_line_index]
        content = lines[matching_line_index:]

        new_header = []
        search_string = ""
        for line in header:
            line = line.replace("giswqs", github_username)
            line = line.replace("geemap", github_repo)
            if "master?filepath=" in line:
                search_string = "master?filepath="
                start_index = line.index(search_string) + len(search_string)
                end_index = line.index(".ipynb") + 6
                relative_path = line[start_index:end_index]
                line = line.replace(relative_path, file_relative_path)
            elif "/master/" in line:
                search_string = "/master/"
                start_index = line.index(search_string) + len(search_string)
                end_index = line.index(".ipynb") + 6
                relative_path = line[start_index:end_index]
                line = line.replace(relative_path, file_relative_path)
            new_header.append(line)

        output_lines = new_header + content

        with open(in_file, "w") as f:
            f.writelines(output_lines)


def update_nb_header_dir(in_dir, github_username=None, github_repo=None):
    """Updates header (binder and Google Colab URLs) of all notebooks in a folder .

    Args:
        in_dir (str): The input directory containing Jupyter notebooks.
        github_username (str, optional): GitHub username. Defaults to None.
        github_repo (str, optional): GitHub repo name. Defaults to None.
    """
    files = list(Path(in_dir).rglob("*.ipynb"))
    for index, file in enumerate(files):
        file = str(file)
        if ".ipynb_checkpoints" in file:
            del files[index]
    count = len(files)
    if files is not None:
        for index, file in enumerate(files):
            in_file = str(file)
            print(f"Processing {index + 1}/{count}: {file} ...")
            update_nb_header(in_file, github_username, github_repo)


# def download_from_url(url, out_file_name=None, out_dir='.', unzip=True):
#     """Download a file from a URL (e.g., https://github.com/giswqs/whitebox/raw/master/examples/testdata.zip)

#     Args:
#         url (str): The HTTP URL to download.
#         out_file_name (str, optional): The output file name to use. Defaults to None.
#         out_dir (str, optional): The output directory to use. Defaults to '.'.
#         unzip (bool, optional): Whether to unzip the downloaded file if it is a zip file. Defaults to True.
#     """
#     in_file_name = os.path.basename(url)

#     if out_file_name is None:
#         out_file_name = in_file_name
#     out_file_path = os.path.join(os.path.abspath(out_dir), out_file_name)

#     print('Downloading {} ...'.format(url))

#     try:
#         urllib.request.urlretrieve(url, out_file_path)
#     except:
#         print("The URL is invalid. Please double check the URL.")
#         return

#     final_path = out_file_path

#     if unzip:
#         # if it is a zip file
#         if '.zip' in out_file_name:
#             print("Unzipping {} ...".format(out_file_name))
#             with zipfile.ZipFile(out_file_path, "r") as zip_ref:
#                 zip_ref.extractall(out_dir)
#             final_path = os.path.join(os.path.abspath(
#                 out_dir), out_file_name.replace('.zip', ''))

#         # if it is a tar file
#         if '.tar' in out_file_name:
#             print("Unzipping {} ...".format(out_file_name))
#             with tarfile.open(out_file_path, "r") as tar_ref:
#                 tar_ref.extractall(out_dir)
#             final_path = os.path.join(os.path.abspath(
#                 out_dir), out_file_name.replace('.tart', ''))

#     print('Data downloaded to: {}'.format(final_path))


def download_gee_app(url, out_file=None):
    """Downloads JavaScript source code from a GEE App

    Args:
        url (str): The URL of the GEE App.
        out_file (str, optional): The output file path for the downloaded JavaScript. Defaults to None.
    """
    cwd = os.getcwd()
    out_file_name = os.path.basename(url) + ".js"
    out_file_path = os.path.join(cwd, out_file_name)
    items = url.split("/")
    items[3] = "javascript"
    items[4] = items[4] + "-modules.json"
    json_url = "/".join(items)
    print(f"The json url: {json_url}")

    if out_file is not None:
        out_file_path = out_file
        if not out_file_path.endswith("js"):
            out_file_path += ".js"

    out_dir = os.path.dirname(out_file_path)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    json_path = out_file_path + "on"

    try:
        urllib.request.urlretrieve(json_url, json_path)
    except Exception:
        raise Exception("The URL is invalid. Please double check the URL.")

    with open(out_file_path, "w") as f1:
        with open(json_path, encoding="utf-8") as f2:
            lines = f2.readlines()
            for line in lines:
                # print(line)
                items = line.split("\\n")
                for index, item in enumerate(items):
                    if (index > 0) and (index < (len(items) - 1)):
                        item = item.replace('\\"', '"')
                        item = item.replace(r"\\", "\n")
                        item = item.replace("\\r", "")
                        f1.write(item + "\n")
    os.remove(json_path)
    print(f"The JavaScript is saved at: {out_file_path}")


# # Download file shared via Google Drive
# def download_from_gdrive(gfile_url, file_name, out_dir='.', unzip=True):
#     """Download a file shared via Google Drive
#        (e.g., https://drive.google.com/file/d/18SUo_HcDGltuWYZs1s7PpOmOq_FvFn04/view?usp=sharing)

#     Args:
#         gfile_url (str): The Google Drive shared file URL
#         file_name (str): The output file name to use.
#         out_dir (str, optional): The output directory. Defaults to '.'.
#         unzip (bool, optional): Whether to unzip the output file if it is a zip file. Defaults to True.
#     """
#     try:
#         from google_drive_downloader import GoogleDriveDownloader as gdd
#     except ImportError:
#         print('GoogleDriveDownloader package not installed. Installing ...')
#         subprocess.check_call(
#             ["python", '-m', 'pip', 'install', 'googledrivedownloader'])
#         from google_drive_downloader import GoogleDriveDownloader as gdd

#     file_id = gfile_url.split('/')[5]
#     print('Google Drive file id: {}'.format(file_id))

#     dest_path = os.path.join(out_dir, file_name)
#     gdd.download_file_from_google_drive(file_id, dest_path, True, unzip)


if __name__ == "__main__":
    # Create a temporary working directory
    work_dir = os.path.join(os.path.expanduser("~"), "geemap")
    # Get Earth Engine JavaScript examples. There are five examples in the geemap package data folder.
    # Change js_dir to your own folder containing your Earth Engine JavaScripts, such as js_dir = '/path/to/your/js/folder'
    js_dir = get_js_examples(out_dir=work_dir)

    # Convert all Earth Engine JavaScripts in a folder recursively to Python scripts.
    js_to_python_dir(in_dir=js_dir, out_dir=js_dir, use_qgis=True)
    print(f"Python scripts saved at: {js_dir}")

    # Convert all Earth Engine Python scripts in a folder recursively to Jupyter notebooks.
    # Get the notebook template from the package folder.
    nb_template = get_nb_template()
    py_to_ipynb_dir(js_dir, nb_template)

    # Execute all Jupyter notebooks in a folder recursively and save the output cells.
    execute_notebook_dir(in_dir=js_dir)

    # # # Download a file from a URL.
    # # url = 'https://github.com/giswqs/whitebox/raw/master/examples/testdata.zip'
    # # download_from_url(url)

    # # # Download a file shared via Google Drive.
    # # g_url = 'https://drive.google.com/file/d/18SUo_HcDGltuWYZs1s7PpOmOq_FvFn04/view?usp=sharing'
    # # download_from_gdrive(g_url, 'testdata.zip')

    # # # parser = argparse.ArgumentParser()
    # # # parser.add_argument('--input', type=str,
    # # #                     help="Path to the input JavaScript file")
    # # # parser.add_argument('--output', type=str,
    # # #                     help="Path to the output Python file")
    # # # args = parser.parse_args()
    # # # js_to_python(args.input, args.output)
