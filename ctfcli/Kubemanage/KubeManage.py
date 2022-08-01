import os, sys
import yaml
from pathlib import Path


from docker import client
import kubernetes

import time

from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.client.api.core_v1_api import CoreV1Api
from kubernetes.client.rest import ApiException
from kubernetes.stream import portforward

import configparser

import sys
import yaml
import os
import pathlib
import logging
import traceback
from pathlib import Path
global DEBUG
DEBUG = True

try:
    #import colorama
    from colorama import init
    init()
    from colorama import Fore, Back, Style
    COLORMEQUALIFIED = True
except ImportError as derp:
    print("[-] NO COLOR PRINTING FUNCTIONS AVAILABLE, Install the Colorama Package from pip")
    COLORMEQUALIFIED = False

################################################################################
##############               LOGGING AND ERRORS                #################
################################################################################
log_file            = 'logfile'
logging.basicConfig(filename=log_file, 
                    #format='%(asctime)s %(message)s', 
                    filemode='w'
                    )
logger              = logging.getLogger()
launchercwd         = pathlib.Path().absolute()

redprint          = lambda text: print(Fore.RED + ' ' +  text + ' ' + Style.RESET_ALL) if (COLORMEQUALIFIED == True) else print(text)
blueprint         = lambda text: print(Fore.BLUE + ' ' +  text + ' ' + Style.RESET_ALL) if (COLORMEQUALIFIED == True) else print(text)
greenprint        = lambda text: print(Fore.GREEN + ' ' +  text + ' ' + Style.RESET_ALL) if (COLORMEQUALIFIED == True) else print(text)
yellowboldprint = lambda text: print(Fore.YELLOW + Style.BRIGHT + ' {} '.format(text) + Style.RESET_ALL) if (COLORMEQUALIFIED == True) else print(text)
makeyellow        = lambda text: Fore.YELLOW + ' ' +  text + ' ' + Style.RESET_ALL if (COLORMEQUALIFIED == True) else None
makered           = lambda text: Fore.RED + ' ' +  text + ' ' + Style.RESET_ALL if (COLORMEQUALIFIED == True) else None
makegreen         = lambda text: Fore.GREEN + ' ' +  text + ' ' + Style.RESET_ALL if (COLORMEQUALIFIED == True) else None
makeblue          = lambda text: Fore.BLUE + ' ' +  text + ' ' + Style.RESET_ALL if (COLORMEQUALIFIED == True) else None
debugred = lambda text: print(Fore.RED + '[DEBUG] ' +  text + ' ' + Style.RESET_ALL) if (DEBUG == True) else None
debugblue = lambda text: print(Fore.BLUE + '[DEBUG] ' +  text + ' ' + Style.RESET_ALL) if (DEBUG == True) else None
debuggreen = lambda text: print(Fore.GREEN + '[DEBUG] ' +  text + ' ' + Style.RESET_ALL) if (DEBUG == True) else None
debugyellow = lambda text: print(Fore.YELLOW + '[DEBUG] ' +  text + ' ' + Style.RESET_ALL) if (DEBUG == True) else None
debuglog     = lambda message: logger.debug(message) 
infolog      = lambda message: logger.info(message)   
warninglog   = lambda message: logger.warning(message) 
errorlog     = lambda message: logger.error(message) 
criticallog  = lambda message: logger.critical(message)

def file_to_text(filepath:Path):
    '''
    opens a file and returns the text
    '''
    fileobject = open(filepath)
    file_text = fileobject.read()
    fileobject.close()
    return file_text

def get_dirlist(directory:Path)-> list[Path]:
    '''
    Returns a directory listing of BOTH files and folders
    '''
    wat = []
    for filepath in pathlib.Path(directory).iterdir():
        wat.append(Path(filepath))
    return wat


def getsubdirs(directory)->list[Path]:
    '''
    Returns folders in a directory as Path objects
    '''
    wat = []
    for filepath in pathlib.Path(directory).iterdir():
       if (Path(filepath).is_dir()):
           wat.append(Path(filepath))
    return wat

def getsubfiles(directory)->list:
    '''
    Shallow directory listing of files only \n
    for deep search use getsubfiles_deep()
    '''
    wat = []
    for filepath in pathlib.Path(directory).iterdir():
       if (Path(filepath).is_file()):
           wat.append(Path(filepath))
    return wat

def getsubfiles_deep(directory)->list[Path]:
    '''
    Returns ALL sub-files in a directory as Paths\n
    This itterates down to the BOTTOM of the hierarchy!
    This is a highly time intensive task!
    '''
    wat = [Path(filepath) for filepath in pathlib.Path(directory).glob('**/*')]
    return wat


def getsubfiles_dict(directory)->dict[str:Path]:
    '''
    Returns files in a directory as absolute paths in a dict
    {
        1filename : 1filepath,
        2filename : 2filepath,
        3filename : 3filepath,
        ... and so on
    }
    '''
    wat = {}
    #wat = {filepath.stem: Path(filepath) for filepath in pathlib.Path(directory).glob('**/*')}
    #directory_list = Path(directory).glob('**/*')
    for filepath in pathlib.Path(directory).iterdir():
        if filepath.is_file():
            wat[filepath.stem] = filepath.absolute()
    return wat


# open with read operation
yamlbuffer_read = lambda path: open(Path(path),'r')
# open with write operation
yamlbuffer_write = lambda path: open(Path(path),'r')
#loads a challenge.yaml file into a buffer
loadyaml =  lambda category,challenge: yaml.load(yamlbuffer_read(category,challenge), Loader=yaml.FullLoader)
writeyaml =  lambda category,challenge: yaml.dump_all(yamlbuffer_write(category,challenge), Loader=yaml.FullLoader)
# simulation of a chdir command to "walk" through the repo
# helps metally
#location = lambda currentdirectory,childorsibling: Path(currentdirectory,childorsibling)
# gets path of a file
getpath = lambda directoryitem: Path(os.path.abspath(directoryitem))

################################################################################
##############             ERROR HANDLING FUNCTIONS            #################
################################################################################
def errorlogger(message):
    """
    prints line number and traceback
    TODO: save stack trace to error log
            only print linenumber and function failure
    """
    exc_type, exc_value, exc_tb = sys.exc_info()
    trace = traceback.TracebackException(exc_type, exc_value, exc_tb) 
    lineno = 'LINE NUMBER : ' + str(exc_tb.tb_lineno)
    logger.error(
        redprint(
            message+"\n [-] "+lineno+"\n [-] "+''.join(trace.format_exception_only()) +"\n"
            )
        )
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

    def to_yaml(self, pyyaml=False):
        '''
        Converts class to yaml, use "pyaml=true" to store as python code objects
        '''
        if pyyaml == False:
            raise NotImplemented
        elif pyyaml == True:
            raise NotImplemented
            #not functional yet
            #Constructor._writeyaml()


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
