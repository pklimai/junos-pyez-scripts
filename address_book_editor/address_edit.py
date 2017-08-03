from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import *
from ncclient.transport.errors import SSHError
from lxml import etree
import ipaddress

USER = "lab"
PASSWD = "lab123"
DEVICE_IP = "10.254.0.35"

ADDR_BOOK_NAME = "global"
ADDR_SET_NAME = "ALLOWED-IN"
ADDR_NAME_PREFIX = "CIDR-"

STR_INVITE = """
Address-set editor script for Juniper SRX. Device: {0}
Address book to edit: {1}   Address-set to edit: {2}
  r - READ and show addresses
  a - ADD address (IP or subnet)
  d - DELETE particular address
  q - QUIT script
Choice >>> """

STR_QUITING = "Goodbye!"
STR_READING = "\nReading and displaying address book entries:"
STR_UNKNOWN_INPUT = "Unknown input, please repeat."
STR_ENTER_IP_ADD = "Enter IP or IP/mask to add >>> "
STR_ADDRESS_ADDED = "Address added successfully."
STR_INVALID_IP = "Invalid entry, please repeat."
STR_ENTER_IP_DEL = "Enter IP/mask to delete >>> "
STR_ADDRESS_DELETED = "Address deleted successfully."
STR_PDIFF_BANNER = "\nConfig diff on the device:"
STR_CONFIG_CHANGED = "Configuration change committed."

STR_GET_CONFIG = """<configuration>
                        <security>
                            <address-book>
                                <name>{0}</name>
                            </address-book>
                        </security>
                    </configuration>"""

STR_SET_CONFIG = """set security address-book {0} address {1}{2} {2}
set security address-book global address-set ALLOWED-IN address {1}{2}"""

STR_DELETE_CONFIG = """delete security address-book {0} address {1}{2} {2}
delete security address-book global address-set ALLOWED-IN address {1}{2}"""

class InconsistentConfigException(Exception):
    pass


# All addresses in address set that start with prefix ADDR_NAME_PREFIX, must
# be of 'standard' form (prefix + cidr = cidr)
def read_addresses():
    addr_book_prefixes = set()       # empty sets so far
    address_set_prefixes = set()
    try:
        with Device(host=DEVICE_IP, user=USER, password=PASSWD) as dev:
            resp = dev.rpc.get_config(
                    filter_xml=etree.XML(STR_GET_CONFIG.format(ADDR_BOOK_NAME)),
                    options={'inherit': 'inherit', 'database': 'committed', 'format': 'XML'})
            if resp is not None:
                for address_element in resp.findall("security/address-book/address"):
                    name = address_element.findtext("name")
                    ip_prefix = address_element.findtext("ip-prefix")
                    if name is not None and ip_prefix is not None:
                        if name == ADDR_NAME_PREFIX + ip_prefix:
                            addr_book_prefixes.add(ip_prefix)
                        else:         # this entry was not added by script - ignore
                            pass

                for address_set_element in resp.findall("security/address-book/address-set[name='{0}']/address"
                                                                .format(ADDR_SET_NAME)):
                    ab_name = address_set_element.findtext("name")
                    if ab_name.startswith(ADDR_NAME_PREFIX):
                        test_ip = ab_name[len(ADDR_NAME_PREFIX):]
                        if test_ip in addr_book_prefixes:
                            address_set_prefixes.add(test_ip)
                        else:
                            raise InconsistentConfigException("Inconsistent entry in address book")
    except ConnectRefusedError:
        print("\n\nError: device connection refused!")
    # except SSHError:
    #     print("Error: device connection refused!")
    return address_set_prefixes


def display_addresses(addrs):
    for addr in sorted(addrs):
        print(addr)


def sanitize_ip(address_entered):
    result = address_entered
    if "/" not in result: result += "/32"
    try:
        ip = ipaddress.IPv4Network(result)
    except:
        return None
    return result


def change_config_with_set_commands(set_commands):
    try:
        with Device(host=DEVICE_IP, user=USER, password=PASSWD) as dev:
            # open and close is done automatically by context manager
            with Config(dev, mode="exclusive") as conf:
                # exclusive locks are treated automatically by context manager
                conf.load(set_commands, format="set")
                print(STR_PDIFF_BANNER)
                conf.pdiff()
                conf.commit()
    except LockError:
        print("\n\nError deleting address: configuration was locked!")
    except ConnectRefusedError:
        print("\n\nError: device connection refused!")
    else:
        print(STR_CONFIG_CHANGED)

def add_address(address_sanitized):
    change_config_with_set_commands(STR_SET_CONFIG.format(
                ADDR_BOOK_NAME, ADDR_NAME_PREFIX, address_sanitized))


def del_address(address_sanitized):
    change_config_with_set_commands(STR_DELETE_CONFIG.format(
        ADDR_BOOK_NAME, ADDR_NAME_PREFIX, address_sanitized))


def main():
    while True:
        print(STR_INVITE.format(DEVICE_IP, ADDR_BOOK_NAME, ADDR_SET_NAME), end="")
        choice = input().lower()
        if choice == "q":
            print(STR_QUITING)
            break
        elif choice == "r":
            print(STR_READING)
            addrs = read_addresses()
            display_addresses(addrs)
        elif choice == "a":
            print(STR_ENTER_IP_ADD, end="")
            address_entered = input()
            address_sanitized = sanitize_ip(address_entered)
            if address_sanitized is None:
                print(STR_INVALID_IP)
            else:
                add_address(address_sanitized)
        elif choice == "d":
            print(STR_ENTER_IP_DEL, end="")
            address_entered = input()
            address_sanitized = sanitize_ip(address_entered)
            if address_sanitized is None:
                print(STR_INVALID_IP)
            else:
                del_address(address_sanitized)
        else:
            print(STR_UNKNOWN_INPUT)

if __name__ == "__main__":
    main()
