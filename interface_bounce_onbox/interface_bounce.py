from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import *
import argparse
from time import sleep

arguments = {
    "interface": "Name of the interface to disable/enable",
    "delay": "Time to wait before enabling the interface (seconds)",
}

def config_xml(interface_name, disable_attributes): 
    return """
        <configuration>
            <interfaces>
                <interface>
                    <name>{0}</name>
                    <disable {1}/>
                </interface>
            </interfaces>
        </configuration>
    """.format(interface_name, disable_attributes)

def change_config(dev, delta_config, log_message):
    print "%s: Locking the configuration" % log_message
    try:
        dev.cu.lock()
    except LockError:
        print "Error: Unable to lock configuration"
        return False

    print "%s: Loading configuration changes" % log_message
    try:
        dev.cu.load(delta_config, format="xml", merge=True)
    except ConfigLoadError as err:
        print "Unable to load configuration changes: \n" + err
        print "Unlocking the configuration"
        try:
            dev.cu.unlock()
        except UnlockError:
            print "Error: Unable to unlock configuration"
        return False
   
    print "%s: Committing the configuration" % log_message
    try:
        dev.cu.commit()
    except CommitError:
        print "Error: Unable to commit configuration"
        print "Unlocking the configuration"
        try:
            dev.cu.unlock()
        except UnlockError:
            print "Error: Unable to unlock configuration"
        return False
   
    print "%s: Unlocking the configuration" % log_message
    try:
        dev.cu.unlock()
    except UnlockError:
        print "Error: Unable to unlock configuration"
        return False

    return True


def main():
    parser = argparse.ArgumentParser()
    for key in arguments:
        parser.add_argument(('-' + key), required=True, help=arguments[key])

    args = parser.parse_args()

    with Device() as dev:
        dev.bind( cu=Config )
        if change_config(dev, config_xml(args.interface, ""), "Disabling interface"):
            print "Waiting %s seconds..." % args.delay
            sleep(float(args.delay))
            if change_config(dev, config_xml(args.interface, "delete='delete'"), "Enabling interface"):
                print "Interface bounce script finished successfully."
            else:
                print "Error enabling the interface, it will remain disabled."
    
if __name__ == "__main__":
    main()
