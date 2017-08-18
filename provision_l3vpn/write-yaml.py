#!/usr/bin/python3

# This script writes a YAML file with N Customer VRFs
# Use for stress testing the deployment script.

N = 1000

with open("l3vpn-data-SCALED.yaml", "w") as f:

    f.write(
"""---
customers:""")

    for i in range(N):
        f.write("""
  Cust_{0}:
    vrf_target: "target:65000:{0}"
    AS: 65{0}""".format(str(i)))

    f.write("""
PEs:
  PE1:
    management_ip: "10.254.0.41"
    VPN_data:""")

    for i in range(N):
        f.write("""
      - customer_id: Cust_{0}
        interface_name: ge-0/0/2
        unit: 1{0}
        vlan_id: 1{0}
        ip_mask: 10.100.0.1/24
        customer_ip: 10.100.0.2
        prefix_limit: 10""".format(str(i)))

