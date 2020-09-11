#!/usr/bin/env python
"""
This module is intended to help provide recordings of bulkio streams
passed between waveforms.  A JSON configuration file is passed
in to describe the domain, waveform/ports to listen to.

Notes
-----
Example JSON file.  This module is only looking for message out ports.

{
    "domain":"REDHAWK_DEV",
    "ports":[
        ["Waveform1", "port_a", "floatIn", "/tmp/out1.bin"],
        ["Waveform1", "port_b", "octetIn", "/tmp/out2.bin"],
        ["Waveform2", "port_c", "shortIn", "/tmp/out3.bin"]
    ]
}

In this example, waveform1 and waveform2 are on the REDHAWK_DEV
domain.  The third parameter of ports ("*In") describes the type
of port and is the name of the input port of the file sink to
connect.  Finally, the last element of each port is the file to
store in.  Currently the files are stored as bluefiles.
"""
from ossie.utils import redhawk, sb
from rh_tools.domain.domain_tools import find_waveform
import uuid
import sys
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
        (WAVEFORM_NAME, PORT_NAME, PORT_DATA_TYPE OUTPUT_FILE)
        PORT_DATA_TYPE should match an input port of the sb.FileSink
        {"floatIn", "shortIn", "octetIn"}

    Returns
    -------
    my_msgs : dict
        Dictionary where keys is the combo of waveform + port name
        The value will be the recorded messages.
    """
    # --------------  connect and get list of waveforms  --------------------
    dom = redhawk.attach(domain)
    waveforms = dom.applications

    # ------------------------  prepare variables  --------------------------
    my_sink_list = {}

    # add a message sink per port
    for (c_name, c_port, c_type, c_file) in waveform_ports:
        # enforce strings
        c_name = str(c_name)
        c_port = str(c_port)
        c_type = str(c_type)
        c_file = str(c_file)

        print("Name = %s, Port = %s"%(str(c_name), str(c_port)))

        # select waveform from the list
        c_wave = find_waveform(waveforms, c_name)

        try:
            # get the port of interest
            port_inst = c_wave.getPort(c_port)

            # ---------------  connect to message sink  ---------------------
            f_sink = sb.FileSink(filename=c_file, midasFile=True)
            port_inst.connectPort(\
                f_sink.getPort(c_type),
                "conn_"+ str(uuid.uuid1()))
            f_sink.start()

            # track sink
            key = c_name + ":" + c_port
            my_sink_list[key] = f_sink
        except:
            print("Failed to connect to port:\t%s:%s"%(c_name, c_port))

    # -----------------------  user prompt to end  --------------------------
    if len(my_sink_list) > 0:
        prompt("Hit enter to end...")
    else:
        print("No connections set...exiting")

    # --------------------------  stop and release  -------------------------
    for key in my_sink_list.keys():
        try:
            my_sink_list[key].stop()
            my_sink_list[key].releaseObject()
        except Exception as e:
            print("Failed to release sink: %s"%str(e))


if __name__ == "__main__":
    # --------------------  parse command-line arguments  -------------------
    from argparse import ArgumentParser
    import json
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("json", help="JSon specification")
    args = parser.parse_args()

    # -----------------------  begin processing  ----------------------------
    with open(args.json, "r") as cfg:
        specs = json.load(cfg)

        # verify json information
        assert specs.get("domain") is not None, "Expecting a domain field"
        assert specs.get("ports") is not None, "Expecting a ports field"

        # listen to messages
        listen_waveform_ports(specs["domain"], specs["ports"])
