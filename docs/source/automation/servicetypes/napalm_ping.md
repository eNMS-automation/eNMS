Uses Napalm to connect to the selected target device and performs a
ping. The output contains ping round trip time
statistics. 

![Napalm Ping Service](../../_static/automation/service_types/napalm_ping.png)

    !!! note

    The iosxr driver does not support ping, but the ios driver can be selected instead.

Configuration parameters for creating this service instance:

- All [Napalm Service Common Parameters](napalm_common.md).
- `Count`: Number of ping packets to send.
- `Packet Size`: Size of the ping packet payload to send in bytes.
- `Destination IP`: The IP address of the device to which to send the ping command.
- `Source IP`: Override the source IP address of the ping
  packet with this provided IP.
- `Ping Timeout`: Seconds to wait before declaring a ping timeout.
- `Ttl`: Time to Live parameter, which tells routers when to discard
  this packet because it has been in the network too long (too many
  hops).
- `VRF`: Ping a specific virtual routing and forwarding interface.
