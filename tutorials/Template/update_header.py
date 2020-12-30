import os
from geemap.conversion import *

work_dir = os.path.dirname(os.path.dirname(__file__))
update_nb_header_dir(work_dir, github_username="giswqs", github_repo="geemap")
