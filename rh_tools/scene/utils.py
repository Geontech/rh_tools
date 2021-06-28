from collections import OrderedDict
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
        elif isinstance(c_val, list):
            c_val = convert_list(c_val)

        # store in output dict
        out[str(key)] = c_val

    return out

def convert_list(my_list):
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
    out = []
    assert isinstance(my_list, list), "Expecting a list"
    for elem in my_list:
        if isinstance(elem, dict):
            c_val = convert_dict(elem)
        elif isinstance(elem, list):
            c_val = convert_list(elem)
        elif isinstance(elem, unicode):
            c_val = str(elem)
        else:
            c_val = elem

        # store in output list
        out.append(c_val)

    return out

def get_instance(unique_id, comp_dict, wfm_dict):
    """Get instance specified from the unique_id

    The unique_id should be unique in the comp_dict and
    wfm_dict keys.

    .. warning:: Unique id for both comp_dict and
        wfm_dict is expected, but not enforced.

    Parameters
    ----------
    unique_id : str
        The unique id for the component or waveform.

    comp_dict : OrderedDict
        The dictionary of component instances.  If unique_id refers
        to a component, the unique_id should match one of the keys.

    wfm_dict : OrderedDict
        The dictionary of waveform instances.  If unique_id refers
        to a waveform, the unique_id should match one of the keys.

    Returns
    -------
    inst : component or waveform instance, or None
        Return None if unique_id is not a match for any key in
        either dictionary
    """
    if unique_id in comp_dict:
        return comp_dict[unique_id]
    elif unique_id in wfm_dict:
        return wfm_dict[unique_id]
    else:
        return None