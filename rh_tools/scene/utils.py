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

        out[str(key)] = c_val
    return out