
import sys
import os
import subprocess
import re
from pathlib import Path
from subprocess import Popen, PIPE, TimeoutExpired
import logging
import time
from enum import Enum

Log = logging.getLogger(__name__)
LogCubeLogs = logging.getLogger("native.log")
LogCubeResp = logging.getLogger("native.response")
LogCubeExec = logging.getLogger("native.exec")

__ALL__ = ("MxConnection", "MxException", "MxCommandError", "MxStatus")

class MxException(Exception): pass
class MxNsPathException(MxException): pass
class MxCommandError(MxException):
    def __init__ (self, statusCode, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mxstatus = statusCode
    def __str__ (self):
        return "{}\nMxStatus {}".format(super().__str__(), self.mxstatus.name)

class MxStatus (Enum):
    MxOK                = "OK"
    MxError             = "Error"
    MxTerminated        = "Session Terminated"
    MxCoderError        = "Coder Exception"
    MxUnknown           = "Unknown Error"
    MxUnprocessed       = "Command Incomplete"
    MxBadState          = "Bad State (IPC)"
    MxConnectError      = "Bad State (IPC)"

    def __bool__ (self):
        return (self == MxStatus.MxOK)

class Coder (object):
    _RE_END = re.compile("^.*(\d+)\s+(OK|KO)\s*$")

    def __init__ (self, command):
        self.data       = []
        self.status     = MxStatus.MxUnprocessed
        self.command    = command
        self.result     = None

    def _emit (self, line):
        m = self._RE_END.match(line)
        if m:
            if m.group(2) == "OK":
                self.status = MxStatus.MxOK
            else:
                self.status = MxStatus.MxError
            LogCubeExec.debug("(exitcond) " + self.status.name)
            return True
        else:
            self.data.append(line)
            return False

    @property
    def done(self):
        return self.status != MxStatus.MxUnprocessed

    @property
    def pending(self):
        return self.status == MxStatus.MxUnprocessed

    @property
    def success(self):
        return self.done and self.status != MxStatus.MxOK

    def fail(self, status = MxStatus.MxUnknown):
        self.status = status

    def finish (self):
        self.result = self.processResult ()
        return self.result

    def processResult (self):
        return self.data

    def __str__ (self):
        return "Command<" + self.command + ">"

class DetectCoder (Coder):
    _RE_CMDDECL = re.compile(r'^\s\s([\w\s\d\-_]+\w)\s*(<[^:]+)?(:\s*?(.*))?$')
    _RE_ARGDECL = re.compile(r'<([\s\w\d,|]+)(\s(.*))?>')
    _RE_BASEDECL = re.compile(r'^(\s)?(\w.*)$')

    _ParserPending = 0
    _ParserAmbiguous = 1
    _ParserIsNs = 2
    _ParserIsCmd = 3

    """class Decl (object):
        def __init__ (self, command, args = None, description = None):
            self.command = command
            self.args = args
            self.description = description
            self._top = top"""

    def __init__(self, top, namespace):
        super().__init__(namespace if namespace is not None and len(namespace) > 0 else "help")
        self._commandMap = {}
        self._top = top
        self._namespace = namespace
        self._namespaceObj = top._makeNamespace(namespace)
        self.created = []
        self._parserState = self._ParserPending
        self._parserReset()

    def _parserCreateNamespace (self, ns):
        pass

    def _parserAddCommand (self, ns, command):
        pass

    def _parserReset (self):
        if self._parserState == self._ParserAmbiguous:
            self._parserAddAsNamespace(self._parserBase)

        self._parserBase = None
        self._parserNs = None
        self._parserIsCmdOnly = False
        self._parserState = self._ParserPending

    def _parserPushAmbiguous (self, m):
        self._parserReset()

        # the root namespace has some quirks
        mRootNsWorkaround = (m.group(1) is not None)
        if self._namespace is None:
            if not mRootNsWorkaround:
                return

        self._parserBase = m.group(2).strip()
        self._parserState = self._ParserAmbiguous
        Log.info("BASE: {} ({})".format(self._parserBase, mRootNsWorkaround))

    def _parserPushCmd (self, m):
        self._parserState = self._ParserIsCmd
        m_func = m.group(1)
        m_args = m.group(2)
        m_help = m.group(4)

        if "help" in m_func.lower():
            return

        if self._namespace is None or m_func.startswith(self._namespace):
            Log.info("COMMAND: '{}' - '{}' - '{}'".format(m_func, m_args, m_help) )
            args = []
            if m_args is not None:
                arg_iter = self._RE_ARGDECL.finditer(m_args)
                for j in arg_iter:
                    aname = j.group(1)
                    Log.info("             (arg) '{}' - '{}'".format(j.group(1), j.group(3)))
                    if "|" in aname:
                        args.append(ArgEnum("unnamed", enumValues = aname.split("|"), help=j.group(3)))
                    else:
                        args.append(Arg(j.group(1), help=j.group(3)))
            path = m_func.split(" ")
            callName = path[-1]
            self._add(Caller(callName, *args, help = m_help))
        else:
            Log.info("(bad entry) {}".format(m_func))

    def _parserAddAsNamespace (self, ns):
        if "help" in ns.lower():
            return
        path = ns.split(" ")
        self._add(Namespace(path[-1]))

    def _add (self, obj):
        self._namespaceObj._addChild(obj)
        self.created.append(obj)
        obj.set_top(self._top)
        if isinstance(obj,Namespace):
            Log.debug ("Added Ns: " + str(obj))
        else:
            Log.debug ("Added Call: " + str(obj))

    def processResult (self):
        Log.info ("Processing Result")
        if self.status == MxStatus.MxError or self.status == MxStatus.MxOK:
            if len(self.data)>0:
                if "java.lang.NullPointerException" in self.data[0]:
                    Log.error("Got NPE!")
                    return self.created
            for line in self.data:
                if "help" in line or "Usage" in line:
                    continue

                m_basedecl = self._RE_BASEDECL.match(line)

                if (m_basedecl):
                    #Log.info("BASE: {}".format(line))
                    self._parserPushAmbiguous (m_basedecl)
                else:
                    if not line.startswith("  " + self._parserBase):
                        m_entry = None # Force fallback
                    else:
                        m_entry = self._RE_CMDDECL.match(line)
                    if (not m_entry):
                        Log.info("Unmatched Input: {} part {}".format(line,self._parserBase))
                        if self._parserBase is not None:
                            line = "  " + self._parserBase + ":" + line
                            Log.info("Reformatted: {}".format(line))
                            m_entry = self._RE_CMDDECL.match(line)
                            if not m_entry:
                                Log.error("XXXXXXXXXXXX This should work: " + line)
                        if not m_entry:
                            continue
                    self._parserPushCmd (m_entry)
            self._parserReset()
            self.status = MxStatus.MxOK # since command listing returns KO
        return self.created

class Arg(object):
    ArgType         = "String"
    def __init__ (self, name, help = None):
        self._name = name.replace(" ", "_")
        self._oname = name
        self._help = help
    def validate (self, argument):
        return True
    def __str__ (self):
        return self.ArgType + " " + self._name
    def _serialize (self):
        ser = {
            "type" : self.ArgType,
            "name" : self._name,
            "oname" : self._oname,
            "help" : self._help
        }
        return ser
    @classmethod
    def _deserialize (cls, entry):
        arg = cls(entry['oname'], help=entry["help"])
        return arg
"""
class ArgFile (Arg):
    ArgType         = "Path"
    CondExists      = (1<<0)
    CondNew         = (1<<1)
    CondDir         = (1<<2)
    CondFile        = (1<<3)
    CondRwcLikely   = (1<<4)

    def __init__ (self, *args, condition = 0, **kwargs):
        super().__init__(*args,**kwargs)
        self.condition = condition
    def validate (self, argument):
        p = Path(argument)
        if (self.condition&ArgFile.CondExists) and not p.exists():
            return False
        if (self.condition&ArgFile.CondDir) and not p.is_dir():
            return False
        if (self.condition&ArgFile.CondFile) and p.is_dir():
            return False
        if (self.condition&ArgFile.CondNew) and p.exists():
            return False
        return True
"""
class ArgInt (Arg):
    ArgType         = "Int"
    def validate (self, argument):
        try:
            i = int(argument)
        except:
            return False
        return True

class ArgEnum (Arg):
    ArgType         = "Enum"
    def __init__ (self, *args, enumValues = None, **kwargs):
        super().__init__(*args,**kwargs)
        self.enumValues = enumValues
    def validate (self, argument):
        return True
    def __str__ (self):
        if self.enumValues is None:
            extra = "{<Not Defined>}"
        else:
            extra = "{" + " | ".join(self.enumValues) + "}"
        return super().__str__() + extra
    def _serialize (self):
        ser = super()._serialize()
        ser["options"] = self.enumValues
        return ser
    @classmethod
    def _deserialize (cls, entry):
        return cls(entry['oname'], enumValues=entry["options"], help=entry["help"])


ARGTYPES = {
    ArgEnum.ArgType     : ArgEnum,
    ArgInt.ArgType      : ArgInt,
    Arg.ArgType         : Arg,
}

class Caller (object):
    def __init__ (self, name, *args, coder = Coder, help = None):
        self._parent = None
        self._top = None
        self._path = None
        self._name = name.replace(" ", "_")
        self._oname = name
        self._args = args
        self._help = help
        self._coder = coder
        self._echo = False

    def set_top (self, top):
        self._top = top
        if self._parent is not None:
            self._path = self._parent._path + [self._name]
        else:
            self._path = []

    def encode (self, args):
        if len(args) != len(self._args):
            raise MxException("Mismatched argument count. Got {} expected {}".format(len(args), len(self._args)))
        return Coder(" ".join(list(self._path) + list(args)))

    def __call__ (self, *args):
        coder = self.encode(args)
        self._top._transact(coder)

        try:
            return coder.finish()
        except Exception as e:
            Log.exception("Exception while processing result")
            coder.fail(MxStatus.MxCoderError)
            raise MxCommandError(coder.status, "Command '" + coder.command + "' failed while processing results.")

        if not coder.success:
            raise MxCommandError(coder.status, "Command '" + coder.command + "' failed.")

    def __str__ (self):
        return "(C) " + "::".join(self._path) + "(" + ",".join([str(i) for i in self._args]) + ")"

    def _dump (self, *args, includeHelp = False, **kwargs):
        prefix = "".ljust((len(self._path)*4))
        Log.info(prefix + str(self))
        if (includeHelp):
            if self._help:
                Log.info(prefix + "  " + self._help)
            for i in self._args:
                if i._help is not None:
                    Log.info(prefix + "  " + i._name + ": " + i._help)
    def _serialize (self):
        ser = {
            "type" : "Caller",
            "name" : self._name,
            "oname" : self._oname,
            "help" : self._help,
            "args" : list ([i._serialize() for i in self._args])
        }
        return ser
    @staticmethod
    def _deserialize (entry):
        caller = Caller(entry['oname'], help=entry["help"])
        arglist = []
        for i in entry['args']:
            cls = ARGTYPES[i["type"]] if i["type"] in ARGTYPES else Arg
            c = cls._deserialize(i)
            arglist.append(c)
        caller._args = tuple(arglist)
        return caller
class Namespace (object):
    def __init__ (self, name, *args, help = None):
        self._parent = None
        self._path = []
        self._top = None
        self._name = name.replace(" ", "_")
        self._oname = name
        self._help = help
        self._children = {}
        self._isRoot = False
        for i in args:
            self._addChild(i)
    def set_top (self, top):
        self._top = top
        if self._parent is not None:
            self._path = self._parent._path + [self._name]
        else:
            self._path = []
        for i in self._children.values():
            i.set_top(top)

    def _addChild (self, command):
        self._children[command._name] = command
        command._parent = self
    @property
    def _childNamespaces (self):
        lst = []
        for i in self._children.values():
            if isinstance(i, Namespace):
                lst.append(i)
        lst.sort(key=lambda x: x._name)
        return lst
    @property
    def _childCalls (self):
        lst = []
        for i in self._children.values():
            if isinstance(i, Caller):
                lst.append(i)
        lst.sort(key=lambda x: x._name)
        return lst
    def __getattr__(self, name):
        if name in self._children:
            return self._children[name]
        raise AttributeError("Attr " + name + " does not exist.")

    def __str__ (self):
        return "(N) " + "::".join(self._path)

    def _dump (self, includeHelp = False, *args, **kwargs):
        prefix = "".ljust(len(self._path)*4)
        if (self._isRoot):
            Log.info(prefix + "<Root>")
        else:
            Log.info(prefix + str(self))
        if (includeHelp):
            if self._help is not None:
                Log.info(prefix + "  " + self._help)
        cns = self._childNamespaces
        ccall = self._childCalls
        if len(cns) > 0:
            Log.info(prefix + "  [Namespaces]")
            for v in cns:
                v._dump(*args,includeHelp=includeHelp,**kwargs)
        if len(ccall) > 0:
            Log.info(prefix + "  [Calls]")
            for v in ccall:
                v._dump(*args,includeHelp=includeHelp,**kwargs)
    def _serialize (self):
        ser = {
            "type" : "Namespace",
            "name" : self._name,
            "oname" : self._oname,
            "help" : self._help,
            "children" : list ([i._serialize() for i in self._children.values()])
        }
        return ser
    @staticmethod
    def _deserialize (entry):
        ns = Namespace(entry['oname'], help=entry["help"])
        for i in entry['children']:
            if i["type"] == "Namespace":
                c = Namespace._deserialize(i)
            elif i["type"] == "Caller":
                c = Caller._deserialize(i)
            else:
                Log.error("Unknown type: {}".format(i))
                continue
            ns._addChild(c)
        return ns

def qmode (*argsnames):
    return list([Arg(i) for i in argsnames])

class MxConnection (object):
    _RE_LOGITEM=re.compile(r'\d+-\d+-\d+\s+\d+:\d+:\d+,\d+\s+\[\w+\].*')
    _NOT_CONNECTED = 0
    _IDLE_NOT_RDY = 1
    _IDLE_RDY = 2
    _BSY = 3
    _CONNECTION_DROPPED = 4

    RE_ACCEPT_CMDS = re.compile("^MX>\s*$")

    def __init__ (self, config):
        self._config = config
        self._proc = None
        self._st = self._NOT_CONNECTED
        self._sout = None
        self._sin = None
        self._serr = None
        self._cubemx = None# self._config.tool("stm32cubemx")
        config.configureLogger(LogCubeLogs)
        config.configureLogger(LogCubeResp)
        config.configureLogger(LogCubeExec)
        config.configureLogger(Log)

        x = config._apiSchema
        if x is not None:
            self._ns = Namespace._deserialize(x)
        else:
            self._ns = Namespace("",
                Caller("help"),
                Caller("exit"),
            )
        self._ns.set_top(self)


        """
        self._ns = Namespace("",
            Namespace("config",
                Caller("load",          ArgFile("file", condition=ArgFile.CondFile)),
                Caller("save"),
                Caller("saveas",        ArgFile("file", condition=ArgFile.CondRwcLikely)),
                Caller("saveext",       ArgFile("file", condition=ArgFile.CondRwcLikely))
            ),
            Caller("help"),
            Caller("exit"),
        )
        """
        self._ns._isRoot = True
    def __del__ (self):
        self.disconnect()

    def __enter__ (self):
        Log.debug("**ENTER**")
        self.connect()
        return self

    def __exit__ (self, type, value, traceback):
        Log.debug("**EXIT**")
        self.disconnect()

    def disconnect (self):
        Log.info("Disconnecting")
        if self._proc is not None:
            try:
                coder = Coder("exit")
                self._transact(coder)
                Log.info("Waiting for exit")
                self._proc.wait(5)
            except TimeoutExpired as e:
                Log.info("Timeout - Force")
                try:
                    self._proc.kill()
                    Log.info("Tried to kill the process.")
                except:
                    pass
            except:
                pass
            self._proc = None

    def connect (self):
        self._cubemx = self._config.tool("stm32cubemx")
        self._cubemx_inter = self._cubemx.command("interactive")
        cmd = [self._cubemx_inter.path] + list(self._cubemx_inter.arguments)
        Log.info(">> " + " ".join(cmd))
        self._proc = Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        self._st = self._IDLE_NOT_RDY
        #self._st = self._IDLE_RDY
        #Popen

    def __getattr__(self, name):
        return self._ns.__getattr__(name)

    def _makeNamespace (self, nspath):
        if nspath is None or len(nspath) == 0:
            return self._ns

        nsSearchPath = nspath if isinstance(nspath, (tuple,list)) else nspath.strip().split(" ")
        nscur = self._ns
        nsnext = None
        nscurpath = []

        Log.debug ("mkNamespace: " + "/".join(nsSearchPath))

        for i in nsSearchPath:
            nscurpath.append(i)
            if i in nscur._children:
                nsnext = nscur._children[i]
                if isinstance(nsnext, Namespace):
                    if len(nspath) > 1:
                        nscur = nsnext
                    else:
                        return nsnext
                else:
                    raise MxNsPathException("Path '{}' is not a namespace in search for namespace '{}'.", " ".join(nscurpath), " ".join(nsSearchPath))
            else:
                nsnext = Namespace(i)
                nscur._addChild(nsnext)
                nsnext.set_top(i)
                nscur = nsnext

        return nscur

    def _transact (self, transact):
        Log.debug("mx exec>> " + transact.command)
        if self._st == self._NOT_CONNECTED:
            self.connect()

        if self._st == self._IDLE_NOT_RDY:
            while True:
                line = self._proc.stdout.readline().decode("ascii")
                LogCubeLogs.debug ("(log)" + line)
                if len(line) == 0:
                    self._st = self._CONNECTION_DROPPED
                    transact.fail(MxStatus.MxConnectError)
                    return
                else:
                    if "MX>" in line: # indicator that it is ready to process commands
                        self._st = self._IDLE_RDY
                        break
        time.sleep(0.2)
        if self._st == self._IDLE_RDY:
            self._st = self._BSY
            try:
                LogCubeExec.debug("(start) " + transact.command)
                self._proc.stdin.write(bytes(transact.command + "\n","ascii"))
                self._proc.stdin.flush()
                while transact.pending:
                    line = self._proc.stdout.readline().decode("ascii")
                    if len(line) == 0:
                        self._st = self._CONNECTION_DROPPED
                        transact.fail(MxStatus.MxTerminated)
                        return
                    line = line.rstrip()
                    m = self._RE_LOGITEM.match(line)
                    if m:
                        LogCubeLogs.debug("(log) " + line)
                    else:
                        LogCubeResp.debug("(recv) " + line)
                        transact._emit(line)
            except (EOFError,ChildProcessError,BrokenPipeError) as e:
                Log.error("Error: {}".format(str(e)))
                transact.fail(MxStatus.MxTerminated)
                self._st = self._CONNECTION_DROPPED
            except:
                Log.exception("Exception Caught")
                transact.fail(MxStatus.MxTerminated)
                self._st = self._CONNECTION_DROPPED
            finally:
                self._st = self._IDLE_RDY
                LogCubeExec.debug("(done) " + transact.command + " -> " + transact.status.name)
        else:
            Log.error("Error: Bad State {}".format(self._st))
            transact.fail(MxStatus.MxTerminated)

    def _detect (self, ns = None, recursive = False):
        scanList = [ns]
        count = 0
        while len(scanList) > 0:
            nsName = scanList[0].replace(" ", "::") if scanList[0] is not None else "<Root>"
            Log.info ("Detecting: {}".format(nsName))
            coder = DetectCoder(self, scanList[0])
            del scanList[0]
            self._transact(coder)
            children = coder.finish()
            count += len(children) if count is not None else 0
            if coder.status != MxStatus.MxOK:
                Log.info ("Detecting failed for {} (Status {})".format(nsName, coder.status.name))
                if coder.status == MxStatus.MxTerminated:
                    return
            elif recursive:
                if not recursive:
                    continue
                if children is not None:
                    for i in children:
                        if isinstance(i, Namespace):
                            Log.info ("Adding '{}' to detect queue.".format("::".join(i._path)))
                            scanList.append(" ".join(i._path))
        Log.info ("** Detection Completed - Found {} items. **".format(count))

    def dump (self,*args,**kwargs):
        self._ns._dump(*args,**kwargs)
    def _serialize (self):
        return self._ns._serialize ()
