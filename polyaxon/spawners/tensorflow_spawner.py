# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import logging

from polyaxon_schemas.environments import TensorflowClusterConfig
from polyaxon_schemas.polyaxonfile.specification.frameworks import TensorflowSpecification
from polyaxon_schemas.utils import TaskType

from experiments.paths import get_experiment_outputs_path
from spawners.experiment_spawner import ExperimentSpawner
from spawners.templates.config_maps import get_env_var

logger = logging.getLogger('polyaxon.spawners.tensorflow')


class TensorflowSpawner(ExperimentSpawner):

    def get_env_vars(self, task_type, task_idx):
        tf_config = {
            'cluster': self.get_cluster(),
            'task': {'type': task_type, 'index': task_idx},
            'model_dir': get_experiment_outputs_path(self.experiment_name),
            'environment': 'cloud'
        }
        return get_env_var('TF_CONFIG', tf_config)

    def create_workers(self):
        n_pods = self.spec.cluster_def[0].get(TaskType.WORKER, 0)

        cluster, is_distributed, = self.spec.cluster_def
        resources = TensorflowSpecification.get_worker_resources(
            environment=self.spec.environment,
            cluster=cluster,
            is_distributed=is_distributed
        )
        env_vars = self._get_multi_env_vars(task_type=TaskType.WORKER, n_pods=n_pods)
        return self._create_multi_pods(task_type=TaskType.WORKER,
                                       resources=resources,
                                       env_vars=env_vars,
                                       n_pods=n_pods)

    def delete_workers(self):
        n_pods = self.spec.cluster_def[0].get(TaskType.WORKER, 0)
        self._delete_multi_pods(task_type=TaskType.WORKER, n_pods=n_pods)

    def create_servers(self):
        n_pods = self.spec.cluster_def[0].get(TaskType.PS, 0)
        cluster, is_distributed, = self.spec.cluster_def
        resources = TensorflowSpecification.get_ps_resources(
            environment=self.spec.environment,
            cluster=cluster,
            is_distributed=is_distributed
        )
        env_vars = self._get_multi_env_vars(task_type=TaskType.PS, n_pods=n_pods)
        return self._create_multi_pods(task_type=TaskType.PS,
                                       resources=resources,
                                       env_vars=env_vars,
                                       n_pods=n_pods)

    def delete_servers(self):
        n_pods = self.spec.cluster_def[0].get(TaskType.PS, 0)
        self._delete_multi_pods(task_type=TaskType.PS, n_pods=n_pods)

    def start_experiment(self, user_token=None):
        experiment = super(TensorflowSpawner, self).start_experiment(user_token=user_token)
        experiment[TaskType.WORKER] = self.create_workers()
        experiment[TaskType.PS] = self.create_servers()
        return experiment

    def stop_experiment(self):
        super(TensorflowSpawner, self).stop_experiment()
        self.delete_workers()
        self.delete_servers()

    def get_cluster(self):
        cluster_def, is_distributed = self.spec.cluster_def

        job_name = self.pod_manager.get_job_name(task_type=TaskType.MASTER, task_idx=0)
        cluster_config = {
            TaskType.MASTER: [self._get_pod_address(job_name)]
        }

        workers = []
        for i in range(cluster_def.get(TaskType.WORKER, 0)):
            job_name = self.pod_manager.get_job_name(task_type=TaskType.WORKER, task_idx=i)
            workers.append(self._get_pod_address(job_name))

        cluster_config[TaskType.WORKER] = workers

        servers = []
        for i in range(cluster_def.get(TaskType.PS, 0)):
            job_name = self.pod_manager.get_job_name(task_type=TaskType.PS, task_idx=i)
            servers.append(self._get_pod_address(job_name))

        cluster_config[TaskType.PS] = servers

        return TensorflowClusterConfig.from_dict(cluster_config).to_dict()
