import logging
import json
from .config import Config
from .native import MxConnection
import argparse
from pathlib import Path
import sys

FORMAT = '[%(name)-15s - %(levelname)-6s] %(message)s'
logging.basicConfig(format=FORMAT,level=logging.DEBUG)
Log = logging.getLogger('cubemx')

parser = argparse.ArgumentParser(description='Automate stm32cubemx by command line.')
subparsers = parser.add_subparsers(help='Command', dest="command")
# Top Level Arguments
parser.add_argument('--config', required=False,
                    help='Overrides the local configuration file.\nDefault:' + Config.LocalConfigFile)
parser.add_argument('--config-no-defaults', action='store_true',
                    help='Don\'t load the default command set/settings.')
# Dump Command
op_dump = subparsers.add_parser("dump",
                                help="Dump the command set.")
# Dump Command
op_help = subparsers.add_parser("show-help",
                                help="Show help info from CubeMX.")

# Generate Function
op_generate = subparsers.add_parser("generate",
                                help="Generate the minimal code generation files without copying middleware/firmware/etc.")
op_generate.add_argument('project',
                    help='The input configuration (ioc file) for CubeMX.')
op_generate.add_argument('outdir',
                    help='The output directory.')
op_generate.add_argument('--single', action='store_true',
                    help='Use a single file to store IP settings. As opposed to multiple files.')
args = parser.parse_args()

# Start Work!
if args.command is None:
    Log.error("Must specify a command!")
    sys.exit(-1)

config = Config.LocalConfig (configFile = args.config, nodefaults = args.config_no_defaults)
Log.info("Command DB Version: " + str(config.commandDbVersionInfo))

# Don't need to connect to the application to evaluate...
if args.command == 'dump':
    session = MxConnection(config)
    session.dump(includeHelp=True)
    sys.exit(0)

with MxConnection(config) as session:
    if args.command == "generate":
        input = str(Path(args.project).resolve())
        output = str(Path(args.outdir).resolve())
        try:
            session.config.load(input)
            session.generate.one_file_per_ip()
            session.generate.code(output)
        except:
            Log.exception ("Failed to complete code generation successfully...")
    elif args.command == "show-help":
        for i in session.help():
            Log.info(">>> " + i)
