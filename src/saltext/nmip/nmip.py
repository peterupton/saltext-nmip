"""
Salt execution module
this module configures network interfaces using NetworkManager
"""

import configparser
import ctypes
import logging
import os
import stat
import subprocess

log = logging.getLogger(__name__)

__virtualname__ = "nmip"

def __virtual__():
    """
    helper for configuring host with Network Manager
    """
    return __virtualname__


def define_connection(properties):
    """
    Defines a NetworkManagerconnection given a dictionary where top-level keys are groups
    and second-level keys are keys in the nmconnection file
    for example {'connection': {'id': 'test'}} results in the following:

    [connection]
    id=test

    or in nmcli syntax: 

    "connection.id test"


    CLI Example::

        salt '*' nmip.define_connection {'connection': {'id': 'main', 'type: 'ethernet'}, 'ipv4': {'address1': '192.168.1.90/24', 'dns': '8.8.8.8', 'method': 'manual}}
    """

    # define a filename from the connection id
    if 'connection' not in properties.keys() or 'id' not in properties['connection'].keys():
        return {
                'retcode': 2,
                'comment': 'connection.id is required'
                }
    filename = f"/etc/NetworkManager/system-connections/{properties['connection']['id']}.nmconnection"
    with open(filename, 'w') as connectionfile:
        configparser.read_dict(properties).write(connectionfile)
    # (re)load the connection file
    os.chmod(filename, stat.S_IRUSR | stat.S_IWUSR)
    os.chown(filename, 0, 0)
    try:
        comp = subprocess.run(['nmcli', 'connection', 'load', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        comp.check_returncode()
    except subprocess.CalledProcessError as e:
        return {"retcode": e.returncode, "comment": f"connection {properties['id']} failed loading"}
    if "Could not load file" in comp.stderr.decode():
        return {"retcode": 1, "comment": f"connection {properties['id']} failed, likely due to invalid connection properties"}

    return {"retcode": 0, "comment": f"connection {properties['id']} defined"}


def down_connection(connection_id):
    """
    down a connection
    """
    subprocess.run(['nmcli', 'connection', 'down', connection_id], check=True)
    return {"retcode": 0, "comment": f"{connection_id} down"}

def up_connection(connection_id):
    """
    up a connection
    """
    try:
        comp = subprocess.run(['nmcli', 'connection', 'up', connection_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        comp.check_returncode()
    except subprocess.CalledProcessError as e:
        return {"retcode": e.returncode, "comment": f"connection {connection_id} failed to start, stderr: {comp.stderr.decode()}"}
    return {"retcode": 0, "comment": f"{connection_id} up"}

def delete_connection(connection_id):
    """
    delete a connection
    """

    subprocess.run(['nmcli', 'connection', 'delete', connection_id], check=True)
    return {"retcode": 0, "comment": f"{connection_id} deleted"}

def configure_connection(properties):
    """
    define and configure a connection
    """
    define_connection(properties)
    up_connection(properties['id'])
    return {"retcode": 0, "comment": f"{properties['id']} configured"}

