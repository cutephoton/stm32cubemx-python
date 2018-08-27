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

## Existing Command Database

The current command database. It's far from perfect/tested as it was automatically
generated from an imperfect dataset.

```
** Showing Command Db **
 <Root>
   [Namespaces]
     (N) add
       [Calls]
         (C) add::template_dir()
     (N) check
       [Namespaces]
         (N) check::mcu
           [Calls]
             (C) check::mcu::modes()
                check modes for current mcu
         (N) check::mcus
           [Calls]
             (C) check::mcus::modes()
                 check all modes for all mcus
             (C) check::mcus::xml()
                 open all the mcus
         (N) check::mode
           [Calls]
             (C) check::mode::enabled()
                 Check mode enable <Periph> <Mode Name>: check mode enability
     (N) clock
       [Calls]
         (C) clock::resolution()
             resolve clock issues
     (N) config
       [Calls]
         (C) config::load(String path)
             load <file>: open saved config
         (C) config::save()
             save: save config
         (C) config::saveas(String path)
             save <file>: save config
     (N) csv
       [Calls]
         (C) csv::pinout(String file)
     (N) disable
       [Namespaces]
         (N) disable::project
           [Calls]
             (C) disable::project::generate()
                 project generate true/false
     (N) export
       [Calls]
         (C) export::script()
             export configAsScript <outputscript>
     (N) generate
       [Calls]
         (C) generate::all_code_in_main()
             generate all code in main.c
         (C) generate::code(String path)
         (C) generate::one_file_per_ip()
             generate one file per ip
     (N) get
       [Namespaces]
         (N) get::available
           [Calls]
             (C) get::available::modes(String peripheral_regular_expression_match)
                get a list of available modes in a peripheral
               peripheral_regular_expression_match: (.* for all)
         (N) get::gpio
           [Calls]
             (C) get::gpio::parameters(String matching_pin,String matching_parameter)
                get the gpio parameter value on a pin
         (N) get::ip
           [Calls]
             (C) get::ip::parameters(String matching_ip,String param_name)
                get the ip parameter value
         (N) get::mapped
           [Calls]
             (C) get::mapped::modes(String peripheral_regular_expression_match)
                get a list of set modes in a peripheral
               peripheral_regular_expression_match: (.* for all)
         (N) get::mcu
           [Calls]
             (C) get::mcu::name()
             (C) get::mcu::package()
             (C) get::mcu::peripherals()
         (N) get::possible
           [Calls]
             (C) get::possible::remaps(String signal_regex)
                list all possible remaps of a matching signal
       [Calls]
         (C) get::available-analog-signals(String pin_name)
         (C) get::dest_path()
           get your template destination path
         (C) get::functions(String pin_regex)
            list all possible functions of a pin
         (C) get::mode(Enum unnamed{active | available | all},String peripheral)
            get mode(s) for a given peripheral
           peripheral: (.* for all)
         (C) get::mode_param_list(String peripheral,String active_mode)
            get parameter(s) for a given active mode
         (C) get::mode_param_pattern(String peripheral,String active_mode,String pattern)
            get all pattern parameter(s) for a given active mode
         (C) get::mode_param_possvalue(String peripheral,String active_mode,String parameter)
            get parameter possible value(s) for a given active mode parameter
         (C) get::modes(String peripheral_regular_expression_match)
            get a list of all leaf modes in a peripheral
           peripheral_regular_expression_match: (.* for all)
         (C) get::pinout()
            get the mcu pinout
         (C) get::signal(String pin)
            get the signal set on a pin
         (C) get::sub-mode-state(String Periph)
         (C) get::sub-modes(String Periph)
         (C) get::tpl_path()
           get your template source path
         (C) get::version()
             print current version
     (N) import
       [Namespaces]
         (N) import::get
           [Calls]
             (C) import::get::report()
                 get import report
         (N) import::set
           [Calls]
             (C) import::set::Option()
                 set manual import option
         (N) import::try
           [Namespaces]
             (N) import::try::auto
               [Calls]
                 (C) import::try::auto::import()
                     import ioc mcu to current mcu, then write the report
           [Calls]
             (C) import::try::import()
                 try import
             (C) import::try::import_and_log()
                 import ioc mcu to current mcu, then write the report
       [Calls]
         (C) import::GPIOconstraint()
             constraints on GPIO <constrainedGPIO>: will set the signal from pin origin to pin target
         (C) import::add_compatibility_rule()
             hack_rules <file>: open saved config
         (C) import::channelconstraint()
             constraints on channel <IPOrigin> <channelOrigin> <IPDestination> <channelDestination>: change channel for described IPs
         (C) import::hackmxdb()
             hackmxdb import <pin name> <signal name>: will hack the MxDb by deleting all Alternates Pins for <signal name> except for <pin name>
         (C) import::openioc()
             load import ioc file
     (N) not_a_possible_value
       [Namespaces]
         (N) not_a_possible_value::ip
           [Calls]
             (C) not_a_possible_value::ip::parameters(String matching_ip,String param_name,String param_value)
                is ip parameter value not allowed?
     (N) pinout
       [Namespaces]
         (N) pinout::check
           [Namespaces]
             (N) pinout::check::keep
               [Namespaces]
                 (N) pinout::check::keep::user
                   [Calls]
                     (C) pinout::check::keep::user::placement()
         (N) pinout::uncheck
           [Namespaces]
             (N) pinout::uncheck::keep
               [Namespaces]
                 (N) pinout::uncheck::keep::user
                   [Calls]
                     (C) pinout::uncheck::keep::user::placement()
     (N) possible_value
       [Namespaces]
         (N) possible_value::ip
           [Calls]
             (C) possible_value::ip::parameters(String matching_ip,String param_name,String param_value)
                is ip parameter value allowed?
     (N) project
       [Namespaces]
         (N) project::get
           [Calls]
             (C) project::get::heapsize()
                get minimum heap size
             (C) project::get::stacksize()
                get minimum stack size
         (N) project::set
           [Calls]
             (C) project::set::heapsize(String heapsize)
                set minimum heap size
             (C) project::set::stacksize(String stacksize)
                set minimum stack size
       [Calls]
         (C) project::couplefilesbyip()
            Peripheral initialization done in main or in separate IPs files.
         (C) project::generate()
            generates full project
         (C) project::generateunderroot()
            Project files generated under project root directory instead of specific subdir .
         (C) project::import()
             import project setting parameters
         (C) project::name(String name)
            set project name
         (C) project::path(String path)
            set project path
         (C) project::save()
             save project setting
         (C) project::toolchain(String toolchain)
            set toolchain
         (C) project::toolchainlocation(String toolchain_location)
            set toolchainlocation
     (N) reset
       [Calls]
         (C) reset::mode(String Periph,String Mode_Name)
            reset a mode in a peripheral
         (C) reset::noparam(String ip_regexp)
         (C) reset::pin(String pin_name)
         (C) reset::pin-signal()
             reset pin <pin name> <signal name>
         (C) reset::signal(String signal_name)
         (C) reset::userconst(String userconstant)
            remove a user constant. No error reporting
     (N) set
       [Namespaces]
         (N) set::gpio
           [Calls]
             (C) set::gpio::parameters(String matching_pin,String param_name,String param_value)
                set the gpio parameter value on a pin
         (N) set::ip
           [Calls]
             (C) set::ip::no_ui_warning(String matching_ip)
                disable warnings in ip ui
             (C) set::ip::parameters(String matching_ip,String param_name,String param_value)
                set the ip parameter value
       [Calls]
         (C) set::dest_path(String path)
           set your template destination path
         (C) set::mode(String Periph,String Mode_Name)
            set a mode in a peripheral
         (C) set::noparam(String ip_regexp)
         (C) set::pin(String pin_name,String signal_name)
         (C) set::tpl_path(String path)
           set your template source path
         (C) set::userconst(String userconstant,String value)
            add or update a user constant with new value
         (C) set::username(String Periph,String User_Name)
            set a User name for a peripheral
   [Calls]
     (C) clearpinout()
        remove all the pin mapping
     (C) exit()
        exit
     (C) help()
        Get usage information.
     (C) load(String mcu)
        open mcu xml file
     (C) log(String level)
     (C) script(String file)
        execute all command in file
     (C) setDriver()
         set Ip driver
     (C) tinyload(String mcu)
        load mcu for pinout only
     (C) waitclock()
         Wait for a delay in seconds until clock has finished its initialization
```
