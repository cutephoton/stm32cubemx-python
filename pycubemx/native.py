
import sys
import os
import subprocess
import re
from pathlib import Path
from subprocess import Popen, PIPE, TimeoutExpired
import logging
import time
from enum import Enum
import select
import fcntl

Log = logging.getLogger(__name__)
LogCubeLogs = logging.getLogger("native.log")
LogCubeResp = logging.getLogger("native.response")
LogCubeExec = logging.getLogger("native.exec")
Encoding="ascii" # Can I use UTF-8 over the terminal? What other options are there?

__ALL__ = ("MxConnection", "MxException", "MxCommandError", "MxStatus",
           "Namespace", "Caller")

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

class Caller (object):
    def __init__ (self, name, argcount, coder = Coder, help = None):
        self._parent = None
        self._top = None
        self._path = None
        self._name = name.replace(" ", "_")
        self._oname = name
        self._argcount = argcount
        self._help = help
        self._coder = coder
        self._echo = False

    @property
    def _callable (self):
        return True

    def set_top (self, top):
        self._top = top
        if self._parent is not None:
            self._path = self._parent._path + [self._name]
        else:
            self._path = []

    def encode (self, args):
        if len(args) != self._argcount:
            raise MxException("Mismatched argument count. Got {} expected {}".format(len(args), self._argcount))
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
        return "(C) " + "::".join(self._path) + "(argcount={})".format(self._argcount)

    def _dump (self, wrfunc, *args, includeHelp = False, **kwargs):
        prefix = "".ljust((len(self._path)*4))
        wrfunc(prefix + str(self))
        if (includeHelp):
            if self._help:
                wrfunc(prefix + "    >> " + self._help)

    def _serialize (self):
        ser = {
            "type" : "Caller",
            "name" : self._name,
            "oname" : self._oname,
            "help" : self._help,
            "argcount" : self._argcount
        }
        return ser
    @staticmethod
    def _deserialize (entry):
        caller = Caller(entry['oname'], entry['argcount'], help=entry["help"])
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
    @property
    def _callable (self):
        return False
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

    def _getChild (self, name):
        if name in self._children:
            return self._children[name]
        return None

    def __getattr__(self, name):
        if name in self._children:
            return self._children[name]
        raise AttributeError("Attr " + name + " does not exist.")

    def __str__ (self):
        return "(N) " + "::".join(self._path)

    def _dump (self, wrfunc, includeHelp = False, *args, **kwargs):
        prefix = "".ljust(len(self._path)*4)
        if (self._isRoot):
            wrfunc(prefix + "<Root>")
        else:
            wrfunc(prefix + str(self))
        if (includeHelp):
            if self._help is not None:
                wrfunc(prefix + "  " + self._help)
        cns = self._childNamespaces
        ccall = self._childCalls
        if len(cns) > 0:
            wrfunc(prefix + "  [Namespaces]")
            for v in cns:
                v._dump(*args,includeHelp=includeHelp,wrfunc=wrfunc,**kwargs)
        if len(ccall) > 0:
            wrfunc(prefix + "  [Calls]")
            for v in ccall:
                v._dump(*args,includeHelp=includeHelp,wrfunc=wrfunc,**kwargs)
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
            # Implement the bare essentials for the command set (if not provided)
            self._ns = Namespace("",
                Caller("help",0),
                Caller("exit",0),
            )
        self._ns.set_top(self)
        self._ns._isRoot = True

    def __del__ (self):
        self.disconnect()

    def __enter__ (self):
        #Log.debug("**ENTER**")
        self.connect()
        return self

    def __exit__ (self, type, value, traceback):
        #Log.debug("**EXIT**")
        self.disconnect()

    def disconnect (self):
        Log.info("Disconnecting")
        if self._proc is not None:
            try:
                if self._st != self._CONNECTION_DROPPED:
                    Log.info("Waiting for exit")
                    try:
                        self._proc.stdin.write(bytes("exit\n",Encoding))
                        self._proc.stdin.flush()
                    except: pass
                self._proc.wait(5)
            except TimeoutExpired as e:
                Log.info("Timeout - Force")
                try:
                    self._proc.kill()
                    Log.info("Tried to kill the process.")
                except:
                    Log.exception("Unable to kill process. (Why?)")
                    pass
            except:
                Log.exception("OTHER EXCEPTION")
            self._proc = None
            self._st = self._NOT_CONNECTED

    def connect (self):
        if self._st == self._CONNECTION_DROPPED:
            self.disconnect()

        if self._st != self._NOT_CONNECTED:
            Log.info("Already connected.")
            return

        self._cubemx = self._config.STM32CubeMX
        try:
            if self._cubemx.valid is False:
                raise MxException("STM32CubeMX tool not found.")
            cmd = [self._cubemx.command] + list(self._cubemx.arguments) + ["-s"]
            Log.info(">> " + " ".join(cmd))

            Log.info("Connecting> " + " ".join(cmd))
            self._proc = Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE)
            self._st = self._IDLE_NOT_RDY

            Log.info("Waiting until session ready...")

            fd = self._proc.stdout.fileno()
            florig = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, florig | os.O_NONBLOCK)
            while True:
                sel = select.select([self._proc.stdout], [], [], 2.0)
                if len(sel[0]) == 0:
                    # Think we're good...
                    break
                else:
                    self._proc.stdout.read(1024) # discard content
            fcntl.fcntl(fd, fcntl.F_SETFL, florig)
            self._st = self._IDLE_RDY
            """while True:
                line = self._proc.stdout.readline().decode(Encoding)
                LogCubeLogs.debug ("(log)" + line)
                if len(line) == 0:
                    self._st = self._CONNECTION_DROPPED
                    transact.fail(MxStatus.MxConnectError)
                    return
                else:
                    if "MX>" in line: # indicator that it is ready to process commands
                        self._st = self._IDLE_RDY
                        break"""

            time.sleep(0.2)
            Log.info("Session Ready!")
        except FileNotFoundError as e:
            Log.error("Unable to locate STM32CubeMX executable.")
            raise MxException("STM32CubeMX cannot be executed.")
        except:
            Log.exception("Error occured while initializing session...")
            self.disconnect()
            raise MxException("STM32CubeMX cannot be executed.")

    def __getattr__(self, name):
        return self._ns.__getattr__(name)

    def _makeNamespace (self, nspath):
        if nspath is None or len(nspath) == 0:
            return self._ns

        nsSearchPath = nspath if isinstance(nspath, (tuple,list)) else nspath.strip().split(" ")
        nscur = self._ns
        nsnext = None
        nscurpath = []

        #Log.debug ("mkNamespace: " + "::".join(nsSearchPath))

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

        if self._st == self._IDLE_RDY:
            self._st = self._BSY
            try:
                LogCubeExec.debug("(start) " + transact.command)
                self._proc.stdin.write(bytes(transact.command + "\n",Encoding))
                self._proc.stdin.flush()
                while transact.pending:
                    line = self._proc.stdout.readline().decode(Encoding)
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
    """
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
        """
    def _getcall (self, api):
        base = self._ns
        for i in api:
            o = base._getChild(i)
            if o is None:
                return None
            base = o
        return base

    def dump (self,wrfunc=None,**kwargs):
        if wrfunc is None:
            wrfunc = lambda msg: Log.info(msg)
        self._ns._dump(wrfunc=wrfunc,**kwargs)

    def _serialize (self):
        return self._ns._serialize ()
"""

class DetectCoder (Coder):
    _RE_CMDDECL = re.compile(r'^\s\s([\w\s\d\-_]+\w)\s*(<[^:]+)?(:\s*?(.*))?$')
    _RE_ARGDECL = re.compile(r'<([\s\w\d,|]+)(\s(.*))?>')
    _RE_BASEDECL = re.compile(r'^(\s)?(\w.*)$')

    _ParserPending = 0
    _ParserAmbiguous = 1
    _ParserIsNs = 2
    _ParserIsCmd = 3

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
"""
