import os, sys
import yaml, pathlib, logging, traceback
from pathlib import Path
from yaml import SafeDumper,MappingNode,Dumper,Loader
from yaml import safe_load,safe_dump,add_representer

from ctfcli.utils.config import Config
from ctfcli.utils.utils import getpath
from ctfcli.ClassConstructor import Yaml,Constructor
from docker import client
from hashlib import sha1
import kubernetes

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
class KubernetesManagment(KubernetesYaml):
    def __init__(self):
        """
        
        """
        # Configs can be set in Configuration class directly or using helper
        # utility. If no argument provided, the config will be loaded from
        # default location.
        kubernetes.config.load_kube_config()

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

#if __name__ == '__main__':
listofimportantyamlfiles = ["deployment.yaml","service.yaml"]
packageofyaml = {}
packageofcode = {}
for importantyaml in listofimportantyamlfiles:
    # get path
    yamlpath = getpath(importantyaml)
    # load file
    newyaml = Yaml().loadyaml(yamlpath)
    # add to output
    packageofyaml[importantyaml] = newyaml

for importantyaml in listofimportantyamlfiles:
    # get path
    yamlpath = getpath(importantyaml)
    # load file WITH CONSTRUCTOR FOR CODE
    newpythoncode = Constructor()._loadyaml(getpath(importantyaml))
    # add to output
    packageofcode[importantyaml] = newpythoncode