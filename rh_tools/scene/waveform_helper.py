from collections import OrderedDict
from ossie.utils import redhawk
import bulkio
def get_domain(domain, devices=[]):
    """Get the domain

    .. warn:: Enforcing device list has not been implemented

    Parameters
    ----------
    domain : str or None
        The name of the domain.  If None, tries to connect to
        available domain

    devices : list
        List of devices to launch with the domain.
    """
    active_domains = redhawk.scan()
    if domain in active_domains:
        # domain exists, just attach
        dom = redhawk.attach(domain)
    else:
        if devices:
            dom = redhawk.kickDomain(domain,
                kick_domain_managers=True, device_managers=devices)
        else:
            dom = redhawk.kickDomain(domain, kick_device_managers=False)

    # TODO: check that devices is available, otherwise launch them now
    pass

    return dom

def launch_waveform(wfm_name, wfm_config, domain=None, devices=[]):
    """Launch waveform and return waveform instance

    .. warn:: Waveforms require an active GPP node on the domain.

    Parameters
    ----------
    wfm_name : str
        Name of the waveform (i.e. 'rh.basic_components_demo)

    wfm_config : dict
        The configuration dictionary

    domain : str or None
        The domain to connect to.  If None, connect to one of them.

    devices : list
        Devices to launch.

    Returns
    -------
    wfm_inst : ossie.utils.redhawk.core.App
        The waveform instance

    wfm_unique_id : str
        The unique id assigned to this waveform instance

    Raises
    ------
    ApplicationInstallationError Invalid name or waveform not installed
    """
    # get the domain to launch waveform from
    dom = get_domain(domain, devices)

    # get a unique name
    ts = bulkio.timestamp.now()
    unique_name = str(wfm_name) + "_" + str(ts)

    # create the waveform instance
    wfm_inst = dom.createApplication(\
        application_sad=wfm_name,
        name=unique_name,
        initConfiguration=wfm_config,
        deviceAssignment=[],
    )
    return wfm_inst, unique_name

def get_port(wfm_inst, port_name):
    """Get the port from the waveform described by the name

    Parameters
    ----------
    wfm_inst : ossie.utils.redhawk.core.App
        Instance of the waveform, i.e. from launch_waveform

    Returns
    -------
    port_inst : CF.PortSet.PortInfoType or None
        The PortInfoType (this has 'name', 'description', 'direction',
        'obj_ptr', and 'repid')
    """
    ports = wfm_inst.getPortSet()
    for port in ports:
        if port.name == port_name:
            return port

    # return None, if port not found
    return None

def release_waveforms(wfm_dict):
    """Release waveforms

    Parameters
    ----------
    wfm_dict : dict
        A dictionary of waveform instances

    Raises
    ------
    AssertionError Error checking on the input parameters
    """
    # -------------------------  error checking  ----------------------------
    assert isinstance(wfm_dict, dict),\
        "Expecting a dictionary of waveform instances"

    # ------------------------  release waveforms  --------------------------
    for wfm in wfm_dict:
        try:
            # remove for dict
            wfm_inst = wfm_dict.pop(wfm)

            # release from domain
            wfm_inst.ref.releaseObject()
        except Exception as e:
            print("Issue with releasing %s"%wfm)
            print(e)

def launch_waveforms(wfm_specs):
    """Launch waveforms

    Parameters
    ----------
    wfm_specs : dict
        Dictionary of waveforms.  Each key is a unique id to
        describe the waveform.

        The fields are:
            'key': name of the waveform
            'val': configuration dict for the waveform
            'domain': domain to launch waveform
            'devices': devices to launch on the domain.

    Returns
    -------
    wfm_dict : OrderdDict
        The dictionary of waveform instances.  Each value is
        a ossie.utils.redhawk.core.App
    """
    wfm_dict = OrderedDict()

    for wfm_id in wfm_specs:
        wfm_inst, wfm_uid = launch_waveform(
            wfm_name=wfm_specs[wfm_id]["key"],
            wfm_config=wfm_specs[wfm_id]["val"],
            domain=wfm_specs[wfm_id].get("domain", None),
            devices=wfm_specs[wfm_id].get("devices", [])
        )
        wfm_dict[wfm_id] = wfm_inst

        log_specs = wfm_specs[wfm_id].get("log", {})
        for key in log_specs:
            wfm_inst.setLogLevel(key, log_specs[key])

    return wfm_dict

def start_waveforms(wfm_dict):
    """Start the waveform instances in wfm_dict

    Parameters
    ----------
    wfm_dict : OrderedDict
        The dictionary of waveform instances
    """
    for key in wfm_dict:
        try:
            wfm_dict[key].start()
        except Exception as e:
            print("Failed to start %s"%str(key))

def stop_waveforms(wfm_dict):
    """Stop the waveform instances in wfm_dict

    Parameters
    ----------
    wfm_dict : OrderedDict
        The dictionary of waveform instances
    """
    for key in wfm_dict:
        try:
            wfm_dict[key].ref.stop()
        except Exception as e:
            print("Failed to stop %s"%str(key))