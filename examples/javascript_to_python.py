import os
from geemap.conversion import *

# Create a temporary working directory
work_dir = os.path.join(os.path.expanduser('~'), 'geemap')
# Get Earth Engine JavaScript examples. There are five examples in the geemap package folder. 
# Change js_dir to your own folder containing your Earth Engine JavaScripts, such as js_dir = '/path/to/your/js/folder'
js_dir = get_js_examples(out_dir=work_dir) 

# Convert all Earth Engine JavaScripts in a folder recursively to Python scripts.
js_to_python_dir(in_dir=js_dir, out_dir=js_dir, use_qgis=True)
print("Python scripts saved at: {}".format(js_dir))

# Convert all Earth Engine Python scripts in a folder recursively to Jupyter notebooks.
nb_template = get_nb_template()  # Get the notebook template from the package folder.
py_to_ipynb_dir(js_dir, nb_template)

# Execute all Jupyter notebooks in a folder recursively and save the output cells.
execute_notebook_dir(in_dir=js_dir)