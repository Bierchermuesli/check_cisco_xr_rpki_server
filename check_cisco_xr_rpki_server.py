#!/usr/bin/python3
"""A monitoring plugin designed to validate the state of RPKI servers, total Route Origin Validation (ROV), and the delta between them.

2020-09-01 Stefan Grosser - initial release
2024-03-12 Stefan Grosser - some brush up and public release
"""

from nagplug import Plugin, OK, WARNING, CRITICAL, UNKNOWN
from nagplug import Threshold
from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, AuthenticationException, SSHException
import os


def main():
    # New Instance
    check = Plugin(version="1.0", name="RPKI Server")
    check.add_arg("-u", "--user", metavar="USER", help="SSH User")
    check.add_arg("-p", "--password", metavar="PASS", help="SSH Password")
    check.add_arg("--debug", action="store_true", help="Show Debug output")
    check.add_arg("-d", "--delta", metavar="THRESHOLD", type=Threshold, help="Warning Threshold for Deltas", default="0:1000")
    check.add_arg("-4", "--warning4", metavar="THRESHOLD", type=Threshold, help="Warning Threshold for IPv4 ROAs", default="300000:500000")
    check.add_arg("-6", "--warning6", metavar="THRESHOLD", type=Threshold, help="Warning Threshold for IPv6 ROAs", default="60000:120000")
    check.parse_args()
    check.set_timeout()

    server_ok = []
    all_servers = []
    roasum_v4 = []
    roasum_v6 = []

    ##########################
    # Load textfsm template
    template = os.path.dirname(os.path.realpath(__file__)) + "/ntc-templates/cisco_xr_show_bgp_rpki_server_summary.textfsm"
    try:
        open(template)
    except Exception as e:
        check.add_result(UNKNOWN, f"Template {template} not found {e}")
        check.finish()

    # get the data
    try:
        cisco_xr = {
            "device_type": "cisco_xr",
            "host": check.args.hostname.strip(),
            "username": check.args.user.strip(),
            "password": check.args.password.strip(),
        }
        net_connect_cisco_xr = ConnectHandler(**cisco_xr)
        net_connect_cisco_xr.find_prompt()
        all_servers = net_connect_cisco_xr.send_command("show bgp rpki server summary", use_textfsm=True, textfsm_template=template)

    except (NetMikoTimeoutException, AuthenticationException, SSHException, Exception) as e:
        check.add_result(UNKNOWN, str(e))
        check.finish()

    ##########################
    # Bailing Out
    if len(all_servers) > 0:
        for s in all_servers:
            # lower all keys
            s = {k.lower(): v for k, v in s.items()}

            # convert to int if any
            for key in ["roav4", "roav6"]:
                if s.get(key):
                    s[key] = int(s[key])
                else:
                    s.pop(key, None)

            if check.args.debug:
                print(80 * "-")
                print(s)

            if s["state"] == "ESTAB":
                check.add_perfdata(f"{s['server']}_v4_roas", s["roav4"], warning=check.args.warning4)
                check.add_perfdata(f"{s['server']}_v6_roas", s["roav6"], warning=check.args.warning6)
                check.add_extdata(f"{s['server']} is Online {s['roav4']}/{s['roav6']} ROAs")
                server_ok.append(s["server"])

                # #minimum IPv4 ROAs
                # if s['roav4'] < check.args.min4:
                if check.check_threshold(s["roav4"], warning=check.args.warning4):
                    check.add_result(WARNING, f"{s['server']} IPv4 ROAs out of range")

                # #minimum IPv6 ROAs
                # if s['roav6'] < check.args.min6:
                if check.check_threshold(s["roav6"], warning=check.args.warning6):
                    check.add_result(WARNING, f"{s['server']} IPv6 ROAs out of range")

                roasum_v4.append(s["roav4"])
                roasum_v6.append(s["roav6"])

            elif s["state"] == "CONNECT":
                check.add_result(WARNING, f"{s['server']} Server Down")
                # drop this server from the list for further checks
                del s
            elif s["state"] == "NONE":
                check.add_result(WARNING, f"{s['server']} Server shutdown")
                # drop this server from the list for further checks
                del s
            else:
                check.add_result(UNKNOWN, s["server"] + " is " + s["state"])
                # drop this server from the list for further checks
                del s

        if check.args.debug:
            print(f"ROAv4 {roasum_v4}")
            print(f"ROAv6 {roasum_v6}")

    else:
        check.add_result(CRITICAL, "no RPKI Peers found")

    if len(server_ok) == 0:
        """Critical State if none is online"""
        check.add_result(CRITICAL, "no RPKI Peer connected")

    elif len(server_ok) == len(all_servers):
        """OK State if all onle plus we compare the delta"""
        check.add_result(OK, f"{len(all_servers)} Servers are Online")

        # Check maximum delta over all servers
        delta_v4 = max(abs(x - y) for (x, y) in zip(roasum_v4[1:], roasum_v4[:-1]))
        delta_v6 = max(abs(x - y) for (x, y) in zip(roasum_v6[1:], roasum_v6[:-1]))
        check.add_extdata(f"ROA v4 delta: {delta_v4}")
        check.add_extdata(f"ROA v6 delta: {delta_v6}")
        check.add_perfdata("v4_roas_delta", delta_v4, minimum=0, warning=check.args.delta)
        check.add_perfdata("v6_roas_delta", delta_v6, minimum=0, warning=check.args.delta)

        # if delta_v4 > check.args.delta:
        if check.check_threshold(delta_v4, warning=check.args.delta):
            check.add_result(WARNING, f"ROAv4 delta between all Servers: {delta_v4}")
        # if delta_v6 > check.args.delta:
        if check.check_threshold(delta_v6, warning=check.args.delta):
            check.add_result(WARNING, f"ROAv6 delta between all Servers: {delta_v6}")
    else:
        """Otherwise warning - but at at least more than one is online"""
        check.add_result(WARNING, str(len(server_ok)) + "/" + str(len(all_servers)) + " are online")

    # cleanup and exit
    check.finish()


if __name__ == "__main__":
    main()
