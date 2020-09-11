from ossie.utils import redhawk
def find_event_channel_from_domain(domain, name):
    try:
        dom = redhawk.attach(domain)
        for evt in dom.eventChannels:
            if evt.name == name:
                return evt

        # no match
        return None
    except:
        return None
def find_waveform_from_domain(domain, name):
    """Find a waveform by name on a given domain

    Scans through the list of waveforms to find one
    with the matching name.  The Waveforms will have
    a unique number attached, so this just finds the
    first instance that matches.

    Parameters
    ----------
    domain : str
        The name of the domain

    name : str
        Name of the waveform

    Returns
    -------
    output : waveform (ossie.cf.CF._objref_Application) or None
        If no match, return None
        If match return the first instance in waveforms that
        matches
    """
    try:
        dom = redhawk.attach(domain)
        return find_waveform(dom.apps, name)
    except:
        return None

def find_waveform(waveforms, name):
    """Find a waveform by name

    Scans through the list of waveforms to find one
    with the matching name.  The Waveforms will have
    a unique number attached, so this just finds the
    first instance that matches.

    Parameters
    ----------
    waveforms : list
        List of waveforms, typically from accessing
        applications on the domain.

    name : str
        Name of the waveform

    Returns
    -------
    output : waveform (ossie.cf.CF._objref_Application) or None
        If no match, return None
        If match return the first instance in waveforms that
        matches
    """
    for wvfm in waveforms:
        if name in wvfm.name:
            return wvfm
    return None