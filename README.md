# Check Cisco XR RPKI Server State
A monitoring plugin designed to validate the state of RPKI servers, total Route Origin Validation (ROV), and the delta between them.

To ensure consistency, it's recommended to run multiple and a diverse set of RPKI validators you have to ensure that they announce approximately the same number of ROVs, for example cases where a Trust Anchor Locator (TAL) might be missing. There might be always a slightly difference for example some validators reject >/24 ROAs.

This Plugin utilizes simple XR CLI scraping for its operations. While SNMP/Telemetry might be better options, XR CLI scraping is sufficiently accurate for checks 3-4 times a days.

Tested on XR 6.x to 7.x on Cisco ASR and NCS


## Example Outputs:

```
RPKI SERVER WARNING - 192.0.2.1 Server Down, 192.0.2.4 IPv4 ROAs out of range, 192.0.2.6 Server shutdown, 2/4 are online | '192.0.2.4_v4_roas'=15835;300000:500000;;; '192.0.2.4_v6_roas'=27103;60000:120000;;; '192.0.2.5_v4_roas'=157211;300000:500000;;; '192.0.2.5_v6_roas'=26517;60000:120000;;;
192.0.2.4 is Online 15835/27103 ROAs
192.0.2.5 is Online 157211/26517 ROAs
```

## Setup / Requirements

- pip install -r requirements.txt
- the SSH user needs permissions to run "show bgp rpki server summary"