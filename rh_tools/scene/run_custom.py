#!/usr/bin/env python
"""Convenience function to specify a Redhawk scenario in JSON.

This module supports loading in a scenario in the Redhawk sandbox,
loading components and setting up connections.

.. note:: Currently only support loading components.

Example
--------
JSON Format:

>>> scene = {
>>>     "components": {
>>>         "Source":{
>>>             "key":"rh.FileReader",
>>>             "val":{
>>>                 "source_uri":filepath,
>>>                 "playback_state":"PLAY"
>>>             },
>>>         "Sink":{
>>>             "key":"rh.FileWrite",
>>>             "val":{}
>>>         },
>>>     },
>>>     "connections":[
>>>         ["Source", "dataFloat_out", "Sink", "dataFloat_in"]
>>>     ],
>>>     "simulation":{
>>>         "type":"time",
>>>         "value":{
>>>             "duration": 10.0
>>>         }
>>>     }
>>>    "debug":{
>>>        "throughput":[
>>>            ["Source0", "dataFloat_out"],
>>>         ],
>>>         "message_sink":[
>>>             ["Source", "output_msg_port_name"]
>>>         ]
>>>     }
>>> }
"""
from ossie.utils import sb
import json
from collections import OrderedDict
import time
import sys
from pprint import pprint
if sys.version_info.major == "2":
    # Python2 user prompt
    user_prompt = raw_input
else:
    # Python3 user prompt
    user_prompt = input
TIME_INC = 1 # 1 sec updates

def convert_dict(my_dict):
    """Convert dictionary from json load.

    Corrects a dictionary from json load, where strings are
    in the unicode format.  This function will recursively
    parse a dictionary to convert unicode to string.

    Parameters
    ----------
    my_dict : dict
        A dictionary loaded from json.

    Returns
    -------
    out_dict : dict
        Output should convert both keys and values that are
        unicode over to str.
    """
    # --------------------------  error checking  ---------------------------
    assert isinstance(my_dict, dict), "Expecting dict"

    # convert
    out = OrderedDict()
    for key in my_dict:
        # get current value
        c_val = my_dict[key]

        # do necessary conversions
        if isinstance(c_val, unicode):
            c_val = str(c_val)
        elif isinstance(c_val, dict):
            c_val = convert_dict(c_val)

        out[str(key)] = c_val
    return out

def start_in_reverse_order(my_comps):
    """Start the ordered list of components in reversed order

    Assuming the user sets up the scenario from a source -> sink,
    this function will start all component, but from the last component
    first, and the first component last.  Thus sinks will start prior
    to the sources.

    Parameters
    ----------
    my_comps : OrderedDict
        The list of components in the scenario.
    """
    my_list = my_comps.items()
    for ind in range(len(my_comps) - 1, -1, -1):
        my_list[ind][1].start()

