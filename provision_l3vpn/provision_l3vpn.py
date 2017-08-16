import jinja2
import os
import yaml
from pprint import pprint
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import *

USER = "lab"
PASSWD = "lab123"

def render(tpl_path, context):
    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)

with open("l3vpn-data.yaml") as var_file:
    l3vpn_data = yaml.load(var_file)

for PE in l3vpn_data["PEs"]:
    print("\n\nWorking on PE %s" % PE)
    z = {}
    z.update(l3vpn_data["PEs"][PE])
    z.update({"customers": l3vpn_data["customers"]})
    pprint(z)
    result_conf = render("l3vpn_config.jinja2", z)
    print(result_conf)

    try:
        with Device(host=l3vpn_data["PEs"][PE]["management_ip"], user=USER, password=PASSWD) as dev:
            # open and close is done automatically by context manager
            with Config(dev, mode="exclusive") as conf:
                # exclusive locks are treated automatically by context manager
                conf.load(result_conf, format="text")
                #print(STR_PDIFF_BANNER)
                conf.pdiff()
                conf.commit()
    except LockError:
        print("\n\nError applying config: configuration was locked!")
    except ConnectRefusedError:
        print("\n\nError: Device connection refused!")
    except ConnectTimeoutError:
        print("\n\nError: Device connection timed out!")
    except ConnectAuthError:
        print("\n\nError: Authentication failure!")
    except ConfigLoadError as ex:
        print("\n\nError: " + str(ex))
    else:
        print("Config applied successfully!")
