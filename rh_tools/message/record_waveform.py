#!/usr/bin/env python
"""
This module is intended to help provide recordings of messages
passed between waveforms.  A JSON configuration file is passed
in to describe the domain, waveform/ports to listen to.

The recorded messages are stored in a dictionary with the
waveform:port name as the keys.  This is serialized into a
pickle file for further analysis.

Notes
-----
Example JSON file.  This module is only looking for message out ports.

{
    "domain":"REDHAWK_DEV",
    "ports":[
        ["Waveform1", "port_a"],
        ["Waveform1", "port_b"],
        ["Waveform2", "port_c"]
    ]
}
"""
from ossie.utils import redhawk, sb
from rh_tools.domain.domain_tools import find_waveform
import uuid
import sys
import time
if sys.version_info.major == 2:
    prompt = raw_input
else:
    prompt = input

def listen_waveform_ports(domain, waveform_ports):
    """Listen to message events on specific waveform ports on domain

    Parameters
    ----------
    domain : str
        The Redhawk domain to connect

    waveform_ports : list of tuples
        This will be a list of ports.  Each tuple is a combination of
        (WAVEFORM_NAME, PORT_NAME)

    Returns
    -------
    my_msgs : dict
        Dictionary where keys is the combo of waveform + port name
        The value will be the recorded messages.
    """
    # --------------  connect  ----------------------------------------------
    dom = redhawk.attach(domain)

    # ------------------------  prepare variables  --------------------------
    my_msg_sinks = {}
    my_msgs = {}
    waveform_ports_connected = 0
    print_decimation = 0
    PRINT_EVERY_NTH_LOOP = 20

    while waveform_ports_connected < len(waveform_ports):
        if print_decimation == 0:
            print("Connecting ports ({} of {} complete) ...".format(waveform_ports_connected, len(waveform_ports)))
        print_decimation = (print_decimation + 1) % PRINT_EVERY_NTH_LOOP

        # --------------  get applications  ---------------------------------
        waveforms = dom.applications

        # add a message sink per port
        for (c_name, c_port) in waveform_ports:
            # enforce strings
            c_name = str(c_name)
            c_port = str(c_port)
            waveform_port_key = c_name + ":" + c_port

            if not waveform_port_key in my_msg_sinks:
                # select waveform from the list
                c_wave = find_waveform(waveforms, c_name)

                try:
                    # get the port of interest
                    port_inst = c_wave.getPort(c_port)

                    # ---------------  connect to message sink  ---------------------
                    msg_sink = sb.MessageSink(storeMessages=True)
                    port_inst.connectPort(\
                        msg_sink.getPort("msgIn"),
                        "conn_"+ str(uuid.uuid1()))
                    msg_sink.start()

                    # track sink
                    my_msg_sinks[waveform_port_key] = msg_sink
                    print("Connected Waveform Name = {}, Port Name = {}".format(str(c_name), str(c_port)))
                    waveform_ports_connected = waveform_ports_connected + 1
                except:
                    pass

        # Wait for a tenth of a second before trying again
        time.sleep(0.1)

    # -----------------------  user prompt to end  --------------------------
    if len(my_msg_sinks) > 0:
        prompt("Hit enter when you are finished recording messages ...")
    else:
        print("No connections set...exiting")

    # --------------------------  get messages  -----------------------------
    for key in my_msg_sinks.keys():
        my_msgs[key] = my_msg_sinks[key].getMessages()
        try:
            my_msg_sinks[key].releaseObject()
        except Exception as e:
            print("Failed to release msg sink: %s"%str(e))
    return my_msgs

if __name__ == "__main__":
    # --------------------  parse command-line arguments  -------------------
    from argparse import ArgumentParser
    import json
    description = \
        """
        Expecting a JSON config file to store a dictionary with a
        "domain" field specifying the str name of the domain.

        And a "ports" fields specifying the list of tuples
        (waveform_name, msg_output_port_name)\n
        """
    parser = ArgumentParser(description=description)
    parser.add_argument("json", help="JSon specification")
    parser.add_argument("--output", default="/tmp/recorded_messages.json", help="output file to save messages")
    parser.add_argument("--pickle", action="store_true", help="Output the data in pickle format instead of json")
    args = parser.parse_args()

    # -----------------------  begin processing  ----------------------------
    with open(args.json, "r") as cfg:
        specs = json.load(cfg)

        # verify json information
        assert specs.get("domain") is not None, "Expecting a domain field"
        assert specs.get("ports") is not None, "Expecting a ports field"

        # listen to messages
        msgs = listen_waveform_ports(specs["domain"], specs["ports"])

        # record message to file for further analysis
        if msgs and args.output:
            if args.pickle:
                import pickle
                pickle.dump(msgs, open(args.output, "w"))
            else:
                json.dump(msgs, open(args.output, "w"), indent=2)
