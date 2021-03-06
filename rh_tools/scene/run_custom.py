#!/usr/bin/env python
"""Convenience function to specify a Redhawk scenario in JSON.

This module supports loading in a scenario in the Redhawk sandbox,
loading components and setting up connections.

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
from ossie.utils import sb, redhawk
import json
from collections import OrderedDict
import time
import sys
import uuid
from pprint import pprint
import time
import warnings
from rh_tools.scene.utils import convert_dict, get_instance
from rh_tools.scene import component_helper
from rh_tools.scene import waveform_helper
from rh_tools.scene import message_helper
from rh_tools.scene import throughput_helper
if sys.version_info.major == "2":
    # Python2 user prompt
    user_prompt = raw_input
else:
    # Python3 user prompt
    user_prompt = input
TIME_INC = 1 # 1 sec updates

def setup_domains(domain_dict, delay=5):
    """Setup domains specified

    Attempts to attach or kick start a list of domains with the
    specified device managers.

    .. warning:: Currently does not support launching device managers
        when attaching to a domain

    Parameters
    ----------
    domain_dict : dict
        Dictionary of domain specs.  The key will be the domain name.
        The supported fields include:
            devices_managers : list
    """
    active_domains = redhawk.scan()

    for domain in domain_dict:
        # extract potential list of device managers
        dev_mgrs = domain_dict[domain].get("device_managers", [])

        # -----------------------  setup domain instance  -------------------
        if domain in active_domains:
            # attach to active domain
            dom = redhawk.attach(domain)

        else:
            # kick start domain
            if dev_mgrs:
                dom = redhawk.kickDomain(domain, device_managers=dev_mgrs)
            else:
                # no device managers.. just launch domain
                dom = redhawk.kickDomain(domain, kick_device_managers=False)

            # allow delay x number of device managers to load
            time.sleep(delay * len(dev_mgrs))

        # -----------------------  check device managers  -------------------
        if dev_mgrs:
            # check if device managers have been loaded
            for dev_mgr in dev_mgrs:
                if dev_mgr not in dom.devMgrs:
                    warnings.warn("Have not implemented setting up device"+\
                        " managers on an active domain")



def load_and_run_scenario(json_file, time_inc=1, wfm=""):
    """Load a scenario and run

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
        settings = convert_dict(settings)
    elif isinstance(json_file, dict):
        settings = json_file
    else:
        raise ValueError("Expecting a string json filepath or dict")

    # extract from dictionary (verify keys exist)
    comp_specs = settings.get("components", {})
    wave_specs = settings.get("waveforms", {})
    domain_specs = settings.get("domains", {})
    conns = settings["connections"]
    simm = settings["simulation"]
    debug = settings.get("debug", {})

    if domain_specs:
        setup_domains(domain_specs)

    # ---------------------------  load components  -------------------------
    comp_dict = component_helper.launch_components(sb, comp_specs)

    # --------------------------  load waveforms  ---------------------------
    wfm_dict = waveform_helper.launch_waveforms(wave_specs)

    # ----------------------  connect message sinks  ------------------------
    msg_sinks, msg_store = message_helper.connect_msg_sinks(
        sb, comp_dict, wfm_dict, debug)

    # -------------------------  setup connections  -------------------------
    for conn in conns:
        try:
            obj_1 = get_instance(conn[0], comp_dict, wfm_dict)
            port_1 = obj_1.getPort(str(conn[1]))
            obj_2 = get_instance(conn[2], comp_dict, wfm_dict)
            port_2 = obj_2.getPort(str(conn[3]))
            port_1.connectPort(port_2,
                "conn_%s_to_%s_"%(str(conn[0]), str(conn[2]))\
                + str(uuid.uuid1()))
        except Exception as e:
            print("Error running connection %s"%str(conn))
            raise
    # ---------------------------  setup debug  ---------------------------
    throughput_ports = throughput_helper.setup_throughput(
        debug.get("throughput", []),
        comp_dict=comp_dict, wfm_dict=wfm_dict)

    # --------------------------  save waveform  ----------------------------
    if wfm:
        raise NotImplementedError("Waveform Generation is not working")
        # NOTE: Generated waveform does not track component settings

        with open(wfm + ".sad.xml", "w") as fid:
            fid.write(sb.generateSADXML(wfm))

    # --------------------------  run simulation  ---------------------------
    if simm["type"].lower() in ["time"]:
        print("In time simulation")
        waveform_helper.start_waveforms(wfm_dict)
        component_helper.start_in_reverse_order(comp_dict)

        tic = time.time()
        while time.time() - tic < simm["value"]["duration"]:
            # show message being passed
            message_helper.show_messages(msg_sinks, msg_store)

            # show port throughput statistics
            throughput_helper.show_throughput(throughput_ports)

            # sleep a little
            time.sleep(time_inc)

        component_helper.stop_in_order(comp_dict)
        waveform_helper.stop_waveforms(wfm_dict)
        #sb.stop()

    elif simm["type"].lower() in ["user"]:
        # run till user hits enter
        sb.start()
        resp = user_prompt("Hit enter to exit")
        sb.stop()

    else:
        raise RuntimeError("Unexpected type of simulation")

    # save messages
    if msg_store:
        message_helper.save_messages(msg_store)

    # TODO: release components/waveforms/devices/domains
    waveform_helper.release_waveforms(wfm_dict)
    throughput_helper.close(throughput_ports)

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