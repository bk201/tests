# Copyright (c) 2021 SUSE LLC
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact SUSE LLC.
#
# To contact SUSE about this file by physical or electronic mail,
# you may find current contact information at www.suse.com

import jinja2
import json
import math
import os
import polling2
import random
import string
import time
import uuid


def random_name():
    """Generate a random alphanumeric name using uuid.uuid4()"""
    return uuid.uuid4().hex


def random_alphanumeric(length=5, upper_case=False):
    """Generate a random alphanumeric string of given length

    :param length: the size of the string
    :param upper_case: whether to return the upper case string
    """
    if upper_case:
        return ''.join(random.choice(
            string.ascii_uppercase + string.digits) for _ in range(length))
    else:
        return ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(length))


def get_json_object_from_template(template_name, **template_args):
    """Load template from template file

    :param template_name: the name of the template. It is the filename of
                          template without the file extension. For example, if
                          you want to load './templates/foo.json.j2', then the
                          template_name should be 'foo'.
    :param template_args: dictionary of template argument values for the given
                          Jinja2 template
    """
    # get the current path relative to the ./templates/ directory
    my_path = os.path.dirname(os.path.realpath(__file__))
    # NOTE: the templates directory must be at the same level as
    # utilities.py, and all the templates must have the '.yaml.j2' extension
    templates_path = os.path.join(my_path, 'templates')
    template_file = f'{templates_path}/{template_name}.json.j2'
    # now load the template
    with open(template_file) as tempfile:
        template = jinja2.Template(tempfile.read())
    template.globals['random_name'] = random_name
    template.globals['random_alphanumeric'] = random_alphanumeric
    # now render the template
    rendered = template.render(template_args)
    return json.loads(rendered)


def poll_for_resource_ready(admin_session, endpoint, expected_code=200):
    ready = polling2.poll(
        lambda: admin_session.get(endpoint).status_code == expected_code,
        step=5,
        timeout=60)
    assert ready, 'Timed out while waiting for %s to yield %s' % (
        endpoint, expected_code)


def get_latest_resource_version(admin_session, lookup_endpoint):
    poll_for_resource_ready(admin_session, lookup_endpoint)
    resp = admin_session.get(lookup_endpoint)
    assert resp.status_code == 200, 'Failed to lookup resource: %s' % (
        resp.content)
    return resp.json()['metadata']['resourceVersion']


def poll_for_update_resource(admin_session, update_endpoint, request_json,
                             lookup_endpoint):

    resp = None

    def _update_resource():
        # we want the update response to return back to the caller
        nonlocal resp

        # first we need to get the latest resourceVersion and fill that in
        # the request_json as it is a required field and must be the latest.
        request_json['metadata']['resourceVersion'] = (
            get_latest_resource_version(admin_session, lookup_endpoint))
        resp = admin_session.put(update_endpoint, json=request_json)
        if resp.status_code == 409:
            return False
        else:
            assert resp.status_code == 200, 'Failed to update resource: %s' % (
                resp.content)
            return True

    # NOTE(gyee): we need to do retries because kubenetes cluster does not
    # guarantee freshness when updating resources because of the way it handles
    # queuing. See
    # https://github.com/kubernetes/kubernetes/issues/84430
    # Therefore, we must do fetch-retry when updating resources.
    # Apparently this is way of life in Kubernetes world.
    updated = polling2.poll(
        _update_resource,
        step=3,
        timeout=120)
    assert updated, 'Timed out while waiting to update resource: %s' % (
        update_endpoint)
    return resp


def lookup_vm_instance(admin_session, harvester_api_endpoints, vm_json):
    # NOTE(gyee): seem like the corresponding VM instance has the same name as
    # the VM. If this assumption is not true, we need to fix this code.
    resp = admin_session.get(harvester_api_endpoints.get_vm_instance % (
        vm_json['metadata']['name']))
    assert resp.status_code == 200, 'Failed to lookup VM instance %s' % (
        vm_json['metadata']['name'])
    return resp.json()


