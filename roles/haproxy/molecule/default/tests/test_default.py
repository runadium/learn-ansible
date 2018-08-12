
import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

def test_haproxy_package_is_installed(host):
    package = host.package("haproxy")
    assert package.is_installed


def test_haproxy_service_is_started(host):
    service = host.service('haproxy')
    assert service.is_running
    assert service.is_enabled
