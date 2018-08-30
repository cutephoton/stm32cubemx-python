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
from pycubemx import MxConnection, Config

c = Config.LocalConfig()
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
<Root>
  [Namespaces]
    (N) add
      [Namespaces]
        (N) add::mw
          [Calls]
            (C) add::mw::(argcount=5)
                >> add mw name root_dir mode_file config_file template_dir
    (N) boardselector
      [Namespaces]
        (N) boardselector::get
          [Calls]
            (C) boardselector::get::mcuseries(argcount=0)
                >> boardselector get mcuseries
            (C) boardselector::get::type(argcount=0)
                >> boardselector get type
            (C) boardselector::get::vendor(argcount=0)
                >> boardselector get vendor
        (N) boardselector::list
          [Namespaces]
            (N) boardselector::list::selected
              [Calls]
                (C) boardselector::list::selected::peripherals(argcount=0)
                    >> boardselector list selected peripherals
          [Calls]
            (C) boardselector::list::boards(argcount=0)
                >> boardselector list boards
            (C) boardselector::list::mcuseries(argcount=0)
                >> boardselector list mcuseries
            (C) boardselector::list::peripherals(argcount=0)
                >> boardselector list peripherals
            (C) boardselector::list::types(argcount=0)
                >> boardselector list types
            (C) boardselector::list::vendors(argcount=0)
                >> boardselector list vendors
        (N) boardselector::set
          [Calls]
            (C) boardselector::set::mcuseries(argcount=1)
                >> boardselector set mcuseries <mcuseriesName[,mcuseriesName...]>
            (C) boardselector::set::peripheral(argcount=2)
                >> boardselector set peripheral <periphName> <nbinstance>
            (C) boardselector::set::type(argcount=1)
                >> boardselector set type <typeName[,typeName...]>
            (C) boardselector::set::vendor(argcount=1)
                >> boardselector set vendor <vendorName[,vendorName...]>
        (N) boardselector::unset
          [Calls]
            (C) boardselector::unset::mcuseries(argcount=1)
                >> boardselector unset mcuseries <mcuseriesName[,mcuseriesName...]>
            (C) boardselector::unset::type(argcount=1)
                >> boardselector unset type <typeName[,typeName...]>
            (C) boardselector::unset::vendor(argcount=1)
                >> boardselector unset vendor <vendorName[,vendorName...]>
      [Calls]
        (C) boardselector::close(argcount=0)
            >> boardselector close
        (C) boardselector::open(argcount=0)
            >> boardselector open
        (C) boardselector::reset(argcount=0)
            >> boardselector reset
        (C) boardselector::search(argcount=1)
            >> boardselector search <PartNumber>
    (N) check
      [Namespaces]
        (N) check::mcu
          [Calls]
            (C) check::mcu::modes(argcount=0)
                >> check mcu modes: check modes for current mcu
        (N) check::mcus
          [Calls]
            (C) check::mcus::modes(argcount=0)
                >> check all modes for all mcus
            (C) check::mcus::xml(argcount=0)
                >> open all the mcus
        (N) check::mode
          [Calls]
            (C) check::mode::enabled(argcount=2)
                >> Check mode enable <Periph> <Mode Name>: check mode enability
    (N) clock
      [Namespaces]
        (N) clock::set
          [Calls]
            (C) clock::set::hclk(argcount=1)
                >> clock set hclk
      [Calls]
        (C) clock::resolution(argcount=0)
            >> resolve clock issues
    (N) config
      [Calls]
        (C) config::load(argcount=1)
            >> load <file>: open saved config
        (C) config::save(argcount=0)
            >> save: save config
        (C) config::saveas(argcount=1)
            >> save <file>: save config
        (C) config::saveext(argcount=1)
            >> save <file>: save extended config
    (N) csv
      [Calls]
        (C) csv::pinout(argcount=0)
            >> csv pinout <file>
    (N) disable
      [Namespaces]
        (N) disable::project
          [Calls]
            (C) disable::project::generate(argcount=1)
                >> project generate true/false
    (N) dma
      [Calls]
        (C) dma::add(argcount=1)
            >> dma add <dma request name>: add dma request
        (C) dma::available_controller_requests(argcount=1)
            >> dma available_controller_requests <controller name>: list available dma requests for a given controller
        (C) dma::available_controller_streams(argcount=2)
            >> dma available_controller_streams <request name> <controller name>: list available dma streams for a given request in a given controller
        (C) dma::available_periph_requests(argcount=1)
            >> dma available_periph_requests <peripheral name>: list available dma requests for a given peripheral
        (C) dma::available_streams(argcount=1)
            >> dma available_streams <request name>: list available dma streams for a given request
        (C) dma::delete(argcount=1)
            >> dma delete <dma request name>: delete all dma requests having a given name
        (C) dma::delete_all(argcount=0)
            >> dma delete_all: delete all dma requests
        (C) dma::get_param(argcount=2)
            >> usage: dma get_param <request name> <param name>; get dma parameter value for a given request
        (C) dma::is_available(argcount=1)
            >> dma is_available <request name>: is request available
        (C) dma::is_available_in(argcount=2)
            >> dma is_available_in <request name> <controller name>: is request available in controller
        (C) dma::list(argcount=1)
            >> dma list <dma request name>: list all dma requests having a given name
        (C) dma::list_all(argcount=0)
            >> dma list_all: list all dma requests
        (C) dma::list_controller(argcount=1)
            >> dma list_controller <controller name>: list dma requests for a given controller
        (C) dma::list_periph(argcount=1)
            >> dma list_periph <peripheral name>: list dma requests for a given peripheral
        (C) dma::listbriefly(argcount=1)
            >> dma listbriefly <dma request name>: list all dma requests having a given name
        (C) dma::set_flow(argcount=2)
            >> usage: dma set_flow <request name> <flow name> ; set dma flow for a given request
        (C) dma::set_param(argcount=3)
            >> usage: dma set_param <request name> <param name> <value>; set dma parameter value for a given request
        (C) dma::used_flows(argcount=0)
            >> dma used_flows: list all used dma flows
    (N) export
      [Calls]
        (C) export::script(argcount=1)
            >> export configAsScript <outputscript>
    (N) generate
      [Calls]
        (C) generate::all_code_in_main(argcount=0)
            >> generate all code in main.c
        (C) generate::code(argcount=1)
            >> generate code <path>
        (C) generate::one_file_per_ip(argcount=0)
            >> generate one file per ip
    (N) get
      [Namespaces]
        (N) get::available
          [Calls]
            (C) get::available::modes(argcount=1)
                >> get available modes <peripheral regular expression match (.* for all)>: get a list of available modes in a peripheral
        (N) get::gpio
          [Calls]
            (C) get::gpio::parameters(argcount=2)
                >> get gpio parameters <matching pin> <matching parameter>: get the gpio parameter value on a pin
        (N) get::ip
          [Calls]
            (C) get::ip::parameters(argcount=2)
                >> get ip parameters <matching ip> <param name>: get the ip parameter value
        (N) get::mapped
          [Calls]
            (C) get::mapped::modes(argcount=1)
                >> get mapped modes <peripheral regular expression match (.* for all)>: get a list of set modes in a peripheral
        (N) get::mcu
          [Calls]
            (C) get::mcu::name(argcount=0)
                >> get mcu name
            (C) get::mcu::package(argcount=0)
                >> get mcu package
            (C) get::mcu::peripherals(argcount=0)
                >> get mcu peripherals
        (N) get::possible
          [Calls]
            (C) get::possible::remaps(argcount=1)
                >> get possible remaps <signal regex>: list all possible remaps of a matching signal
      [Calls]
        (C) get::available-analog-signals(argcount=1)
            >> get available-analog-signals <pin name>
        (C) get::dest_path(argcount=0)
            >> get dest_path:get your template destination path
        (C) get::functions(argcount=1)
            >> get functions <pin regex>: list all possible functions of a pin
        (C) get::mode(argcount=2)
            >> get mode <active|available|all> <peripheral (.* for all)>: get mode(s) for a given peripheral
        (C) get::mode_param_list(argcount=2)
            >> get mode_param_list <peripheral> <active_mode>: get parameter(s) for a given active mode
        (C) get::mode_param_pattern(argcount=2)
            >> get mode_param_pattern <peripheral> <active_mode> <pattern>: get all pattern parameter(s) for a given active mode
        (C) get::mode_param_possvalue(argcount=3)
            >> get mode_param_possvalue <peripheral> <active_mode> <parameter>: get parameter possible value(s) for a given active mode parameter
        (C) get::modes(argcount=1)
            >> get modes <peripheral regular expression match (.* for all)>: get a list of all leaf modes in a peripheral
        (C) get::pinout(argcount=0)
            >> get pinout: get the mcu pinout
        (C) get::signal(argcount=1)
            >> get signal <pin>: get the signal set on a pin
        (C) get::sub-mode-state(argcount=2)
            >> get sub-mode-state <Periph> <moderoot,submode1,submode1.1>
        (C) get::sub-modes(argcount=1)
            >> get sub-modes <Periph>
        (C) get::tpl_path(argcount=0)
            >> get tpl_path:get your template source path
        (C) get::version(argcount=0)
            >> print current version
    (N) import
      [Namespaces]
        (N) import::get
          [Calls]
            (C) import::get::report(argcount=1)
                >> get import report
        (N) import::set
          [Calls]
            (C) import::set::Option(argcount=2)
                >> set manual import option
        (N) import::try
          [Namespaces]
            (N) import::try::auto
              [Calls]
                (C) import::try::auto::import(argcount=1)
                    >> import ioc mcu to current mcu, then write the report
          [Calls]
            (C) import::try::import(argcount=0)
                >> try import
            (C) import::try::import_and_log(argcount=1)
                >> import ioc mcu to current mcu, then write the report
      [Calls]
        (C) import::GPIOconstraint(argcount=1)
            >> constraints on GPIO <constrainedGPIO>: will set the signal from pin origin to pin target
        (C) import::add_compatibility_rule(argcount=4)
            >> hack_rules <file>: open saved config
        (C) import::channelconstraint(argcount=4)
            >> constraints on channel <IPOrigin> <channelOrigin> <IPDestination> <channelDestination>: change channel for described IPs
        (C) import::hackmxdb(argcount=2)
            >> hackmxdb import <pin name> <signal name>: will hack the MxDb by deleting all Alternates Pins for <signal name> except for <pin name>
        (C) import::openioc(argcount=1)
            >> load import ioc file
    (N) list
      [Namespaces]
        (N) list::unsupported
          [Calls]
            (C) list::unsupported::mcus(argcount=0)
                >> list unsupported mcus
    (N) mdma
      [Calls]
        (C) mdma::add_channel_request(argcount=2)
            >> mdma add_channel_request <mdma channel name> <mdma request name>: add mdma request on channel
        (C) mdma::add_request(argcount=1)
            >> mdma add_request <mdma request name>: add mdma request
        (C) mdma::delete_all_requests(argcount=0)
            >> mdma delete_all_requests: delete all mdma requests
        (C) mdma::delete_channel(argcount=1)
            >> mdma delete_channel <mdma channel name>: delete all mdma requests on a given channel
        (C) mdma::delete_request(argcount=1)
            >> mdma delete_request <mdma request name>: delete all mdma requests having a given name
        (C) mdma::list_all_requests(argcount=0)
            >> mdma list_all_requests: list all mdma requests
        (C) mdma::list_channel_requests(argcount=1)
            >> mdma list_channel_requests <mdma channel name>: list all mdma requests on a given channel
        (C) mdma::list_nth_request_on_channel(argcount=3)
            >> mdma list_nth_request_on_channel <mdma channel name> <request rank> <request name>: list nth request on a channel
        (C) mdma::list_nth_request_parameters(argcount=2)
            >> mdma list_nth_request_parameters <mdma channel name> <request rank>: list nth request parameters on a channel
        (C) mdma::list_peripheral_requests(argcount=1)
            >> mdma list_peripheral_requests <peripheral name>: list mdma requests for a given peripheral
        (C) mdma::list_request(argcount=1)
            >> mdma list_request <mdma request name>: list all dma requests having a given name
    (N) not_a_possible_value
      [Namespaces]
        (N) not_a_possible_value::ip
          [Calls]
            (C) not_a_possible_value::ip::parameters(argcount=3)
                >> not_a_possible_value ip parameters <matching ip> <param name> <param value>: is ip parameter value not allowed?
    (N) nvic
      [Calls]
        (C) nvic::disable(argcount=1)
            >> nvic disable <IRQ number>: disable interrupt
        (C) nvic::enable(argcount=1)
            >> nvic enable <IRQ number>: enable interrupt
        (C) nvic::get_enable_state(argcount=1)
            >> nvic get_enable_state: get interrupt enable state
        (C) nvic::get_interrupts(argcount=0)
            >> nvic get_interrupts: get interrupts
        (C) nvic::get_ip_interrupts(argcount=1)
            >> nvic get_ip_interrupts <IP name>: get IP interrupts
        (C) nvic::get_irqhandlergenerated(argcount=1)
            >> nvic get_irqhandlergenerated <IRQ number>: get interrupt 'IRQ handler generated' flag
        (C) nvic::get_priority(argcount=1)
            >> nvic get_priority <IRQ number>: get interrupt preemption priority
        (C) nvic::get_prioritygroup(argcount=0)
            >> nvic get_prioritygroup: get interrupt priority group
        (C) nvic::get_subpriority(argcount=1)
            >> nvic get_subpriority <IRQ number>: get interrupt subpriority
        (C) nvic::get_usesfreertosfunctions(argcount=1)
            >> nvic get_usesfreertosfunctions <IRQ number>: get interrupt 'uses freeRTOS functions' flag
        (C) nvic::set_irqhandlergenerated(argcount=2)
            >> nvic set_irqhandlergenerated <IRQ number> <boolean value>: set/reset interrupt 'IRQ handler generated' flag
        (C) nvic::set_priority(argcount=2)
            >> nvic set_priority <IRQ number> <preemption priority>: set interrupt preemption priority
        (C) nvic::set_prioritygroup(argcount=1)
            >> nvic set_prioritygroup <priority group>: set interrupt priority group
        (C) nvic::set_subpriority(argcount=2)
            >> nvic set_subpriority <IRQ number> <subpriority>: set interrupt subpriority
        (C) nvic::set_usesfreertosfunctions(argcount=2)
            >> nvic set_usesfreertosfunctions <IRQ number> <boolean value>: set/reset interrupt 'uses freeRTOS functions' flag
    (N) possible_value
      [Namespaces]
        (N) possible_value::ip
          [Calls]
            (C) possible_value::ip::parameters(argcount=3)
                >> possible_value ip parameters <matching ip> <param name> <param value>: is ip parameter value allowed?
    (N) project
      [Namespaces]
        (N) project::get
          [Calls]
            (C) project::get::heapsize(argcount=0)
                >> project get heapsize: get minimum heap size
            (C) project::get::stacksize(argcount=0)
                >> project get stacksize: get minimum stack size
        (N) project::set
          [Calls]
            (C) project::set::heapsize(argcount=1)
                >> project set heapsize <heapsize>: set minimum heap size
            (C) project::set::stacksize(argcount=1)
                >> project set stacksize <stacksize>: set minimum stack size
      [Calls]
        (C) project::couplefilesbyip(argcount=1)
            >> project couplefilesbyip <1/0>: Peripheral initialization done in main or in separate IPs files.
        (C) project::generate(argcount=0)
            >> project generate: generates full project
        (C) project::generateunderroot(argcount=1)
            >> project generateunderroot <1/0>: Project files generated under project root directory instead of specific subdir .
        (C) project::import(argcount=0)
            >> import project setting parameters
        (C) project::name(argcount=1)
            >> project name <name>: set project name
        (C) project::path(argcount=1)
            >> project path <path>: set project path
        (C) project::save(argcount=1)
            >> save project setting
        (C) project::toolchain(argcount=1)
            >> project toolchain <toolchain>: set toolchain
        (C) project::toolchainlocation(argcount=1)
            >> project toolchainlocation <toolchain location>: set toolchainlocation
    (N) reset
      [Calls]
        (C) reset::mode(argcount=2)
            >> reset mode <Periph> <Mode Name>: reset a mode in a peripheral
        (C) reset::noparam(argcount=1)
            >> reset noparam <ip regexp>
        (C) reset::pin(argcount=1)
            >> reset pin <pin name>
        (C) reset::pin-signal(argcount=2)
            >> reset pin <pin name> <signal name>
        (C) reset::signal(argcount=1)
            >> reset signal <signal name>
        (C) reset::userconst(argcount=1)
            >> reset userconst <userconstant> : remove a user constant. No error reporting
    (N) selector
      [Namespaces]
        (N) selector::get
          [Calls]
            (C) selector::get::core(argcount=0)
                >> selector get core
            (C) selector::get::family(argcount=0)
                >> selector get family
            (C) selector::get::package(argcount=0)
                >> selector get package
            (C) selector::get::subfamily(argcount=0)
                >> selector get subfamily
        (N) selector::list
          [Namespaces]
            (N) selector::list::selected
              [Calls]
                (C) selector::list::selected::peripherals(argcount=0)
                    >> selector list selected peripherals
          [Calls]
            (C) selector::list::cores(argcount=0)
                >> selector list cores
            (C) selector::list::families(argcount=0)
                >> selector list families
            (C) selector::list::mcus(argcount=0)
                >> selector list mcus
            (C) selector::list::packages(argcount=0)
                >> selector list packages
            (C) selector::list::peripherals(argcount=0)
                >> selector list peripherals
            (C) selector::list::subfamilies(argcount=0)
                >> selector list subfamilies
        (N) selector::set
          [Namespaces]
            (N) selector::set::io
              [Calls]
                (C) selector::set::io::min(argcount=1)
                    >> selector set io min <value>
          [Calls]
            (C) selector::set::core(argcount=1)
                >> selector set core <coreName[,coreName...]>
            (C) selector::set::family(argcount=1)
                >> selector set family <familyName[,familyName...]>
            (C) selector::set::package(argcount=1)
                >> selector set package <packageName[,packageName...]>
            (C) selector::set::peripheral(argcount=2)
                >> selector set peripheral <periphName> <nbinstance>
            (C) selector::set::subfamily(argcount=1)
                >> selector set subfamily <subFamilyName[,subFamilyName...]>
        (N) selector::unset
          [Calls]
            (C) selector::unset::core(argcount=1)
                >> selector unset core <coreName[,coreName...]>
            (C) selector::unset::family(argcount=1)
                >> selector unset family <familyName[,familyName...]>
            (C) selector::unset::package(argcount=1)
                >> selector unset package <packageName[,packageName...]>
            (C) selector::unset::subfamily(argcount=1)
                >> selector unset subfamily <subFamilyName[,subFamilyName...]>
      [Calls]
        (C) selector::close(argcount=0)
            >> selector close
        (C) selector::open(argcount=0)
            >> selector open
        (C) selector::reset(argcount=0)
            >> selector reset
        (C) selector::search(argcount=1)
            >> selector search <PartNumber>
    (N) set
      [Namespaces]
        (N) set::gpio
          [Calls]
            (C) set::gpio::parameters(argcount=3)
                >> set gpio parameters <matching pin> <param name> <param value>: set the gpio parameter value on a pin
        (N) set::ip
          [Calls]
            (C) set::ip::no_ui_warning(argcount=1)
                >> set ip no_ui_warning <matching ip>: disable warnings in ip ui
            (C) set::ip::parameters(argcount=3)
                >> set ip parameters <matching ip> <param name> <param value>: set the ip parameter value
      [Calls]
        (C) set::dest_path(argcount=1)
            >> set dest_path <path>:set your template destination path
        (C) set::mode(argcount=2)
            >> set mode <Periph> <Mode Name>: set a mode in a peripheral
        (C) set::noparam(argcount=1)
            >> set noparam <ip regexp>
        (C) set::pin(argcount=2)
            >> set pin <pin name> <signal name>
        (C) set::tpl_path(argcount=1)
            >> set tpl_path <path>:set your template source path
        (C) set::userconst(argcount=2)
            >> set userconst <userconstant> <value> : add or update a user constant with new value
        (C) set::username(argcount=2)
            >> set username <Periph> <User Name>: set a User name for a peripheral
    (N) tooltip
      [Namespaces]
        (N) tooltip::log
          [Calls]
            (C) tooltip::log::off(argcount=0)
                >>  tooltip log off: hide the tooltip content in log
            (C) tooltip::log::on(argcount=0)
                >>  tooltip log on: display the tooltip content in log
  [Calls]
    (C) clearpinout(argcount=0)
        >> clearpinout: remove all the pin mapping
    (C) exit(argcount=0)
        >> exit: exit
    (C) help(argcount=0)
    (C) load(argcount=1)
        >> load <mcu>: open mcu xml file
    (C) log(argcount=1)
        >> log <level>
    (C) setDriver(argcount=1)
        >> set Ip driver
    (C) tinyload(argcount=1)
        >> tinyload <mcu>: load mcu for pinout only
    (C) waitclock(argcount=1)
        >> Wait for a delay in seconds until clock has finished its initialization
```
