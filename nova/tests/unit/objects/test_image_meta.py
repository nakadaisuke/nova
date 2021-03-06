# Copyright 2014 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import datetime

from nova import exception
from nova import objects
from nova import test


class TestImageMeta(test.NoDBTestCase):
    def test_basic_attrs(self):
        image = {'status': 'active',
                 'container_format': 'bare',
                 'min_ram': 0,
                 'updated_at': '2014-12-12T11:16:36.000000',
                 # Testing string -> int conversion
                 'min_disk': '0',
                 'owner': '2d8b9502858c406ebee60f0849486222',
                 # Testing string -> bool conversion
                 'protected': 'yes',
                 'properties': {
                     'os_type': 'Linux',
                     'hw_video_model': 'vga',
                     'hw_video_ram': '512',
                     'hw_qemu_guest_agent': 'yes',
                     'hw_scsi_model': 'virtio-scsi',
                 },
                 'size': 213581824,
                 'name': 'f16-x86_64-openstack-sda',
                 'checksum': '755122332caeb9f661d5c978adb8b45f',
                 'created_at': '2014-12-10T16:23:14.000000',
                 'disk_format': 'qcow2',
                 'id': 'c8b1790e-a07d-4971-b137-44f2432936cd'
        }
        image_meta = objects.ImageMeta.from_dict(image)

        self.assertEqual('active', image_meta.status)
        self.assertEqual('bare', image_meta.container_format)
        self.assertEqual(0, image_meta.min_ram)
        self.assertIsInstance(image_meta.updated_at, datetime.datetime)
        self.assertEqual(0, image_meta.min_disk)
        self.assertEqual('2d8b9502858c406ebee60f0849486222', image_meta.owner)
        self.assertTrue(image_meta.protected)
        self.assertEqual(213581824, image_meta.size)
        self.assertEqual('f16-x86_64-openstack-sda', image_meta.name)
        self.assertEqual('755122332caeb9f661d5c978adb8b45f',
                         image_meta.checksum)
        self.assertIsInstance(image_meta.created_at, datetime.datetime)
        self.assertEqual('qcow2', image_meta.disk_format)
        self.assertEqual('c8b1790e-a07d-4971-b137-44f2432936cd', image_meta.id)

        self.assertIsInstance(image_meta.properties, objects.ImageMetaProps)

    def test_no_props(self):
        image_meta = objects.ImageMeta.from_dict({})

        self.assertIsInstance(image_meta.properties, objects.ImageMetaProps)

    def test_volume_backed_image(self):
        image = {'container_format': None,
                 'size': 0,
                 'checksum': None,
                 'disk_format': None,
        }
        image_meta = objects.ImageMeta.from_dict(image)

        self.assertEqual('', image_meta.container_format)
        self.assertEqual(0, image_meta.size)
        self.assertEqual('', image_meta.checksum)
        self.assertEqual('', image_meta.disk_format)

    def test_null_substitution(self):
        image = {'name': None,
                 'checksum': None,
                 'owner': None,
                 'size': None,
                 'virtual_size': None,
                 'container_format': None,
                 'disk_format': None,
        }
        image_meta = objects.ImageMeta.from_dict(image)

        self.assertEqual('', image_meta.name)
        self.assertEqual('', image_meta.checksum)
        self.assertEqual('', image_meta.owner)
        self.assertEqual(0, image_meta.size)
        self.assertEqual(0, image_meta.virtual_size)
        self.assertEqual('', image_meta.container_format)
        self.assertEqual('', image_meta.disk_format)


