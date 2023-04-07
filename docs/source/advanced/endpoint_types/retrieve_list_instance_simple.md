# Retrieve a List of Instances - Simple
Using a simple GET where filer criteria easily fit into the address, return
a list of instances that match criteria with set attributes.

**Method**: Get<br />
**Address**: /rest/query/`instance_type`?`parameter1`=`value1`&`parameter2`=`value2`...<br />
**Parameters**: None<br />
**Payload**: None<br />


### Example: Retrieve all devices
 
```/rest/query/device```

### Example: Retrieve all devices whose port is 22 and operating system EOS

```/rest/query/device?port=22&operating_system=eos```
    
