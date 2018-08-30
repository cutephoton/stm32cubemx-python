import sys
from .native import *
from .config import *

__ALL__ = ("MxConnection", "MxException", "MxCommandError", "MxStatus", 'Config','ConfigException')

if (sys.version_info < (3, 5)):
    print ("Requires python 3.5 or later.")
    sys.exit(-1)
