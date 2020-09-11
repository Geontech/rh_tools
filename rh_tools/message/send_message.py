from ossie.utils import sb, redhawk
from ossie.events import Subscriber, Publisher
from rh_tools.domain.domain_tools import find_waveform_from_domain
import uuid

def send_message(msg, wvfm, port_name, domain="REDHAWK_DEV", msg_id="default"):
    """Connect to waveform message in port and send message

    1. Connects to a domain.
    2. Searches for wavefor and gets input message port.
    3. Send message

    Parameters
    ----------
    msg : dict
        The message to transmit

    wvfm : str
        The name of the waveform to connect to.

    port_name : str
        The name of the port (on the specified wvfm)

    domain : str
        Name of the domain to attach and search for the waveform.

    msg_id : str
        The id of the message.
    """
    wvfm = find_waveform_from_domain(domain, wvfm)
    if wvfm:
        port = wvfm.getPort(port_name)
        msg_src = sb.MessageSource(msg_id)
        msg_port = msg_src.getPort("msgOut")
        #msg_port.connectPort(port, "conn_" + str(uuid.uuid1()))
        msg_src.connectPort(port, "conn_" + str(uuid.uuid1()))
        msg_src.start()
        msg_src.sendMessage(msg)
        msg_src.releaseObject()
    else:
        raise RuntimeWarning("Cannot find waveform on domain")


def publish_to_event_channel(msg, event_channel, domain="REDHAWK_DEV"):
    """Publish message to the event channel

    Parameters
    ----------
    msg : dict
        Message to publish

    event_channel : str
        The event channel to publish

    domain : str
        The name of domain to seek the event channel
    """
    try:
        dom = redhawk.attach(domain)
        pub = Publisher(dom, event_channel)

        pub.push(msg)
    except:
        raise

if __name__ == "__main__":
    from argparse import ArgumentParser
    import json
    import yaml
    parser = ArgumentParser()
    parser.add_argument("--domain", default="REDHAWK_DEV",
        help="Domain to connect")
    parser.add_argument("json", help="Json file describing message")
    parser.add_argument("--waveform", default="", help="Name of the waveform")
    parser.add_argument("--port", default="", help="Name of port on waveform")
    parser.add_argument("--evt_chan", default="",
        help="Event channel to publish")
    parser.add_argument("--msg_id", default="def_msg",
        help="The id of the message")
    args = parser.parse_args()

    # load message from json
    # NOTE: using yaml to avoid utf strings
    msg = yaml.safe_load(open(args.json, "r"))

    if args.evt_chan:
        print("Publish to event channel %s"%args.evt_chan)
        publish_to_event_channel(msg, args.evt_chan, args.domain)

    if args.waveform and args.port:
        print("Push message to specified waveform/port")
        send_message(msg, wvfm=args.waveform, port_name=args.port,
            domain=args.domain, msg_id=args.msg_id)