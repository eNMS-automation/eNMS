Uses Napalm to connect to the selected target devices and performs a
traceroute to another designated target.

![Napalm Traceroute Service](../../_static/automation/service_types/napalm_traceroute.png)

Configuration parameters for creating this service instance:

- All [Napalm Service Common Parameters](napalm_common.md). 
- `Destination IP`: The IP address of the device to which to send the echo packet.
- `Source IP address`: Override the source IP address of the ping
  packet with this provided IP.
- `Timeout`: Seconds to wait before declaring timeout.
- `ttl`: Time to Live parameter, which tells routers when to discard
  this packet because it has been in the network too long (too many
  hops).
- `vrf`: Ping a specific virtual routing and forwarding interface.
