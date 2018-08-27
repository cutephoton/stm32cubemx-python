#!/usr/bin/env python3
import logging
from pycubemx import MxConnection, Config, GetBaseConfig
import os

EXAMPLE_PROJECT = os.path.abspath(os.path.join(os.path.dirname(__file__), "example-data", "cubeboot.ioc"))
EXAMPLE_PROJECT_TMP_OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "example-data-output"))

FORMAT = '[%(name)-15s - %(levelname)-6s] %(message)s'
logging.basicConfig(format=FORMAT,level=logging.DEBUG)
Log = logging.getLogger('cubemx')

c = GetBaseConfig ()
c.loadFile("cubemx-paths-local.json")
Log.info("Command DB Version: " + str(c.commandDbVersionInfo))
with MxConnection(c) as x:
    Log.info ("** Showing Command Db **")
    x.dump(includeHelp = True)

    Log.info ("** Loading Project **")
    # Always use absolute paths
    load = x.config.load(EXAMPLE_PROJECT)
    for i in load:
        Log.info("--> " + i)
    x.generate.one_file_per_ip()
    x.generate.code(EXAMPLE_PROJECT_TMP_OUT)
