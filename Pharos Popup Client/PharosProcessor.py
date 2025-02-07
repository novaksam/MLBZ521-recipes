#!/usr/bin/env python
#
# Copyright 2022 Zack Thompson (mlbz521)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import os
import sys

from autopkglib import Processor, ProcessorError

if not os.path.exists("/Library/AutoPkg/Selenium"):
    raise ProcessorError("Selenium is required for this recipe!  "
        "Please review my Shared Processors README.")

sys.path.insert(0, "/Library/AutoPkg/Selenium")

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support.expected_conditions import presence_of_element_located


__all__ = ["PharosProcessor"]


class PharosProcessor(Processor):

    """This processor finds the download URL for Ricoh print driver.
    """

    input_variables = {
        "downloads_page": {
            "required": False,
            "description": (
                "The downloads page to search on."
                "Default:  https://community.pharos.com/s/article/Macintosh-Updates-For-Uniprint"
            )
        },
        "prefix_dl_url": {
            "required": False,
            "description": (
                "The prefix of the downloads url to match."
                "Default:  https://pharos.com/support/downloads/mac/Mac OS X Popup"
            )
        },
        "web_driver": {
            "required": False,
            "description": (
                "The web driver engine to use.",
                "Default:  Chrome"
            )
        },
        "web_driver_path": {
            "required": False,
            "description": (
                "The OS version to search against.",
                "Default:  $PATH"
            )
        }
    }
    output_variables = {
        "url": {
            "description": "Returns the url to download."
        }
    }

    description = __doc__


    class WebDriver():
        """A Class that creates a Context Manager to interact with a WebDriver Engine"""

        def __init__(self, engine, path=None):
            self.engine = engine
            self.path = path


        def __enter__(self):
            """Opens a connection to the database"""

            try:

                if self.engine == "Chrome":

                    options = webdriver.ChromeOptions()
                    options.add_argument("headless")

                    if self.path:
                        self.web_engine = webdriver.Chrome(
                            executable_path=self.path, options=options
                        )

                    else:
                        self.web_engine = webdriver.Chrome(options=options)

            except:
                raise ProcessorError("Failed to load the specified WebDriver engine.")

            return self.web_engine


        def __exit__(self, exc_type, exc_value, exc_traceback):
            self.web_engine.close


    def main(self):
        """Do the main thing."""

        # Define variables
        downloads_page = self.env.get('downloads_page', 
            "https://community.pharos.com/s/article/Macintosh-Updates-For-Uniprint")
        prefix_dl_url = self.env.get('prefix_dl_url', 
            "https://pharos.com/support/downloads/mac/Mac OS X Popup")
        prefix_dl_url = re.sub(r"\s", "%20", prefix_dl_url)
        web_driver = self.env.get("web_driver", "Chrome")
        web_driver_path = self.env.get("web_driver_path")

        self.output("Using Web Driver:  {}".format(web_driver), verbose_level=1)
        self.output("downloads_page:  {}".format(downloads_page), verbose_level=1)

        if web_driver_path:
            self.output("Path to Web Driver Engine:  {}".format(web_driver_path), verbose_level=2)
        else:
            self.output("The Web Driver Engine is assumed to be in the $PATH.", verbose_level=2)

        with self.WebDriver(web_driver, web_driver_path) as web_engine:

            try:
                web_engine.get(downloads_page)
            except:
                raise ProcessorError("Failed to access the download page.")

            try:
                WebDriverWait(web_engine, timeout=10).until(
                    lambda d: d.find_elements_by_link_text("Download")
                )
                download_links = web_engine.find_elements_by_link_text("Download")
            except:
                raise ProcessorError("Failed to find and open the operating "
                    "system section labled \"Mac OS X\".")

            try:
                for link in download_links:
                    if re.match(prefix_dl_url, link.get_attribute("href")):
                        download_url = link.get_attribute("href")
                        version = re.match(r".+(\d+\.\d+\.\d+).+", download_url).group(1)

            except:
                raise ProcessorError(
                    "Failed to find and collect the download url from the download link.")


        if not download_url:
            raise ProcessorError("Failed to find a matching download type for the provided model.")

        if not version:
            raise ProcessorError("Failed to identify the version of the download.")

        self.env["url"] = download_url
        self.output("Download URL: {}".format(self.env["url"]), verbose_level=1)
        self.env["version"] = version
        self.output("Version: {}".format(self.env["version"]), verbose_level=1)


if __name__ == "__main__":
    processor = PharosProcessor()
    processor.execute_shell()
