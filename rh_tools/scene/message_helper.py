from collections import OrderedDict
from pprint import pprint
import json
import pickle
import pandas
import uuid
from rh_tools.scene.waveform_helper import get_port
def connect_msg_sinks(sb, comp_dict, wfm_dict, debug):
    """Connect message sinks to the components and waveforms

    Parameters
    ----------
    sb : module
        The sandbox module from ossie.utils

    comp_dict : OrderedDict
        The keys are the unique ids for the components.
        The values are the instances of the component.

    wfm_dict : OrderedDict
        The keys are the unique ids for the waveforms
        The values are the instances of the waveforms.

    debug : dict
        This dictionary support throughput and message
        sinks to connect at various output ports of the
        components/waveforms.
    """
    # initialize output
    msg_sinks = OrderedDict()
    msg_store = OrderedDict()

    for msink in debug.get("message_sink", []):
        # -------------------  initialize msg sinks  ------------------------
        new_key = "(%s)_(%s)"%(str(msink[0]), str(msink[1]))
        msg_sinks[new_key] = sb.MessageSink(storeMessages=True)

        if msink[0] in comp_dict:
            # connect component output to msg sink
            comp_dict[str(msink[0])].connect(msg_sinks[new_key],
                usesPortName=str(msink[1]))

        elif msink[0] in wfm_dict:
            tmp_p = get_port(wfm_dict[str(msink[0])], msink[1])
            tmp_p.obj_ptr.connectPort(
                msg_sinks[new_key].getPort("msgIn"),
                "msink_conn_" + str(uuid.uuid1()))
            #wfm_dict[str(msink[0])].connect(msg_sinks[new_key],
            #    usesPortName=str(msink[1]))

        # -------------------------  setup storage  -------------------------
        filename = ""
        out_format = "json"
        if len(msink) > 2:
            filename = msink[2]
        if len(msink) > 3:
            out_format = msink[3]

        msg_store[new_key] = {
            "filename":filename,
            "format":out_format,
            "messages":[]
        }

    return msg_sinks, msg_store


def show_messages(message_sinks, msg_store):
    """Show messages received at a given port

    Parameters
    ----------
    message_sinks : dict
        Dictionary where key is a function of the input comp and port
        The value is the message received.

    msg_store : dict
        Dictionary of the message (and output options).  This is
        updated by the method to store new messages
    """
    for key in message_sinks.keys():

        # get the current message sink
        m_sink = message_sinks[key]

        # print out the message received on the sink
        msgs = m_sink.getMessages()

        if msgs:
            print("=" * 30 + "\nFrom %s\n"%key + "="*30)
            pprint(msgs)

            # append messages
            msg_store[key]["messages"] += msgs

def save_messages(msg_store):
    """Save messages

    Save the messages stored

    Parameters
    ----------
    msg_store : dict
        Dictionary with the keys being the unique id of port
        The value should be another dictionary with fields:
            'filename' the filepath to save to
            'format' from {'json', 'pickle'}
            'messages' the list of messages stored from the
                given port.
    """
    for key in msg_store:
        if msg_store[key]["filename"] != "":
            # save to file
            with open(msg_store[key]["filename"], "w") as fid:
                if msg_store[key]["format"] == "json":
                    json.dump(msg_store[key]["messages"], fid)
                elif msg_store[key]["format"] == "pickle":
                    pickle.dump(msg_store[key]["messages"], fid)
                else:
                    raise NotImplementedError(
                        "save_messages does not support format ()"\
                        %str(msg_store[key]["format"]))

def messages_to_csv(message_list, output_csv_file, remove_msg_name=True):
    """Store messages to CSV

    Parameters
    ----------
    message_list : list
        List of stored messages.  Typically the element will be a dictionary
        with the key being the name of the message type.  The fields of that
        dictionary would be the fields of the message.  This usually is in the
        format of "my_message::my_field", where "my_message" is the name of
        the message

    output_csv_file : str
        The path to save the CSV file

    remove_msg_name : bool
        Specify whether to clear the message name from the field name.

    Raises
    ------
    RuntimeError    If the list is empty
    """
    if len(message_list) > 0:
        msg_name = str(message_list[0].keys()[0])
        new_msg_list = []
        for elem in message_list:
            c_msg = elem[msg_name]

            # -------------------  reformat field names  --------------------
            if remove_msg_name:
                # remove 'message_name::' from keys
                new_msg = {}
                for key in c_msg:
                    new_key = key.replace("%s::"%msg_name, "")
                    new_msg[new_key] = c_msg[key]

                # store new list
                new_msg_list.append(new_msg)
            else:
                # keep msg name in fields
                new_msg_list.append(c_msg)

        df = pandas.DataFrame(new_msg_list)
        df.to_csv(open(output_csv_file, "w"))
    else:
        raise RuntimeError("Why are you giving me an empty list?")

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Load a save message file and convert to CSV")
    parser.add_argument("file", help="File to load from")
    parser.add_argument("--format", default="json",
        help="Format from {'json', 'pickle'")
    parser.add_argument("out", default="/tmp/output.csv",
        help="Output csv")
    parser.add_argument("--keep_msg_name", action="store_true")
    args = parser.parse_args()

    # ----------------------------  output file  ----------------------------
    if args.format == "json":
        my_list = json.load(open(args.file, "r"))
    elif args.format == "pickle":
        my_list = pickle.load(open(args.file, "r"))
    else:
        raise RuntimeError("Unexpected format %s"%str(args.format))
    try:
        rm_msg = not args.keep_msg_name
        messages_to_csv(my_list, args.out, remove_msg_name=rm_msg)
    except RuntimeError as e:
        print("Failed to process %s"%str(args.file))
        print(e)