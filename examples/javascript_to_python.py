from geemap.conversion import *


## Convert an Earth Engine JavaScript to Python script.
work_dir = os.path.dirname(os.path.abspath(__file__))
js_dir = os.path.join(work_dir, 'JavaScripts')
template_dir = os.path.join(work_dir, 'Template')
in_file_path = os.path.join(js_dir, "NormalizedDifference.js")  # change this path to your JavaScript file
out_file_path = os.path.splitext(in_file_path)[0] + ".py"
js_to_python(in_file_path, out_file_path)
print("Python script saved at: {}".format(out_file_path))

# Convert all Earth Engine JavaScripts in a folder recursively to Python scripts.
js_to_python_dir(in_dir=js_dir, out_dir=js_dir, use_qgis=True)
print("Python scripts saved at: {}".format(js_dir))

# Convert an Earth Engine Python script to Jupyter notebook.
in_template =os.path.join(template_dir, 'template.py')
in_file = os.path.join(js_dir, 'NormalizedDifference.py')
out_file = in_file.replace('.py', '.ipynb')
py_to_ipynb(in_file, in_template, out_file, 'giswqs', 'geemap')

# Convert all Earth Engine Python scripts in a folder recursively to Jupyter notebooks.
in_dir = js_dir
py_to_ipynb_dir(in_dir, in_template, github_username='giswqs', github_repo='geemap')

# Execute all Jupyter notebooks in a folder recursively and save the output cells.
execute_notebook_dir(in_dir)