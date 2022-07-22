import yaml

import sys
from pathlib import Path
from ctfcli.core.repository import Repository
from yaml import SafeDumper,MappingNode,Dumper,Loader
from ctfcli.utils.utils import errorlogger
from yaml import SafeDumper,MappingNode
from ctfcli.core.repository import Repository


class Yaml(yaml.YAMLObject): #filetype
    """
    Base class for challenges and the repo

    Anything thats a yaml file inherits from this
    Args:
        filepath (str): Full Filepath to Yaml File to load
    """
    def __init__(self, filepath:Path=None):
        if filepath == None:
            pass
        else:
            self.filename = os.path.basename(filepath)
            self.filepath = filepath
            self.directory = self.filepath.parent
            #if self.filename.endswith(".yaml"):
            #    greenprint("[!] File is .yaml! Presuming to be kubernetes config!")
            #    self.type = "kubernetes"
            #elif self.filename.endswith(".yml"):
            #    greenprint("[!] Challenge File presumed (.yml)")
            #    self.type = "challenge"

    def loadyaml(self, filepath:Path) -> dict:
        """
        Loads the yaml specified by the class variable Yaml.filepath
        """
        # I copied the code to prevent having to go back and rewrite I 
        # think like ONE thing, so this can be cleaned up some
        self.filename = os.path.basename(filepath)
        self.filepath = filepath
        self.directory = self.filepath.parent
        #if self.filename.endswith(".yaml"):
        #    greenprint("[!] File is .yaml! Presuming to be kubernetes config!")
        #    self.type = "kubernetes"
        #elif self.filename.endswith(".yml"):
        #    greenprint("[!] Challenge File presumed (.yml)")
        #    self.type = "challenge"
        try:
            with open(filepath, 'r') as stream:
                return yaml.safe_load(stream)
        except Exception:
            errorlogger("[-] ERROR: Could not load .yml file")
    
    def writeyaml(self):
        """
        Remember to assign data to the file with

        >>> thing = Yaml(filepath)
        >>> thing.data['key'] = value
        """
        try:
            #open the yml file pointed to by the load operation
            with open(self.filepath) as file:
                safe_dump(file)
        except Exception:
            errorlogger("[-] ERROR: Could not Write .yml file, check the logs!")

class Constructor():
    """
    This is one way of turning a yaml file into python code

    https://matthewpburruss.com/post/yaml/

    """
    def __init__(self):
        self.repotag = "!Repo:"
        self.categorytag = "!Category:"
        self.challengetag = "!Challenge:"
        self.nodetags = {
            "":"!Repo:",
            "":"!Category:",
            "":"!Challenge:",
            "":"!Deployment:",
            
        }
        self.represent = lambda tag,dumper,codeobject: dumper.represent_mapping(tag, codeobject.__dict__)
        super().__init__()


    def _representer(self, dumper: SafeDumper, codeobject) -> MappingNode:
        """
        Represent a Object instance as a YAML mapping node.

        This is part of the Output Flow from Python3.9 -> Yaml

        In the Representer Class/Function You must define a mapping
        for the code to be created from the yaml markup

        Args:
            tag (str) : tag to assign object in yaml file
            codeobject (str): python code in a single object
        """
        tag = "!Repo:"
        return dumper.represent_mapping(tag, codeobject.__dict__)
 
    def _loader(self, loader: Loader, node: yaml.nodes.MappingNode):
        """
        Construct an object based on yaml node input
        Part of the flow of YAML -> Python3
        """
        # necessary for pyyaml to load files on windows
        if sys.platform == "win32":
            import pathlib
            pathlib.PosixPath = pathlib.WindowsPath
        return Repository(**loader.construct_mapping(node, deep=True))
        

    def _get_dumper(self,constructor, classtobuild):
        """
        Add representers to a YAML serializer.

        Converts Python to Yaml
        """
        safe_dumper = Dumper
        safe_dumper.add_representer(classtobuild, constructor)
        return safe_dumper
 
    def _get_loader(self, tag, constructor):
        """
        Add constructors to PyYAML loader.

        Converts Yaml to Python
        Args:
            tags (str): the tag to use to mark the yaml object in the file
            constructor (function): the constructor function to call
        """
        loader = Loader
        loader.add_constructor(tag,constructor)
        return loader
    
    def _loadyaml(self,tag, filelocation:Path):
        """
        Loads the masterlist.yaml into Masterlist.data
        Yaml -> Python3

        Args:
            masterlistfile (str): The file to load as masterlist, defaults to masterlist.yaml
        """
        try:
            #open the yml
            # feed the tag and the constructor method to call
            return yaml.load(open(filelocation, 'rb'), 
                Loader=self._get_loader(tag, self._loader))
        except Exception:
            errorlogger("[-] ERROR: Could not load .yml file {filelocation.stem}")

    def _writeyaml(self,filepath, pythoncode, classtype,filemode="w"):
        """
        Creates a New file
        remember to assign data to the file with
        
        >>> thing = yamlconstructor(filepath)
        >>> thing._writenewstorage(pythoncodeobject)

        Args: 
            pythoncode (Object): an instance of a python object to transform to YAML
            filemode (str) : File Mode To open File with. set to append by default
        """
        try:
            with open(filepath, filemode) as stream:
                stream.write(yaml.dump(pythoncode,
                        Dumper=self._get_dumper(self._representer,classtype)))
        except Exception:
            errorlogger("[-] ERROR: Could not Write .yml file, check the logs!")





###############################################################################
#  wat, someone tech me how to make this construct arbitrary classes?
###############################################################################
class YAMLMultiObjectMetaclass(yaml.YAMLObjectMetaclass):
    """
    The metaclass for YAMLMultiObject.
    """
    def __init__(cls, name, bases, **kwds):
        yaml_tags = {}
        super(YAMLMultiObjectMetaclass, cls).__init__(name, bases, kwds)
        for tag in yaml_tags:
            if kwds[tag] is not None:
                cls.yaml_loader.add_multi_constructor(cls.tag, cls.from_yaml)
                cls.yaml_dumper.add_multi_representer(cls, cls.to_yaml)
        if any(yaml_tags) in kwds:
            if kwds['yaml_tag'] is not None:
            cls.yaml_loader.add_multi_constructor(cls.yaml_tag, cls.from_yaml)
            cls.yaml_dumper.add_multi_representer(cls, cls.to_yaml)

class YAMLMultiObject(yaml.YAMLObject, metaclass=YAMLMultiObjectMetaclass):
    """
    An object that dumps itself to a stream.
    
    Use this class instead of YAMLObject in case 'to_yaml' and 'from_yaml' should
    be inherited by subclasses.
    """
    pass


class MyDumper(yaml.SafeDumper):
    def represent_data(self, data):
        if isinstance(data, Enum):
            return self.represent_data(data.value)
        return super().represent_data(data)

class Foo(Enum):
    A = 1
    B = 2

data = {
    'value1': Foo.A,
}
yaml.dump(data, Dumper=MyDumper)

