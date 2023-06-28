#!/usr/bin/env python

"""The setup script."""
import platform
from os import path as op
import io
from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

here = op.abspath(op.dirname(__file__))

# get the dependencies and installs
with io.open(op.join(here, "requirements.txt"), encoding="utf-8") as f:
    core_reqs = f.read().split("\n")
    if platform.system() == "Windows":
        core_reqs.append("pywin32")

with io.open(op.join(here, "requirements_extra.txt"), encoding="utf-8") as f:
    extra_reqs = [x.strip() for x in f.read().split("\n")]

with io.open(op.join(here, "requirements_all.txt"), encoding="utf-8") as f:
    all_reqs = [x.strip() for x in f.read().split("\n")]

install_requires = [x.strip() for x in core_reqs if "git+" not in x]
dependency_links = [x.strip().replace("git+", "") for x in core_reqs if "git+" not in x]

extras_requires = {
    "extra": extra_reqs,
    "all": all_reqs,
    "backends": ["keplergl", "pydeck", "plotly"],
    "lidar": [
        "ipygany",
        "ipyvtklink",
        "laspy[lazrs]",
        "panel",
        "pyntcloud[LAS]",
        "pyvista",
        "pyvista-xarray",
        "rioxarray",
    ],
    "raster": [
        "geedim",
        "localtileserver",
        "rio-cogeo",
        "rioxarray",
        "netcdf4",
        "pyvista-xarray",
    ],
    "sql": ["psycopg2", "sqlalchemy"],
    "apps": ["gradio", "streamlit-folium", "voila"],
    "vector": ["geopandas", "osmnx"],
}

setup_requirements = []

test_requirements = []

setup(
    author="Qiusheng Wu",
    author_email="giswqs@gmail.com",
    python_requires=">=3.8",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    description="A Python package for interactive mapping using Google Earth Engine and ipyleaflet",
    entry_points={
        "console_scripts": [
            "geemap=geemap.cli:main",
        ],
    },
    install_requires=install_requires,
    extras_require=extras_requires,
    dependency_links=dependency_links,
    license="MIT license",
    long_description=readme,
    include_package_data=True,
    keywords="geemap",
    name="geemap",
    packages=find_packages(include=["geemap", "geemap.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/gee-community/geemap",
    version="0.23.1",
    zip_safe=False,
)
