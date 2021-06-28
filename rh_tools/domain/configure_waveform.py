import json
from rh_tools.scene import utils
from rh_tools.domain import domain_tools
from ossie.utils import redhawk

def configure_waveform(wfm_inst, wfm_config):
    """Configure the waveform

    This function can be used to configure the waveform after initial
    launch.

    .. warning:: Seems to work within a Python console.
        But get "weakly-referenced object no longer exists" calling from
        command line.

    Parameters
    ----------
    wfm_config : dict
        The dictionary of key(parameter name) and value
        (parameter setting)
    """
    n_tries = 3
    for prop in wfm_config:
        for retry in range(n_tries):
            try:
                wfm_inst.__setattr__(prop, wfm_config[prop])
                break;
            except:
                print("failed on %d of %d"%(retry+1, n_tries))


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--domain", default="REDHAWK_DEV", help="Domain")
    parser.add_argument("waveform", help="Waveform to connect")
    parser.add_argument("config", help="Waveform config in a json file.")
    parser.add_argument("--debug", action="store_true", help="Run api to verify")
    args = parser.parse_args()


    # ------------------------  extract config  -----------------------------
    with open(args.config) as fid:
        config = json.load(fid)
    config = utils.convert_dict(config)

    # get waveform
    wfm_inst = domain_tools.find_waveform_from_domain(args.domain, args.waveform)

    # apply config
    configure_waveform(wfm_inst, wfm_config=config)