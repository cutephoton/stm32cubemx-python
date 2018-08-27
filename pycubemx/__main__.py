import logging
import json
from .config import Config, GetBaseConfig
from .native import MxConnection

FORMAT = '[%(name)-15s - %(levelname)-6s] %(message)s'
logging.basicConfig(format=FORMAT,level=logging.DEBUG)
Log = logging.getLogger('cubemx')
Log.info ("stm32cubemx python adapter")
c = GetBaseConfig ()
c.loadFile("cubemx-paths-local.json")
Log.info("Command DB Version: " + str(c.commandDbVersionInfo))
with MxConnection(c) as x:
    help = x.help()
    for i in help:
        Log.info("--> " + i)

    """
    x._detect(recursive=True)
    x.dump(includeHelp=True)
    c._apiSchema = x._serialize()
    c.saveFile("PP_config.json")
    """

#x = MxConnection(c)
#x.dump(includeHelp = True)