def lookup_hosts_with_most_available_cpu(admin_session,
                                         harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    nodes_json = resp.json()['data']
    most_available_cpu_nodes = None
    most_available_cpu = 0
    for node in nodes_json:
        # look up CPU usage for the given node
        resp = admin_session.get(harvester_api_endpoints.get_node_metrics % (
            node['metadata']['name']))
        assert resp.status_code == 200, (
            'Failed to lookup metrices for node %s: %s' % (
                node['metadata']['name'], resp.content))
        metrics_json = resp.json()
        # NOTE: Kubernets CPU metrics are expressed in nanocores, or
        # 1 billionth of a CPU. We need to convert it to a whole CPU core.
        cpu_usage = math.ceil(
            int(metrics_json['usage']['cpu'][:-1]) / 1000000000)
        available_cpu = int(node['status']['allocatable']['cpu']) - cpu_usage
        if available_cpu > most_available_cpu:
            most_available_cpu = available_cpu
            most_available_cpu_nodes = [node['metadata']['name']]
        elif available_cpu == most_available_cpu:
            most_available_cpu_nodes.append(node['metadata']['name'])
    return (most_available_cpu_nodes, most_available_cpu)


def lookup_hosts_with_most_available_memory(admin_session,
                                            harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    nodes_json = resp.json()['data']
    most_available_memory_nodes = None
    most_available_memory = 0
    for node in nodes_json:
        # look up CPU usage for the given node
        resp = admin_session.get(harvester_api_endpoints.get_node_metrics % (
            node['metadata']['name']))
        assert resp.status_code == 200, (
            'Failed to lookup metrices for node %s: %s' % (
                node['metadata']['name'], resp.content))
        metrics_json = resp.json()
        # NOTE: Kubernets memory metrics are expressed Kibibyte so convert it
        # back to Gigabytes
        memory_usage = math.ceil(
            int(metrics_json['usage']['memory'][:-2]) * 1.024e-06)
        # NOTE: we want the floor here so we don't over commit
        allocatable_memory = int(node['status']['allocatable']['memory'][:-2])
        allocatable_memory = math.floor(
            allocatable_memory * 1.024e-06)
        available_memory = allocatable_memory - memory_usage
        if available_memory > most_available_memory:
            most_available_memory = available_memory
            most_available_memory_nodes = [node['metadata']['name']]
        elif available_memory == most_available_memory:
            most_available_memory_nodes.append(node['metadata']['name'])
    return (most_available_memory_nodes, most_available_memory)


def lookup_hosts_with_cpu_and_memory(admin_session, harvester_api_endpoints,
                                     cpu, memory):
    """Lookup nodes that satisfies the given CPU and memory requirements"""
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    nodes_json = resp.json()['data']
    nodes = []
    for node in nodes_json:
        # look up CPU usage for the given node
        resp = admin_session.get(harvester_api_endpoints.get_node_metrics % (
            node['metadata']['name']))
        assert resp.status_code == 200, (
            'Failed to lookup metrices for node %s: %s' % (
                node['metadata']['name'], resp.content))
        metrics_json = resp.json()
        # NOTE: Kubernets CPU metrics are expressed in nanocores, or
        # 1 billionth of a CPU. We need to convert it to a whole CPU core.
        cpu_usage = math.ceil(
            int(metrics_json['usage']['cpu'][:-1]) / 1000000000)
        available_cpu = int(node['status']['allocatable']['cpu']) - cpu_usage
        # NOTE: Kubernets memory metrics are expressed Kibibyte so convert it
        # back to Gigabytes
        memory_usage = math.ceil(
            int(metrics_json['usage']['memory'][:-2]) * 1.024e-06)
        # NOTE: we want the floor here so we don't over commit
        allocatable_memory = int(node['status']['allocatable']['memory'][:-2])
        allocatable_memory = math.floor(
            allocatable_memory * 1.024e-06)
        available_memory = allocatable_memory - memory_usage
        if available_cpu >= cpu and available_memory >= memory:
            nodes.append(node['metadata']['name'])
    return nodes


def restart_vm(admin_session, harvester_api_endpoints, previous_uid, vm_name,
               wait_timeout):
    resp = admin_session.post(harvester_api_endpoints.restart_vm % (
        vm_name))
    assert resp.status_code == 204, 'Failed to restart VM instance %s: %s' % (
        vm_name, resp.content)
    assert_vm_restarted(admin_session, harvester_api_endpoints, previous_uid,
                        vm_name, wait_timeout)


def assert_vm_restarted(admin_session, harvester_api_endpoints,
                        previous_uid, vm_name, wait_timeout):
    # give it some time for the VM instance to restart
    time.sleep(120)

    def _check_vm_instance_restarted():
        resp = admin_session.get(
            harvester_api_endpoints.get_vm_instance % (vm_name))
        if resp.status_code == 200:
            resp_json = resp.json()
            if ('status' in resp_json and
                    'phase' in resp_json['status'] and
                    resp_json['status']['phase'] == 'Running' and
                    resp_json['metadata']['uid'] != previous_uid):
                return True
        return False

    success = polling2.poll(
        _check_vm_instance_restarted,
        step=5,
        timeout=wait_timeout)
    assert success, 'Failed to restart VM %s' % (vm_name)


def delete_image(request, admin_session, harvester_api_endpoints, image_json):
    resp = admin_session.delete(harvester_api_endpoints.delete_image % (
        image_json['metadata']['name']))
    assert resp.status_code in [200, 201], 'Unable to delete image %s: %s' % (
        image_json['metadata']['name'], resp.content)

    def _wait_for_image_to_be_deleted():
        resp = admin_session.get(harvester_api_endpoints.get_image % (
            image_json['metadata']['name']))
        if resp.status_code == 404:
            return True
        return False

    success = polling2.poll(
        _wait_for_image_to_be_deleted,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for image to be deleted'


def create_image(request, admin_session, harvester_api_endpoints, url,
                 name=None, description=''):
    request_json = get_json_object_from_template(
        'basic_image',
        name=name,
        description=description,
        url=url
    )
    resp = admin_session.post(harvester_api_endpoints.create_image,
                              json=request_json)
    assert resp.status_code in [200, 201], 'Failed to create image %s: %s' % (
        name, resp.content)
    image_json = resp.json()

    # wait for the image to get ready
    time.sleep(30)

    def _wait_for_image_become_active():
        # we want the update response to return back to the caller
        nonlocal image_json

        resp = admin_session.get(harvester_api_endpoints.get_image % (
            image_json['metadata']['name']))
        assert resp.status_code == 200, 'Failed to get image %s: %s' % (
            image_json['metadata']['name'], resp.content)
        image_json = resp.json()
        if ('status' in image_json and
                'storageClassName' in image_json['status']):
            return True
        return False

    success = polling2.poll(
        _wait_for_image_become_active,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for image to be active.'

    return image_json
