# Check Cisco XR RPKI Server State
A monitoring plugin designed to validate the state of RPKI servers (Established or Down) and check if the total of ROV's makes sense. 

For diversity it's recommended to run a different set of RPKI validators. With this plugin you can verify if all validators advertise a equal total of ROA's. Some validators behaves different, for example some reject >/24 ROAs. If there is a too big drift, it might indicate a problem e.g. a Trust Anchor Locator (TAL) might be missing. 

This Plugin utilizes simple XR CLI scraping for its operations. While Telemetry/SNMP(which oid?) might be better options, XR CLI scraping is sufficiently accurate for checks 3-4 times a days.

Tested on XR 6.x to 7.x on Cisco ASR and NCS


### Example Outputs:
```
RPKI SERVER WARNING - 192.0.2.1 Server Down, 192.0.2.4 IPv4 ROAs out of range, 192.0.2.6 Server shutdown, 2/4 are online | '192.0.2.4_v4_roas'=15835;300000:500000;;; '192.0.2.4_v6_roas'=27103;60000:120000;;; '192.0.2.5_v4_roas'=157211;300000:500000;;; '192.0.2.5_v6_roas'=26517;60000:120000;;;
192.0.2.4 is Online 15835/27103 ROAs
192.0.2.5 is Online 157211/26517 ROAs
```

![image](https://github.com/Bierchermuesli/check_cisco_xr_rpki_server/assets/13567009/ddbac41d-93b0-4f54-a81e-6aeb76207f20)


### Setup / Requirements

- pip install -r requirements.txt
- the SSH user needs permissions to run `show bgp rpki server summary` recommend to limit
- example icinga config:

```
object CheckCommand "check_cisco_xr_rpki_server" {
        import "ipv4-or-ipv6"
        command = [PluginGITS + "check_cisco_xr_rpki_server/check_cisco_xr_rpki_server.py" ]
        arguments = {
                "-H" = {
                        value = "$address$"
                        description = "host to check"
                }
                "--warning4" = {
                        value = "$warning4$"
                        description = "warning threshold"
                }
                "--warning6" = {
                        value = "$warning6$"
                        description = "critical threshold"
                }
                "--delta" = {
                        value = "$delta$"
                        description = "Debug Threshold"
                }
                "--password" = {
                        value = "$ssh_pass$"
                        description = "SSH Password"
                }
                "--user" = {
                        value = "$ssh_user$"
                        description = "SSH User"
                }


        }
// in case you want override the defaults here
  vars.warning4 = "300000:500000"
  vars.warning6 = "60000:120000"
  vars.delta = "0:1000"

}

...

apply Service "BGP RPKI Server"{
     import "generic-service"
     check_command = "check_cisco_xr_rpki_server"
     notes = "Show RPKI Servers"
     check_interval = 6h
     retry_interval = 30m
     vars.ssh_user = "read-only"
     vars.ssh_pass = "foobaz"

     # vars.warning4 = "300000:500000"
     # vars.warning6 = "60000:120000"
     # vars.delta = "0:1000"

     assign where host.vars.os == "IOS-XR" && "BGP" in host.groups
     assign where host.name == "edgy-edge.example.com"
 }
```

Questions? just let me know!
