"""The example shows you how to convert all Earth Engine Python scripts in a GitHub repo to Jupyter notebooks.
"""

import os
from geemap.conversion import *

import subprocess

try:
    from git import Repo
except ImportError:
    print('gitpython package is not installed. Installing ...')
    subprocess.check_call(["python", '-m', 'pip', 'install', 'gitpython'])
    from git import Repo


git_url = 'https://github.com/giswqs/qgis-earthengine-examples'
out_repo_name = 'earthengine-py-notebooks'

# Create a temporary working directory
work_dir = os.path.join(os.path.expanduser('~'), 'geemap')
if not os.path.exists(work_dir):
    os.makedirs(work_dir)

out_dir = os.path.join(work_dir, out_repo_name)

repo_name = git_url.split('/')[-1]
repo_dir = os.path.join(work_dir, repo_name)

if not os.path.exists(repo_dir):
    Repo.clone_from(git_url, repo_dir)

# # Convert all Earth Engine Python scripts in a folder recursively to Jupyter notebooks.
nb_template = get_nb_template()  # Get the notebook template from the package folder.
py_to_ipynb_dir(repo_dir, nb_template, out_dir, github_username='giswqs', github_repo=out_repo_name)

# execute_notebook_dir(out_dir)

