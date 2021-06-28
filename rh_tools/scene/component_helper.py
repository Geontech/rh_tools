from collections import OrderedDict
from rh_tools.scene.utils import convert_dict

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

def stop_in_order(my_comps):
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
    for key in my_comps.keys():
        try:
            my_comps[key].stop()
        except Exception as e:
            print("Error stopping %s"%str(key))
            print(e)

def launch_components(sb, comp_specs):
    """Launch the components in the specs

    .. warning::Log to file seems to work for rh.fileReader, but
        fails on custom made component.

    Parameters
    ----------
    sb : module
        The ossie.utils sandbox module

    comp_specs : dict
        The dictionary of component specifications.
        The keys are the unique id of the component.
        Each element will have fields:
            "key": name of the component in sb.catalog()
            "vals": the dictionary config for the component
            "log": specify the log level to run component.

    Returns
    -------
    comp_dict : OrderedDict
        The dictionary pointing to the component instances.
        The keys of this dictionary should match the keys of the
        comp_specs
    """
    # ---------------------------  load components  -------------------------
    comp_dict = OrderedDict()
    for comp in comp_specs:
        c_comp = comp_specs[comp]
        i_name = str(comp)

        # check for log entry
        log_entry = c_comp.get("log", {})
        log_file = log_entry.get("out_file", None)
        if log_file:
            # default to append
            access = log_entry.get("access", "a")
            assert access in ["a", "w"], "Access should be in {'a','w'}"
            log_file = open(log_file, access)

        # launch component
        comp_dict[comp] = sb.launch(c_comp["key"], instanceName=i_name,
            stdout=log_file)

        # -------------------------  configure  -----------------------------
        # FIXME : potentially may want to control the order of this.
        # remove unicode
        new_dict = convert_dict(c_comp["val"])
        comp_dict[comp].configure(new_dict)

        # ------------------ if log level specified, update  ----------------
        if log_entry:
            log_lvl = log_entry.get("level")

            if log_lvl:
                #comp_dict[comp].log.setLevel(log_lvl)
                comp_dict[comp].setLogLevel(i_name, log_lvl)

    return comp_dict

