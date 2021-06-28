import sys
from rh_tools.scene.utils import get_instance
def setup_throughput(tp_list, comp_dict, wfm_dict):
    """Setup the throughput ports dictionary

    The dictionary will describe the input source
    (componet, portname).  It will provide acces to the
    port, to get throughput statistics.  Potentially the
    throughput_port will also specify file outputs to store
    measurements.

    .. note:: Specifying a file can help isolate the throughput
        measurements from other standard output.

    Parameters
    ----------
    tp_list : list
        List of ports for measuring throughput.
        This can be a 2 tuple (component_id, port_name)
        If 4, (component_id, port_name, out_file, file_access)

    Returns
    -------
    tp_ports : dict
    """
    throughput_ports = {}
    try:
        for tmp_port in tp_list:
            tmp_c = str(tmp_port[0]) # convert from unicode
            tmp_p = str(tmp_port[1]) # convert from unicode
            tmp_name = tmp_c + "_" + tmp_p

            instance = get_instance(tmp_c, comp_dict, wfm_dict)
            if len(tmp_port) > 2:
                # expecting a filename and ""
                assert len(tmp_port) == 4,\
                    "Expecting 4 element list [Obj, port, file, file_access]"
                assert tmp_port[3] in ["a", "w"],\
                    "Expecting 'a' for append, or 'w' for overwrite"
                fid = open(tmp_port[2], tmp_port[3])
            else:
                # if not provided, default to standard out
                fid = sys.stdout

            # store the object, port, port instance and output
            throughput_ports[tmp_name] = {
                "object": tmp_c,
                "port": tmp_p,
                "instance":instance.getPort(tmp_p),
                "out":fid,
            }

        # write the header
        write_header(throughput_ports)
    except Exception as e:
        print("Exception caught %s"%str(e))
        throughput_ports = {}

    return throughput_ports

def show_throughput(tp_ports):
    """Display throughput at specified ports

    Parameters
    ----------
    ports : dict
        Each key should be descriptive of the component/port
        Each value will be an instance of a uses port.
    """
    for key in tp_ports:
        try:
            # get file or stdout
            fid = tp_ports[key]["out"]

            # NOTE: the 0th statistics is for the first connection
            c_port = tp_ports[key]
            port_inst = c_port["instance"]
            eps = port_inst.statistics[0].statistics.elementsPerSecond

            # write out.
            fid.write("%s,%s,%s\n"%(c_port["object"], c_port["port"], str(eps)))

        except Exception as e:
            print(e)

def write_header(tp_ports):
    for key in tp_ports:
        fid = tp_ports[key]["out"]
        fid.write("Component, Port, Elements Per Second\n")

def close(tp_ports):
    """Close the file out

    Parameters
    ----------
    throughput_ports : dict
        Dictionary of throughput ports from setup_throughput
    """
    for key in tp_ports:
        tp_ports[key]["out"].close()
