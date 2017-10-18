from os import chmod
from socket import gethostname

from charms.slurm.helpers import MUNGE_SERVICE
from charms.slurm.helpers import MUNGE_KEY_PATH
from charms.slurm.helpers import SLURMD_SERVICE
from charms.slurm.helpers import SLURM_CONFIG_PATH
from charms.slurm.helpers import SLURMCTLD_SERVICE
from charms.slurm.helpers import create_spool_dir
from charms.slurm.helpers import render_munge_key
from charms.slurm.helpers import render_slurm_config

from charmhelpers.core.host import service_stop
from charmhelpers.core.host import service_pause
from charmhelpers.core.host import service_start
from charmhelpers.core.host import service_restart
from charmhelpers.core.host import service_running
from charmhelpers.core.hookenv import config
from charmhelpers.core.hookenv import status_set
from charmhelpers.core.hookenv import storage_get

from charms.reactive import hook
from charms.reactive import when
from charms.reactive import when_not
from charms.reactive import only_once
from charms.reactive import set_state
from charms.reactive import remove_state
from charms.reactive import when_file_changed


@only_once()
@when('slurm.installed')
def initial_setup():
    status_set('maintenance', 'Initial setup of slurm-node')
    # Disable slurmctld on node
    service_pause(SLURMCTLD_SERVICE)


@when_not('slurm-cluster.connected', 'slurm-cluster.available')
def missing_controller():
    status_set('blocked', 'Missing relation to slurm-controller')
    # Stop slurmd
    service_stop(SLURMD_SERVICE)
    remove_state('slurm-node.configured')
    remove_state('slurm-node.info.sent')


@when('slurm-cluster.connected')
@when_not('slurm-node.info.sent')
def send_node_info(cluster):
    cluster.send_node_info(hostname=gethostname(),
                           partition=config('partition'),
                           default=config('default'))
    set_state('slurm-node.info.sent')


@when('slurm-cluster.changed')
def cluster_has_changed(*args):
    set_state('slurm-node.changed')
    remove_state('slurm-node.configured')


@when('slurm-cluster.available')
@when_not('slurm-node.configured')
def configure_node(cluster):
    status_set('maintenance', 'Configuring slurm-node')
    # Get controller config
    controller_config = cluster.get_config()
    # Setup slurm dirs
    create_spool_dir(config=controller_config)
    # Render configs
    render_munge_key(config=controller_config)
    render_slurm_config(config=controller_config)
    # Make sure slurmd is running
    if not service_running(SLURMD_SERVICE):
        service_start(SLURMD_SERVICE)
    # Update states
    set_state('slurm-node.configured')


@when('slurm-cluster.available', 'slurm-node.configured')
def node_ready(cluster):
    status_set('active', 'Ready')


@hook('config-changed')
def config_changed():
    remove_state('slurm-node.configured')
    remove_state('slurm-node.info.sent')


@hook('scratch-storage-attached')
def setup_storage():
    storage = storage_get()
    chmod(path=storage.get('location'), mode=0o777)


@when_file_changed(SLURM_CONFIG_PATH)
def restart_on_slurm_change():
    service_restart(SLURMD_SERVICE)


@when_file_changed(MUNGE_KEY_PATH)
def restart_on_munge_change():
    service_restart(MUNGE_SERVICE)
