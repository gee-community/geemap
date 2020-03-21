import os
import glob
import datetime
from pathlib import Path

def update_url(in_file, relative_path, out_path):
    out_lines = []
    with open(in_file) as f:
        lines = f.readlines()
        for line in lines:
            line = line.replace("earthengine-py-notebooks", "earthengine-py-documentation")
            line = line.replace("Template/template.ipynb", relative_path)
            out_lines.append(line)
    
    with open(out_path, 'w') as f:
        f.writelines(out_lines)




root_dir = os.path.dirname(os.path.dirname(__file__))
# print(root_dir)

all_files = list(Path(root_dir).rglob('*.ipynb'))

files = []
for file in all_files:
    if "checkpoints" not in str(file):
        files.append(file)

files.sort()
# for file in files:
#     print(file)


i = 1
for index, filename in enumerate(files):

    if index < len(files):
        out_py_path = str(filename).split('/')
        index = out_py_path.index('earthengine-py-documentation')
        relative_path = '/'.join(out_py_path[index+1:])
        out_nb_path = os.path.join(root_dir, relative_path)
        # out_nb_path = out_nb_path.replace(".ipynb", "_bk.ipynb")
        update_url(filename, relative_path, out_nb_path)


