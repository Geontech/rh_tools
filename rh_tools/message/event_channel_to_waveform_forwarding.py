#!/usr/bin/env python
"""
This module is used to listen to a given event channel and
forward messages to a specific waveform input message port.

Notes
-----
The configuration file will be JSON with the fields
* domain (name of the domain)
* event_channel (source of message to forward)
* waveform (waveform to forward towards)
* port (port of the waveform to forward)
* msg_id (ID of the messages expected)

Example
-------
Specify the event channel to listen and forward messages to the
specified waveform port on the given domain

>>> {
>>>     "domain":"REDHAWK_DEV",
>>>     "event_channel":"event_channel",
>>>     "waveform":"my_waveform",
>>>     "port":"message_in",
>>>     "msg_id":"message_id"
>>> }
"""
from ossie.utils import redhawk, sb
from ossie.events import Subscriber, Publisher
from rh_tools.domain import domain_tools as DT
import uuid
from omniORB import CORBA, any
from pprint import pprint

def interpret_event(data):
    """Interpret the message event

    This is used to convert the Corba.Any structure to a
    Python dictionary

    Parameters
    ----------
    data : msg event on event channel
        This is an object returned by the callback function
        supplied to the Subscriber of the event channel.

    Returns
    -------
    out_list : list
        List of dictionaries.
    """
    msg_list = data.value()
    out_list = []
    for msg in msg_list:
        # top level is CORBA.Any the message type
        print("Message Id = %s"%str(msg.id))

        value = msg.value # Corba.Any
        typecode = msg.value.typecode() # Properties
        val_list = msg.value.value()
        out_dict = {}
        for val in val_list:
            out_dict[val.id] = val.value.value()
        out_list.append(out_dict)
    return out_list


class Forwarder:
    def __init__(self, msg_src):
        self._msg_src = msg_src
        self._msg_count = 0

    def forward(self, data):
        msg_list = interpret_event(data)
        for msg in msg_list:
            # FIXME: this can send messages the waveform is not expecting
            self._msg_src.sendMessage(msg)
            self._msg_count += 1
        return


def forward_event_to_waveform(domain, evt_chan, wave, port, msg_id):
    """Forwards message on an event channel to specified waveform input port

    Parameters
    ----------
    domain : str
        The name of the active domain.

    evt_chan : str
        The name of the event channel (on the specified domain)

    wave : str
        The name of the waveform on the domain

    port : str
        The name of the port on the waveform to forward messages.
    """
    # access the event channel and waveform port
    dom = redhawk.attach(domain)
    e_chan = DT.find_event_channel_from_domain(domain, evt_chan)
    wfm = DT.find_waveform_from_domain(domain, wave)
    port_inst = wfm.getPort(port)

    # setup message source and connect to waveform port
    # FIXME: there can be multiple messages on an event channnel.
    #       1) should this filter messages based on this msg id?
    #       2) Do I need a separate message source per msg_id?
    msg_src = sb.MessageSource(msg_id)
    msg_port = msg_src.getPort("msgOut")
    msg_port.connectPort(port_inst, "conn_" + str(uuid.uuid1()) )
    msg_src.start()

    # ----------------------  setup to forward messages ---------------------
    # setup the forwarder
    f = Forwarder(msg_src)

    # subscribe to channel with the callback in forwarder
    sub = Subscriber(dom, channel_name=evt_chan, dataArrivedCB=f.forward)

    # -----------  run forwarding until user hits enter  --------------------
    raw_input("Hit enter to exit")
    msg_src.releaseObject()

if __name__ == "__main__":
    # --------------------  parse command-line arguments  -------------------
    from argparse import ArgumentParser
    import json
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("json", help="JSon specification")
    args = parser.parse_args()

    with open(args.json, "r") as cfg:
        specs = json.load(cfg)

        # verify json information
        assert specs.get("domain") is not None, "Expecting a domain field"
        assert specs.get("event_channel") is not None,\
            "Expecting an event_channel field"
        assert specs.get("waveform") is not None, "Expecting a waveform field"
        assert specs.get("port") is not None, "Expecting a port field"
        assert specs.get("msg_id") is not None, "Expecting a msg_id field"

        forward_event_to_waveform(
            domain=specs["domain"],
            evt_chan=specs["event_channel"],
            wave=specs["waveform"],
            port=specs["port"],
            msg_id=specs["msg_id"])