# import os

# import pytest
# from juju.model import Model


# @pytest.mark.asyncio
# async def test_deploy():
#     # Get build variables
#     CHARM_CTRL_NAME = 'slurm-controller'
#     CHARM_CTRL_URL = 'cs:~{}/{}'.format(
#         os.environ.get('CHARM_STORE_GROUP'), CHARM_CTRL_NAME)
#     CHARM_NODE_NAME = os.environ.get('CHARM_NAME')
#     CHARM_NODE_URL = os.path.join(
#         os.environ.get('CHARM_BUILD_DIR'), CHARM_NODE_NAME)
#     CHARM_INTERFACE_NAME = 'slurm-cluster'

#     model = Model()
#     print('Connecting to model')
#     await model.connect_current()
#     print('Resetting model')
#     await model.reset(force=True)

#     try:
#         # Deploy controller from local
#         print('Deploying {} from {}'.format(CHARM_CTRL_NAME, CHARM_CTRL_URL))
#         ctrl = await model.deploy(entity_url=CHARM_CTRL_URL,
#                                   application_name=CHARM_CTRL_NAME)

#         # Deploy node from store
#         print('Deploying {} from {}'.format(CHARM_NODE_NAME, CHARM_NODE_URL))
#         node = await model.deploy(entity_url=CHARM_NODE_URL,
#                                   application_name=CHARM_NODE_NAME)

#         print('Waiting for blocked')
#         await model.block_until(
#             lambda: all(unit.workload_status == 'blocked'
#                         for unit in ctrl.units))

#         rel = await ctrl.add_relation(local_relation=CHARM_INTERFACE_NAME,
#                                       remote_relation='{}:{}'
#                                       .format(CHARM_NODE_NAME,
#                                               CHARM_INTERFACE_NAME))

#         print('Waiting for active')
#         await model.block_until(
#             lambda: all(unit.workload_status == 'active'
#                         for unit in ctrl.units))

#     finally:
#         print('Disconnecting from model')
#         await model.disconnect()


# #!/usr/bin/env python

# import os
# import unittest
# import amulet

# # Now you can use self.d.sentry[SERVICE][UNIT] to address each of the units
# # and perform more in-depth steps.
# # Each self.d.sentry[SERVICE][UNIT] has the following methods:
# # - .info - An array of the information of that unit from Juju
# # - .file(PATH) - Get the details of a file on that unit
# # - .file_contents(PATH) - Get plain text output of PATH file from that unit
# # - .directory(PATH) - Get details of directory
# # - .directory_contents(PATH) - List files and folders in PATH on that unit
# # - .relation(relation, service:rel) - Get relation data from return service


# class TestCharm(unittest.TestCase):

#     @classmethod
#     def setUpClass(cls):
#         """Set up deployment.

#         This will be called only once during the Test class.
#         """
#         # Get env variables
#         cls.charm_name = os.environ.get('CHARM_NAME')
#         cls.charm_store_group = os.environ.get('CHARM_STORE_GROUP')
#         cls.charm_build_dir = os.environ.get('CHARM_BUILD_DIR')

#         # Generate paths to locally built charms
#         cls.charm_path = os.path.join(cls.charm_build_dir, cls.charm_name)

#         # Setup Amulet deployment
#         cls.d = amulet.Deployment(series='xenial')

#         # Add services
#         cls.d.add(service_name=cls.charm_name, charm=cls.charm_path)
#         cls.d.add(service_name='slurm-node',
#                   charm='cs:~{}/slurm-node'.format(cls.charm_store_group))

#         # # Add relations
#         cls.d.relate('{}:slurm-cluster'.format(cls.charm_name),
#                      'slurm-node:slurm-cluster')

#         # Deploy services
#         cls.d.setup()
#         cls.d.sentry.wait()

#         # Get Slurm controller
#         cls.controller = cls.d.sentry[cls.charm_name][0]

#     def setUp(self):
#         """This will be called before each test method."""
#         pass

#     def test_10_slurm_run(self):
#         self.d.configure(self.charm_name, {
#             'slurmd_debug': 'debug',
#         })
#         self.d.sentry.wait()

#     def test_20_scale_up(self):
#         self.d.add_unit('slurm-node')
#         self.d.sentry.wait()
#         self._run_slurm_srun_checks()

#     def test_30_unrelate(self):
#         self.d.unrelate('{}:slurm-cluster'.format(self.charm_name),
#                         'slurm-node:slurm-cluster')

#         self.d.sentry.wait()

#         self.d.relate('{}:slurm-cluster'.format(self.charm_name),
#                       'slurm-node:slurm-cluster')

#         self.d.sentry.wait_for_messages({'slurm-controller': 'Ready'})
#         self.d.sentry.wait_for_messages({'slurm-node': 'Ready'})

#         self._run_slurm_srun_checks()

#     def test_40_scale_down(self):
#         last_node = self.d.sentry['slurm-node'][-1]
#         self.d.remove_unit(last_node.info['unit_name'])
#         self.d.sentry.wait()
#         self._run_slurm_srun_checks()

#     def _run_slurm_srun_checks(self):
#         for node in self.d.sentry['slurm-node']:
#             node_hostname = node.relation(
#                 'slurm-cluster',
#                 'slurm-controller:slurm-cluster')['hostname']
#             output, exit_code = self.controller.run(
#                 'srun --nodelist={} hostname'.format(node_hostname))
#             self.assertEqual(exit_code, 0)
#             self.assertEqual(node_hostname, output)


# if __name__ == '__main__':
#     unittest.main(verbosity=2)