def load_and_run_scenario(json_file, time_inc=1, wfm=""):
    """Load a scenario and run

    .. warn:: Support for generating waveform not implemented yet.

    Parameters
    ----------
    json_file : str, dict
        The path to a JSON specifying the scenario.  This should include
        "components", "connections", "simulation"

    time_inc : float
        Time increment to run simulation.  After each increment, check
        the debug (throughput)

    wfm : str
        Specify a file to save the scenario to waveform.
        Don't save if empty string
    """
    if isinstance(json_file, str):
        settings = json.load(open(json_file), encoding='ascii')
    elif isinstance(json_file, dict):
        settings = json_file
    else:
        raise ValueError("Expecting a string json filepath or dict")

    # extract from dictionary (verify keys exist)
    comps = settings.get("components", {})
    waves = settings.get("waveforms", {})
    conns = settings["connections"]
    simm = settings["simulation"]
    debug = settings.get("debug", {})
    msg_sinks = OrderedDict()

    # ---------------------------  load components  -------------------------
    comp_dict = OrderedDict()
    for comp in comps:
        c_comp = comps[comp]
        # launch component
        comp_dict[comp] = sb.launch(c_comp["key"])

        # -------------------------  configure  -----------------------------
        # FIXME : potentially may want to control the order of this.
        # remove unicode
        new_dict = convert_dict(c_comp["val"])
        comp_dict[comp].configure(new_dict)

        # ------------------ if log level specified, update  ----------------
        log_lvl = c_comp.get("log")
        if log_lvl:
            comp_dict[comp].log.setLevel(log_lvl)

    for msink in debug.get("message_sink", []):
        # initialize msg sinks
        new_key = "(%s)_(%s)"%(str(msink[0]), str(msink[1]))
        msg_sinks[new_key] = sb.MessageSink(storeMessages=True)

        # connect component output to msg sink
        comp_dict[str(msink[0])].connect(msg_sinks[new_key],
            usesPortName=str(msink[1]))

    # --------------------------  load waveforms  ---------------------------
    # TODO: don't know how to launch from sb

    # -------------------------  setup connections  -------------------------
    for conn in conns:
        # NOTE: order is [comp1, port1, comp2, port2]
        comp_1 = comp_dict[conn[0]]
        comp_2 = comp_dict[conn[2]]
        port_1 = conn[1]
        port_2 = conn[3]

        # ------------------------  connect  --------------------------------
        # FIXME: this works for component may differ if supporting waveforms
        comp_1.connect(comp_2, usesPortName=port_1, providesPortName=port_2)

    # ---------------------------  setup debug  ---------------------------
    try:
        throughput_ports = {}
        for tmp_port in debug.get("throughput", []):
            tmp_c = str(tmp_port[0]) # convert from unicode
            tmp_p = str(tmp_port[1]) # conver from unicode
            tmp_name = tmp_c + "_" + tmp_p
            throughput_ports[tmp_name] = comp_dict[tmp_c].getPort(tmp_p)
    except Exception as e:
        print("Exception caught %s"%str(e))
        throughput_ports = {}

    # --------------------------  save waveform  ----------------------------
    if wfm:
        raise NotImplementedError("Waveform Generation is not working")
        # NOTE: Generated waveform does not track component settings

        with open(wfm + ".sad.xml", "w") as fid:
            fid.write(sb.generateSADXML(wfm))

    # --------------------------  run simulation  ---------------------------
    if simm["type"].lower() in ["time"]:
        print("In time simulation")
        start_in_reverse_order(comp_dict)

        tic = time.time()
        while time.time() - tic < simm["value"]["duration"]:
            # show message being passed
            show_messages(msg_sinks)

            # show port throughput statistics
            show_throughput(throughput_ports)

            # sleep a little
            time.sleep(time_inc)
        sb.stop()

    elif simm["type"].lower() in ["user"]:
        # run till user hits enter
        sb.start()
        resp = user_prompt("Hit enter to exit")
        sb.stop()
    elif simm["type"].lower() in ["data"]:
    	# NOTE: the number of samples is specified in the "head" component
        # TODO: assert that a head component is in components
        raise NotImplementedError("No setup for running on fixed data out")
    else:
        raise RuntimeError("Unexpected type of simulation")

def show_messages(message_sinks):
    """Show messages received at a given port

    Parameters
    ----------
    message_sinks : dict
        Dictionary where key is a function of the input comp and port
        The value is the message received.
    """
    for key in message_sinks.keys():

        # get the current message sink
        m_sink = message_sinks[key]

        # print out the message received on the sink
        msgs = m_sink.getMessages()
        if msgs:
            print("=" * 30 + "\nFrom %s\n"%key + "="*30)
            pprint(msgs)

def show_throughput(ports):
    """Display throughput at specified ports

    Parameters
    ----------
    ports : dict
        Each key should be descriptive of the component/port
        Each value will be an instance of a uses port.
    """
    # TODO: improve the layout
    for key in ports:
        try:
            # NOTE: the 0th statistics is for the first connection
            print("%s: elements per second = %3.4f"%\
                (key, ports[key].statistics[0].statistics.elementsPerSecond))
        except Exception as e:
            print(e)

if __name__ == "__main__":
    # ------------------------  parse input arguments  ----------------------
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("json", help="Scene config stored in json")
    parser.add_argument("--time_inc", default=1, type=float,
        help="Time inc to run")
    parser.add_argument("--out", default="",
        help="The output file to save waveform")
    args = parser.parse_args()

    # ---------------------------------  process  ---------------------------
    # run the simulation
    load_and_run_scenario(args.json, time_inc=args.time_inc, wfm=args.out)