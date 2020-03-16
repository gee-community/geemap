import os
import pkg_resources
from geemap.conversion import *

# The following four lines of code retrieve the file path of 'template.py', which is needed 
# to convert Earth Engine Python scripts to Jupyter notebooks. Do not modify these lines.
example_dir = pkg_resources.resource_filename("geemap", "examples")
print(example_dir)
template_dir = os.path.join(example_dir, 'Template')
template_file = os.path.join(template_dir, 'template.py')

# Convert an Earth Engine JavaScript to Python script. 
# Change in_file_path and out_file_path to your own paths.
js_dir = os.path.join(example_dir, 'JavaScripts')
in_file_path = os.path.join(js_dir, "NormalizedDifference.js")  
out_file_path = os.path.splitext(in_file_path)[0] + ".py"
js_to_python(in_file_path, out_file_path)
print("Python script saved at: {}".format(out_file_path))

# Convert all Earth Engine JavaScripts in a folder recursively to Python scripts.
# Change in_dir and out_dir to your own paths.
js_to_python_dir(in_dir=js_dir, out_dir=js_dir, use_qgis=True)
print("Python scripts saved at: {}".format(js_dir))

# Convert an Earth Engine Python script to Jupyter notebook.
# Change in_file and out_file to your own paths.
in_file = os.path.join(js_dir, 'NormalizedDifference.py')
out_file = in_file.replace('.py', '.ipynb')
py_to_ipynb(in_file, template_file, out_file, 'giswqs', 'geemap')

# Convert all Earth Engine Python scripts in a folder recursively to Jupyter notebooks.
# Change in_dir to your own path.
in_dir = js_dir
py_to_ipynb_dir(in_dir, template_file, github_username='giswqs', github_repo='geemap')

# Execute all Jupyter notebooks in a folder recursively and save the output cells.
# Change in_dir to your own path.
execute_notebook_dir(in_dir)