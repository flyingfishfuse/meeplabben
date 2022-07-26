from ctfcli.utils.utils import infolog,errorlogger,greenprint,redprint,yellowboldprint
from ctfcli.utils.utils import getsubfiles_dict,getsubdirs,file_to_text
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
		yamlfile		(Path): filepath of challenge.yaml
		category		(str):  category to assign to, currently set as folder name
								needs to be set by yaml tag
		handout		 (Path)
		solution		(Path)
	"""
	def __init__(self,
			category,
			handout,
			solution,
			deployment:Path,
			readme
			):
		self.tag = "!Deployment:"
		self.readme = readme
		self.category = category
		self.solution = solution
		self.handout  = handout

		 # here, we deviate from the challenge class and include
		 # deployment and service yaml files
		self.deployment_folder_path = deployment

		self.process_deployment_folder()

		self.process_deployment_files()
		
		 
		#self.service = service

		# this is set after syncing by the ctfd server, it increments by one per
		# challenge upload so it's predictable
		self.id = int

	def process_deployment_folder(self,deployment_folder_path):
		'''
		Processes the contents of the deployment folder into the class
		'''
		# get the listings
		files_in_deployment_folder = getsubfiles_dict(deployment_folder_path)
		#folders_in_deployment_folder = getsubdirs(deployment_folder_path)

		#assign the values
		self.deployment_yaml_path = files_in_deployment_folder.get("deployment")
		self.dockerfile_path = files_in_deployment_folder.get("Dockerfile")
		self.service_yaml_path = files_in_deployment_folder.get("service")
	
	def process_deployment_files(self):
		'''
		Handles the processing of the contents of files necessary for deployment
		If the files are changed on disk they must be updated in the masterlist
		Use this function to do that
		'''
		self.parse_service_yaml(self.service_yaml_path)
		self.parse_dockerfile(self.dockerfile_path)
		self.parse_deployment_yaml(self.deployment_yaml_path)

###############################################################################
#   SERVICE YAML PROCESSING
###############################################################################
	def parse_service_yaml(self,service_yaml_path):
		'''
		Gets the string representation of a service.yml file and
		attach it to the Deployment object as text.

		This allows it to be inserted to the masterlist, attached to the 
		object for easy deployment

		>>> deployed_challenge = Deployment._initdeployment(**kwargs)
		>>> deployed_challenge.service_yaml_text()
			... service.yaml contents ...

		'''
		self.service_yaml_text = file_to_text(self.service_yaml_path)

	def service_yaml(self):
		'''
		Returns the text of the service.yaml
		'''
		return self.service_yaml_text

###############################################################################
#  DOCKERFILE PROCESSING
###############################################################################
	def parse_dockerfile(self, dockerfile_path:Path)-> str:
		'''
		Gets the string representation of a dockerfile and
		attach it to the Deployment object as text.

		This allows it to be inserted to the masterlist, attached to the 
		object for easy deployment

		>>> deployed_challenge = Deployment._initdeployment(**kwargs)
		>>> deployed_challenge.dockerfile_text()
			... dockerfile contents ...
		'''
		self.dockerfile_text = file_to_text(dockerfile_path)

	def dockerfile(self):
		'''
		Returns the text of the Dockerfile
		'''
		return self.dockerfile_text

###############################################################################
#   DEPLOYMENT YAML PROCESSING
###############################################################################

	def parse_deployment_yaml(self, deployment_yaml_path:Path):
		'''
		Gets the string representation of a dockerfile and
		attach it to the Deployment object as text.

		This allows it to be inserted to the masterlist, attached to the 
		object for easy deployment

		>>> deployed_challenge = Deployment._initdeployment(**kwargs)
		>>> deployed_challenge.deployment_yaml_text()
			... deployment.yaml contents ... 
		'''
		self.deployment_yaml_text = file_to_text(self.deployment_yaml_path)

	def deployment_yaml(self):
		'''
		Returns the text of the deployment.yaml
		'''
		return self.deployment_yaml_text

###############################################################################
#   MAIN FLOW
###############################################################################
	def _initdeployment(self,**kwargs):
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