"""Module for reporting issues with geemap."""

# *******************************************************************************#
# This module contains extra features of the geemap package.                     #
# The geemap community will maintain the extra features.                         #
# *******************************************************************************#

import scooby
from typing import Optional


class Report(scooby.Report):
    def __init__(
        self,
        additional: Optional[dict] = None,
        ncol: int = 3,
        text_width: int = 80,
        sort: bool = False,
    ):
        """Initiate a scooby.Report instance."""
        core = [
            "geemap",
            "ee",
            "ipyleaflet",
            "folium",
            "jupyterlab",
            "notebook",
            "ipyevents",
        ]
        optional = ["geopandas", "localtileserver"]

        scooby.Report.__init__(
            self,
            additional=additional,
            core=core,
            optional=optional,
            ncol=ncol,
            text_width=text_width,
            sort=sort,
        )