class TestImageMetaProps(test.NoDBTestCase):
    def test_normal_props(self):
        props = {'os_type': 'windows',
                 'hw_video_model': 'vga',
                 'hw_video_ram': '512',
                 'hw_qemu_guest_agent': 'yes',
                 # Fill sane values for the rest here
                 }
        virtprops = objects.ImageMetaProps.from_dict(props)
        self.assertEqual('windows', virtprops.os_type)
        self.assertEqual('vga', virtprops.hw_video_model)
        self.assertEqual(512, virtprops.hw_video_ram)
        self.assertTrue(virtprops.hw_qemu_guest_agent)

    def test_default_props(self):
        props = {}
        virtprops = objects.ImageMetaProps.from_dict(props)

        for prop in virtprops.fields:
            self.assertIsNone(virtprops.get(prop))

    def test_default_prop_value(self):
        props = {}
        virtprops = objects.ImageMetaProps.from_dict(props)

        self.assertEqual("hvm", virtprops.get("hw_vm_mode", "hvm"))

    def test_non_existent_prop(self):
        props = {}
        virtprops = objects.ImageMetaProps.from_dict(props)

        self.assertRaises(AttributeError,
                          virtprops.get,
                          "doesnotexist")

    def test_legacy_compat(self):
        legacy_props = {
            'architecture': 'x86_64',
            'owner_id': '123',
            'vmware_adaptertype': 'lsiLogic',
            'vmware_disktype': 'preallocated',
            'vmware_image_version': '2',
            'vmware_ostype': 'rhel3_64Guest',
            'auto_disk_config': 'yes',
            'ipxe_boot': 'yes',
            'xenapi_device_id': '3',
            'xenapi_image_compression_level': '2',
            'vmware_linked_clone': 'false',
            'xenapi_use_agent': 'yes',
            'xenapi_skip_agent_inject_ssh': 'no',
            'xenapi_skip_agent_inject_files_at_boot': 'no',
            'cache_in_nova': 'yes',
            'vm_mode': 'hvm',
            'bittorrent': 'yes',
            'mappings': [],
            'block_device_mapping': [],
            'bdm_v2': 'yes',
            'root_device_name': '/dev/vda',
            'hypervisor_version_requires': '>=1.5.3',
            'hypervisor_type': 'qemu',
        }

        image_meta = objects.ImageMetaProps.from_dict(legacy_props)

        self.assertEqual('x86_64', image_meta.hw_architecture)
        self.assertEqual('123', image_meta.img_owner_id)
        self.assertEqual('lsilogic', image_meta.hw_scsi_model)
        self.assertEqual('preallocated', image_meta.hw_disk_type)
        self.assertEqual(2, image_meta.img_version)
        self.assertEqual('rhel3_64Guest', image_meta.os_distro)
        self.assertTrue(image_meta.hw_auto_disk_config)
        self.assertTrue(image_meta.hw_ipxe_boot)
        self.assertEqual(3, image_meta.hw_device_id)
        self.assertEqual(2, image_meta.img_compression_level)
        self.assertFalse(image_meta.img_linked_clone)
        self.assertTrue(image_meta.img_use_agent)
        self.assertFalse(image_meta.os_skip_agent_inject_ssh)
        self.assertFalse(image_meta.os_skip_agent_inject_files_at_boot)
        self.assertTrue(image_meta.img_cache_in_nova)
        self.assertTrue(image_meta.img_bittorrent)
        self.assertEqual([], image_meta.img_mappings)
        self.assertEqual([], image_meta.img_block_device_mapping)
        self.assertTrue(image_meta.img_bdm_v2)
        self.assertEqual("/dev/vda", image_meta.img_root_device_name)
        self.assertEqual('>=1.5.3', image_meta.img_hv_requested_version)
        self.assertEqual('qemu', image_meta.img_hv_type)

    def test_legacy_compat_vmware_adapter_types(self):
        legacy_types = ['lsiLogic', 'busLogic', 'ide', 'lsiLogicsas',
                        'paraVirtual', None, '']

        for legacy_type in legacy_types:
            legacy_props = {
                'vmware_adaptertype': legacy_type,
            }

            image_meta = objects.ImageMetaProps.from_dict(legacy_props)
            if legacy_type == 'ide':
                self.assertEqual('ide', image_meta.hw_disk_bus)
            elif not legacy_type:
                self.assertFalse(image_meta.obj_attr_is_set('hw_disk_bus'))
                self.assertFalse(image_meta.obj_attr_is_set('hw_scsi_model'))
            else:
                self.assertEqual('scsi', image_meta.hw_disk_bus)
                if legacy_type == 'lsiLogicsas':
                    expected = 'lsisas1068'
                elif legacy_type == 'paraVirtual':
                    expected = 'vmpvscsi'
                else:
                    expected = legacy_type.lower()
                self.assertEqual(expected, image_meta.hw_scsi_model)

    def test_duplicate_legacy_and_normal_props(self):
        # Both keys are referring to the same object field
        props = {'hw_scsi_model': 'virtio-scsi',
                 'vmware_adaptertype': 'lsiLogic',
                 }
        virtprops = objects.ImageMetaProps.from_dict(props)
        # The normal property always wins vs. the legacy field since
        # _set_attr_from_current_names is called finally
        self.assertEqual('virtio-scsi', virtprops.hw_scsi_model)

    def test_get(self):
        props = objects.ImageMetaProps(os_distro='linux')
        self.assertEqual('linux', props.get('os_distro'))
        self.assertIsNone(props.get('img_version'))
        self.assertEqual(1, props.get('img_version', 1))

    def test_set_numa_mem(self):
        props = {'hw_numa_nodes': 2,
                 'hw_numa_mem.0': "2048",
                 'hw_numa_mem.1': "4096"}
        virtprops = objects.ImageMetaProps.from_dict(props)
        self.assertEqual(2, virtprops.hw_numa_nodes)
        self.assertEqual([2048, 4096], virtprops.hw_numa_mem)

    def test_set_numa_mem_sparse(self):
        props = {'hw_numa_nodes': 2,
                 'hw_numa_mem.0': "2048",
                 'hw_numa_mem.1': "1024",
                 'hw_numa_mem.3': "4096"}
        virtprops = objects.ImageMetaProps.from_dict(props)
        self.assertEqual(2, virtprops.hw_numa_nodes)
        self.assertEqual([2048, 1024], virtprops.hw_numa_mem)

    def test_set_numa_mem_no_count(self):
        props = {'hw_numa_mem.0': "2048",
                 'hw_numa_mem.3': "4096"}
        virtprops = objects.ImageMetaProps.from_dict(props)
        self.assertIsNone(virtprops.get("hw_numa_nodes"))
        self.assertEqual([2048], virtprops.hw_numa_mem)

    def test_set_numa_cpus(self):
        props = {'hw_numa_nodes': 2,
                 'hw_numa_cpus.0': "0-3",
                 'hw_numa_cpus.1': "4-7"}
        virtprops = objects.ImageMetaProps.from_dict(props)
        self.assertEqual(2, virtprops.hw_numa_nodes)
        self.assertEqual([set([0, 1, 2, 3]), set([4, 5, 6, 7])],
                         virtprops.hw_numa_cpus)

    def test_set_numa_cpus_sparse(self):
        props = {'hw_numa_nodes': 4,
                 'hw_numa_cpus.0': "0-3",
                 'hw_numa_cpus.1': "4,5",
                 'hw_numa_cpus.3': "6-7"}
        virtprops = objects.ImageMetaProps.from_dict(props)
        self.assertEqual(4, virtprops.hw_numa_nodes)
        self.assertEqual([set([0, 1, 2, 3]), set([4, 5])],
                         virtprops.hw_numa_cpus)

    def test_set_numa_cpus_no_count(self):
        props = {'hw_numa_cpus.0': "0-3",
                 'hw_numa_cpus.3': "4-7"}
        virtprops = objects.ImageMetaProps.from_dict(props)
        self.assertIsNone(virtprops.get("hw_numa_nodes"))
        self.assertEqual([set([0, 1, 2, 3])],
                         virtprops.hw_numa_cpus)

    def test_obj_make_compatible(self):
        props = {
            'img_config_drive': 'mandatory',
            'os_admin_user': 'root',
            'hw_vif_multiqueue_enabled': True,
            'img_hv_type': 'kvm',
            'img_hv_requested_version': '>= 1.0',
            'os_require_quiesce': True,
        }

        obj = objects.ImageMetaProps(**props)
        primitive = obj.obj_to_primitive('1.0')
        self.assertFalse(any([x in primitive['nova_object.data']
                              for x in props]))

        for bus in ('lxc', 'uml'):
            obj.hw_disk_bus = bus
            self.assertRaises(exception.ObjectActionError,
                              obj.obj_to_primitive, '1.0')
