# stm32cubemx-python: A tool to control STM32CUBEMX

This is a proof of concept to control STM32CUBEMX application via the internal
interactive test mode. This allows people to perform some operations
on their projects automatically. For example, generating and manipulating
the generation.

One use case, for example, is generating the firmware source code
at build time if the project's IOC file has been updated.

This is really early work. The command database was automatically generated
and may contain lots of errors. I scraped the help screens. Unfortunately,
the commands are outputted a bit inconsistently. It's a start...

The file 'cubemx-paths-local.json' provides example configuration that you need to
customize with local paths. (If I continue to development, I promise to make
this less dumb!)

`python3 -m pycubemx`

This will run CubeMX and have it show you the help prompt.

BTW, to access interactive mode manually:

`STM32CUBEMX -i`

Alright!

## Example Usage

See `test.py` for an example.

```
from pycubemx import MxConnection, Config, GetBaseConfig

c = GetBaseConfig ()
c.loadFile("cubemx-paths-local.json")
print("Command DB Version: " + str(c.commandDbVersionInfo))
with MxConnection(c) as x:
    help = x.help()
    for i in help:
        print("--> " + i)
```
