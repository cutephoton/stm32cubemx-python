import logging
from .server import runServer
from .client import MxRemoteClient
from ..config import Config
import argparse
import sys
from pathlib import Path

def FixArgs():
    for idx,v in enumerate(sys.argv):
        if v.startswith('_DOT_ASTR_'):
            sys.argv[idx] = ".*"
FixArgs()

FORMAT = '[%(name)-15s - %(levelname)-6s] %(message)s'
logging.basicConfig(format=FORMAT,level=logging.DEBUG)
Log = logging.getLogger('cubemx')

parser = argparse.ArgumentParser(description='Automate stm32cubemx by command line.\n Note - For .* expressions, use helper constant _DOT_ASTR_ to avoid globbing files.')
parser.add_argument("--uri", help="URI to server.", default="http://localhost:8080")
parser.add_argument('--config', required=False,
                                help='Overrides the local configuration file.\nDefault:' + Config.LocalConfigFile)
parser.add_argument('--config-no-defaults', action='store_true',
                                help='Don\'t load the default command set/settings.')
subparsers = parser.add_subparsers(help='Command', dest="command")
subparsers.required = True
op_server = subparsers.add_parser("start-server",
                                help="Starts CubeMX server.")
op_mxusage = subparsers.add_parser("mx-usage",
                                help="Returns a listing of supported commands.")
op_mxhelp = subparsers.add_parser("mx-help",
                                help="Returns a listing of supported commands.")

op_generate = subparsers.add_parser("generate",
                                help="Generate the minimal code generation files without copying middleware/firmware/etc.")
op_generate.add_argument('outdir',
                    help='The output directory.')
op_generate.add_argument('--load-project',
        help='The input configuration (ioc file) for CubeMX.')
op_generate.add_argument('--single', action='store_true',
                    help='Use a single file to store IP settings. As opposed to multiple files.')
op_rawapi = subparsers.add_parser("mx-direct",
                                help="Directly call an API.")
op_rawapi.add_argument('mxapi',
                    help='API to use.')
op_rawapi.add_argument('mxargs', nargs='*',
                    help='Arguments to pass to API.')

subparsers.add_parser("mx-disconnect",
                                help="Shutdown CUBEMX.")
subparsers.add_parser("stop-server",
                                help="Shutdown server.")

op_load = subparsers.add_parser("load",
                                help="Load configuration file (*.ioc).")
op_load.add_argument('project',
                    help='The input configuration (ioc file) for CubeMX.')
args = parser.parse_args()

config = Config.LocalConfig (configFile = args.config, nodefaults = args.config_no_defaults)

if args.command == "start-server":
    runServer(config)
    Log.info("Server Stopped")
else:
    try:
        cmd = args.command
        client = MxRemoteClient(config)
        client.init()
        if cmd == "mx-usage":
            usage = client.usage ()
            #sys.stdout.write("mx-usage> ")
            sys.stdout.write(usage)
            sys.stdout.write("\n")
        elif cmd == "mx-help":
            x = client.help()
            for i in x:
                sys.stdout.write("mx-help> ")
                sys.stdout.write(i)
                sys.stdout.write("\n")
        elif cmd == "mx-disconnect":
            x = client.disconnect()
            Log.info("STM32CubeMX: Stopped")
        elif cmd == "stop-server":
            x = client.shutdown()
            Log.info("Stop-Server: Success")
        elif cmd == "mx-direct":
            x = client.directAPI(args.mxapi, *args.mxargs)
            for i in x:
                sys.stdout.write(i)
                sys.stdout.write("\n")
        elif cmd == "generate":
            output = str(Path(args.outdir).resolve())
            if args.load_project is not None:
                input = str(Path(args.project).resolve())
                client.config.load(input)
            if args.single:
                client.generate.all_code_in_main()
            else:
                client.generate.one_file_per_ip()
            client.generate.code(output)
        elif cmd == "load":
            input = str(Path(args.project).resolve())
            client.config.load(input)
        else:
            Log.error("Unknown command: " + cmd)
    except:
        Log.exception ("Failed to execute application.")
        sys.exit(-1)
