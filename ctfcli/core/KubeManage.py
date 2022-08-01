import os, sys
import yaml
from pathlib import Path
from ctfcli.core.deployment import Deployment


from ctfcli.utils.config import Config
from ctfcli.utils.utils import errorlogger, greenprint,redprint,yellowboldprint,debuggreen
from ctfcli.utils.utils import debugblue,debugred,debugyellow

from docker import client
import kubernetes

import select
import socket
import time

import six.moves.urllib.request as urllib_request

from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.client.api.core_v1_api import CoreV1Api
from kubernetes.client.rest import ApiException
from kubernetes.stream import portforward

class Dockerfile:
    '''
    Python representation of a standard Dockerfile
    '''
    def __new__(cls,*args, **kwargs):
        cls.__name__ = 'Dockerfile'
        cls.__qualname__= cls.__name__
        cls.tag = '!Dockerfile'
        return super(cls).__new__(cls, *args, **kwargs)
    
    def __init__(self,dockerfile_path:Path, **entries): 
        #print("[+] Transforming Dockerfile to python code")
        self.__dict__.update(entries)
        self.dockerfile_path = dockerfile_path
    
    def __repr__(self):
        '''
        '''
        wat = []
        for key in self.__dict__:
            wat.append(str(key) + " : " + str(self.__dict__[key]))
        #return self_repr
        return wat
    
    def get_text(self):
        self.__repr__()


class SpecFile:
    '''
    Metaclass for loading yml files into
    '''
    def __new__(cls,*args, **kwargs):
        cls.__name__ = 'service'
        cls.__qualname__= cls.__name__
        cls.tag = '!service'
        return super(cls).__new__(cls, *args, **kwargs)
    
    def __init__(self,**entries): 
        print("[+] Creating Service.yaml python code")
        self.__dict__.update(entries)
    
    def __repr__(self):
        '''
        '''
        wat = []
        for key in self.__dict__:
            wat.append(str(key) + " : " + str(self.__dict__[key]))
        #return self_repr
        return wat

class KubernetesYaml(SpecFile): #file
    """
    Represents a Kubernetes specification
    future
    """    
    def __init__(self): 
        print("[+] Generating new repository")


class HelmManagment():
    def __init__(self):
        '''
        Uses pyhelm to provision the kubernetes infrastructure
        '''

class KubernetesManagment():
    def __init__(self,config:Config):
        """
        
        """
        # Configs can be set in Configuration class directly or using helper
        # utility. If no argument provided, the config will be loaded from
        # default location.
        self.kubeconfig = kubernetes.config.load_kube_config()
        # need various things from config like registry name
        self.config = config
        # the registry in use
        self.registry_str = str
        # cluster namespace
        self.cluster_namespace = 'default'
        # list of pods in cluster
        self.pods_list= dict
    
    def init_client(self):
        '''
        established the client for the cluster, api handler function
        '''
        self.kubeconfig.load_kube_config()
        config = Configuration.get_default_copy()
        config.assert_hostname = False
        Configuration.set_default(config)
        self.core_v1 = core_v1_api.CoreV1Api()
        
    
    def deploy_pod(self,config_path:Path,cluster_namespace = "default"):
        '''
        Deploys a pod with given yml manifest \n
        Do not use on deployed pods that are already running, \n
        that will simply create another and increase overhead  \n
        For those you must reload, or remove/recreate.
        
        '''
        with open(os.path.join(os.path.dirname(__file__), str(config_path.absolute()))) as deployment_yaml:
            dep = yaml.safe_load(deployment_yaml)
            k8s_apps_v1 = client.AppsV1Api()
            cluster_response = k8s_apps_v1.create_namespaced_deployment(
                body=dep, namespace=cluster_namespace)
            greenprint("[+] Deployment created. status='%s'" % cluster_response.metadata.name)

    def port_forward_to_pod(self, namespace:str,host_port:int,pod_port:int, api_instance:CoreV1Api):
        '''
        This requires kubectl be in the path, I looked at the python implementation
        and decided a  direct call to the application is easier and cleaner to implement
        '''

    def deploy_pod_from_json(self,json_container):
        '''
        uses a json container as manifest, more pythonic way of creating a pod
        '''
        name=json_container["metadata"]["name"]
        greenprint(f"[+] Deploying Pod {name}")
        self.core_v1.create_namespaced_pod(body=json_container,
                                           namespace=self.cluster_namespace)
        while True:
            resp = self.core_v1.read_namespaced_pod(name=name,
                                                    namespace=self.cluster_namespace)
            if resp.status.phase != 'Pending':
                break
            time.sleep(1)
        greenprint("[+] Pod deployed")

    def deployment_to_pod(self, deployed_challenge:Deployment):
        '''
        deploys a pod based on a Deployment() class, rather than the yml file representing it
        This same function also exists in the Deployment class itself to allow deployment as its created   
        '''
        self.deploy_pod_from_json(deployed_challenge.deployment_yaml_json)
    
    def get_ports_in_use(self):
        '''
        gets ports being used on HOST SERVER by kubernetes
        '''
    def list_active_pods(self):
        '''
        lists all currently running pods and status
        Can filter by category, difficulty,and popularity
        '''


    def _init_nginx(self,path:Path):
        """
        from docs/examples

        The nginx yaml resides in $PROJECTROOT/containers/nginx
        """
        with open(path.join(path.dirname(__file__), "nginx-deployment.yaml")) as f:
            dep = yaml.safe_load(f)
            k8s_apps_v1 = client.AppsV1Api()
            resp = k8s_apps_v1.create_namespaced_deployment(
                body=dep, namespace="default")
            print("Deployment created. status='%s'" % resp.metadata.name)
