# rh_tools

This project houses some convenience function to help analyze and debug scenarios being run in Redhawk SDR framework.

---

## rh_tools.bulkio

### record_waveform (bulkio)

This will connect output bulkio ports of waveforms to FileSinks.  The file sinks are configured to bluefiles to record information regarding the signal.

---

## rh_tools.domain

### domain_tools

This module houses some helper functions for finding the following things on a specified domain by name:

* Waveforms
* Event Channels

---

## rh_tools.message

This folder houses some modules for either recording or sending message events

### event_channel_to_waveform_forwarding

This will listen for messages on a given event channel on a given domain.
It will then forward messages to a waveform.

One use case is in the application of waveform you don't own.  Instead of putting the event channel into the waveform, this will allow you to dynamically forward messages observed on the event channel to a given port on the waveform.

### record_waveform (messages)

This module uses a JSON file to specify the domain and waveform/message output ports to record from.  The recordings are saved through pickle serialization for further analysis.

### send_message

This module uses a JSON file to specify a message structure.  The message is either sent to a waveform's input message port or to an event channel (or both).  This will allow quickly configuring a message to feed into the system for testing.

## rh_tools.scene

### run_custom

This uses JSON specification to denote the scene in terms of components and connections.

<span style="color:red">06/15/2021: Currently only support components</span>

#### Debug

Debug options are available to identify common things of interest at a given port.

| Option | Description |
| --- | --- |
| Throughput | Measure the element per second out for a given port |
| Message Sink | Identify the messages out of a given port |