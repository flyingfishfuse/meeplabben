from ctfcli.utils.utils import infolog,errorlogger,greenprint,redprint,yellowboldprint
from ctfcli.core.yamlstuff import Yaml,KubernetesYaml

import os
from pathlib import Path
from hashlib import sha1

# deployment managment
from kubernetes import client, config, watch
import docker,yaml

class Deployment():
    """
    Base Class for all the attributes required on both the CTFd side and Repository side
    Represents the challenge.yml as exists in the folder for that specific challenge

    Represents a Challenge Folder
    
    Contents of a Challenge Folder:
        handouts: File or Folder
        solution: File or Folder 
        challenge.yaml

    Args:
        yamlfile        (Path): filepath of challenge.yaml
        category        (str):  category to assign to, currently set as folder name
                                needs to be set by yaml tag
        handout         (Path)
        solution        (Path)
    """
    def __init__(self,
            category,
            handout,
            solution,
            deployment:Path,
            service:Path,
            readme
            ):
        self.tag = "!Deployment:"
        self.readme = readme
        self.category = category
        self.solution = solution
        self.handout  = handout
         
         # here, we deviate from the challenge class and include
         # deployment and service yaml files
        self.deployment_folder = deployment
        #self.service = service

        # this is set after syncing by the ctfd server, it increments by one per
        # challenge upload so it's predictable
        self.id = int

    def _initchallenge(self,**kwargs):
        """
        Unpacks a dict representation of the challenge.yaml into
        The Challenge() Class, this is ONLY for challenge.yaml

        The structure is simple and only has two levels, and no stored code

        >>> asdf = Challenge(filepath)
        >>> print(asdf.category)
        >>> 'Forensics'

        The new challenge name is created by:

        >>> self.__name = "Challenge_" + str(hashlib.sha256(self.name))
        >>> self.__qualname__ = "Challenge_" + str(hashlib.sha256(self.name))
        
        Resulting in a name similar to 
        Args:
            **entries (dict): Dict returned from a yaml.load() operation on challenge.yaml
        """
        # internal data
        self.id = str
        self.synched = bool
        self.installed = bool

        self.jsonpayload = {}
        self.scorepayload = {}
        # we have everything preprocessed
        for each in kwargs:
            setattr(self,each,kwargs.get(each))
        # the new classname is defined by the name tag in the Yaml now
        self.internalname = "Deployment_" + str(sha1(self.name.encode("ascii")).hexdigest())
        self.__name = self.internalname
        self.__qualname__ = self.internalname
        yellowboldprint(f'[+] Internal name: {self.internalname}')

class KubernetesConfig(client.Configuration):
    """
    Wraper for kubernetes.client.configuration
        By default, kubectl looks for a file named config 
        in the $HOME/.kube directory. You can specify other 
        kubeconfig files by setting the KUBECONFIG 
        environment variable
    """
    def __init__(self,kubeconfigpath:Path):
        """
        currently in version 1.5, we set the KUBECONFIG environmment variable 
        in the top level file __main__.py in the root project directory

        if it isnt set, the module is being used in standalone mode and must be set
        manually by providing a dict to kubecopnfigpath

        >>>    {
        >>>        KUBECONFIG  : ""
        >>>        context     : ""
        >>>    }

        Args:
            kubeconfigpath (Path): Path to kubeconfig folder
        """
        self.kubeconfigpath = Path
        if "KUBECONFIG" in os.environ():
            self.kubeconfigpath = os.environ.get("KUBECONFIG")
            infolog(f"[+] KUBECONFIG environment variable set as \n {self.kubeconfigpath}")
        elif "KUBECONFIG" not in os.environ():
            self.setkubernetesenvironment(kubeconfigpath)
            infolog(f"[?] KUBECONFIG environment variable is not set")
            infolog(f"[+] KUBECONFIG environment variable set as \n {self.kubeconfigpath}")
 
    def setkubernetesenvironment(self,configdict:dict,useenv = True):
        """
        sets kubernetes environment
        if useenv is set to True, uses system environment variables
        for setting config, otherwise
        if set to false, uses provided dict
            {
                KUBECONFIG  : ""
                context     : ""
            }
        """
        if useenv:
            config_file = os.environ.get("KUBECONFIG", KUBE_CONFIG_PATH),
            context = os.environ.get("KUBECONTEXT")
        elif not useenv:
            config_file = configdict.get("KUBECONFIG")
            context = configdict.get("context")

        self.load_kube_config(
            config_file,
            context,
        )

    def setkubeconnection(self,
                      authtoken = "YOUR_TOKEN",
                      authorization = "Bearer",
                      host = "http://192.168.1.1:8080"):
        """
        """

        # Defining host is optional and default to http://localhost
        #configuration.host = "http://localhost"

        self.host = host
        self.api_key_prefix['authorization'] = authorization
        self.api_key['authorization'] = authtoken
        v1 = client.CoreV1Api()

class KubernetesManagment():
    def __init__(self):
        """
        
        """
        # Configs can be set in Configuration class directly or using helper
        # utility. If no argument provided, the config will be loaded from
        # default location.
        config.load_kube_config()
    
    def get_k8s_nodes(exclude_node_label_key=app_config["EXCLUDE_NODE_LABEL_KEY"]):
        """
        Returns a list of kubernetes nodes
        """

        try:
            config.load_incluster_config()
        except config.ConfigException:
            try:
                config.load_kube_config()
            except config.ConfigException:
                raise Exception("Could not configure kubernetes python client")

        k8s_api = client.CoreV1Api()
        infolog("Getting k8s nodes...")
        response = k8s_api.list_node()
        if exclude_node_label_key is not None:
            nodes = []
            for node in response.items:
                if exclude_node_label_key not in node.metadata.labels:
                    nodes.append(node)
            response.items = nodes
        infolog.info("Current k8s node count is {}".format(len(response.items)))
        return response.items 

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

class DockerManagment():
    def __init__(self):
        #connects script to docker on host machine
        client = docker.from_env()
        self.runcontainerdetached = lambda container: client.containers.run(container, detach=True)

    def listallpods(self):
        self.setkubeconfig()
        # Configs can be set in Configuration class directly or using helper utility
        print("Listing pods with their IPs:")
        ret = self.client.list_pod_for_all_namespaces(watch=False)
        for i in ret.items:
            print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

    def watchpodevents(self):
        self.setkubeconfig()
        count = 10
        watcher = watch.Watch()
        for event in watcher.stream(self.client.list_namespace, _request_timeout=60):
            print("Event: %s %s" % (event['type'], event['object'].metadata.name))
            count -= 1
            if not count:
                watcher.stop()

    def startcontainerset(self,containerset:dict):
        ''' 
        Starts the set given by params
        '''
        for name,container in containerset.items:
            self.runcontainerdetached(container=containerset[name])

    def runcontainerwithargs(self,container:str,arglist:list):
        client.containers.run(container, arglist)

    def listcontainers(self):
        '''
        lists installed containers
        '''
        for container in client.containers.list():
            print(container.name)


    def opencomposefile(self,docker_config):
        '''
        '''
        with open(docker_config, 'r') as ymlfile:
            docker_config = yaml.load(ymlfile)

    def writecomposefile(self, docker_config,newyamldata):
        with open(docker_config, 'w') as newconf:
            yaml.dump(docker_config, newyamldata, default_flow_style=False)
