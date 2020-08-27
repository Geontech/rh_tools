# rh_tools

## rh_tools.domain
### domain_tools
This module houses some helper functions for finding the following things on a specified domain by name:
* Waveforms
* Event Channels

## rh_tools.message
This folder houses some modules for either recording or sending message events

### record_waveform
This module uses a JSON file to specify the domain and waveform/message output ports to record from.  The recordings are saved through pickle serialization for further analysis.

### send_message
This module uses a JSON file to specify a message structure.  The message is either sent to a waveform's input message port or to an event channel (or both).  This will allow quickly configuring a message to feed into the system for testing.