# rh_tools

## rh_tools.bulkio

### record_waveform
This will connect output bulkio ports of waveforms to FileSinks.  The file sinks are configured to bluefiles to record information regarding the signal.

## rh_tools.domain

### domain_tools
This module houses some helper functions for finding the following things on a specified domain by name:
* Waveforms
* Event Channels

## rh_tools.message
This folder houses some modules for either recording or sending message events

### event_channel_to_waveform_forwarding
This will listen for messages on a given event channel on a given domain.
It will then forward messages to a waveform.

One use case is in the application of waveform you don't own.  Instead of putting the event channel into the waveform, this will allow you  to dynamically forward messages observed on the event channel to a given port on the waveform.

### record_waveform
This module uses a JSON file to specify the domain and waveform/message output ports to record from.  The recordings are saved through pickle serialization for further analysis.

### send_message
This module uses a JSON file to specify a message structure.  The message is either sent to a waveform's input message port or to an event channel (or both).  This will allow quickly configuring a message to feed into the system for testing.