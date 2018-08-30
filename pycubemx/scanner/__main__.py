import logging
import json
import argparse
from pathlib import Path
import sys
from .scanner import Scanner
from time import gmtime, strftime

FORMAT = '[%(name)-15s - %(levelname)-6s] %(message)s'
logging.basicConfig(format=FORMAT,level=logging.DEBUG)
Log = logging.getLogger('cubemx-scanner')

parser = argparse.ArgumentParser(description='Command discovery tool.')

parser.add_argument('output',
                    help='Command database output file.')

parser.add_argument('sourcepath', nargs='*',
                    help='Paths to cubemx source code')

args = parser.parse_args()
scanner = Scanner()
for i in args.sourcepath:
    scanner.addPath(i)
scanner.start()

Log.info("[Commands Discovered]")
for i in scanner.commands:
    Log.info("    " + str(i))

Log.info("Count: {}".format(len(scanner.commands)))

config = scanner.createConfig()
config._config['command_db_version'] = {
    "version"       : "0.0",
    "details"       : "Automatic scan performed on " + strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()),
    "author"        : "pycubemx.scanner"
}
config.saveFile(args.output)
