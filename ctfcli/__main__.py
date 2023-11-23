import os,sys,fire
sys.path.insert(0, os.path.abspath('.'))
from pathlib import Path

#---
from ctfcli.utils.utils import DEBUG
from ctfcli.utils.utils import errorlogger, yellowboldprint,greenprint,redprint
from ctfcli.utils.utils import debugblue,debuggreen,debugyellow
#---
from ctfcli.utils.config import Config
from ctfcli.linkage import SandBoxyCTFdLinkage
from ctfcli.core.gitrepo import SandboxyGitRepository
#from ctfcli.PyKCTF.kctf import ClusterHandler
###############################################################################

class Ctfcli():
	'''
		Proper Usage is as follows

		#THIS TOOL SHOULD BE ALONGSIDE the challenges repository folder
		
		#folder
		#	subfolder_challenges
		#		masterlist.yaml
		#		subfolder_category
		#	subfolder_ctfcli
		#		__main__.py
		
		FIRST RUN, If you have not modified the repository this is not necessary!
		This will generate a Masterlist.yaml file that contains the contents of the 
		repository for loading into the program
		>>> host@server$> python ./ctfcli/ ctfcli ctfdrepo init

		you should provide token and url when running the tool, it will store 
		token only for a limited time. This is intentional and will not be changed
		This tool is capable of getting its own tokens given an administrative username
		and password

		for SINGLE operations, with NO authentication persistance:
		Replace <URL> with your CTFd website url
		Replace <TOKEN> with your CTFd website token
		>>> host@server$> python ./ctfcli/ ctfcli --ctfdurl <URL> --ctfdtoken <TOKEN>

		for multiple operations, WITH authentication persistance:
		This configuration will be able to obtain tokens via CLI
		>>> host@server$> python ./ctfcli/ ctfcli --ctfdurl <URL> --adminusername moop --adminpassword password

		To sync repository contents to CTFd Server, 
		>>> host@server$> python ./ctfcli/ ctfcli syncrepository 

		Not supplying a password/username, or token, will attempt to read auth
		information already in the config./cfg file

		You can obtain a auth token from the "settings" page in the "admin panel"
		This will initialize the repository, from there, you can either:
		
		Pull a remote repository
		you have to create a new masterlist after this
		That will be covered further down.
		>>> host@server$> ctfd.py gitops createremoterepo https://REMOTE_REPO_URL.git

		Generating a completion script and adding it to ~/.bashrc
		>>> host@server$>python ./ctfcli/ ctfcli -- --completion > ~/.ctfcli-completion
		>>> host@server$> echo "source ~/.ctfcli-completion" >> ~/.bashrc  

		To generate a completion script for the Fish shell. 
		(fish is nice but incompatible with bash scripts so far as I know so start.sh wont work)
		>>> -- --completion fish 

		If the commands available in the Fire CLI change, you'll have to regenerate the 
		completion script and source it again.

		/ NOT IMPLEMENTED YET /
		IF YOU ARE MOVING YOUR INSTALLATION AFTER USING THE PACKER/UNPACKER
		IN START.SH, PERFORM THE FOLLOWING ACTIONS/COMMANDS
		>>> host@server$>python ./ctfcli/ ctfcli check_install
		/ NOT IMPLEMENTED YET /
	'''
	def __init__(self):
		# we import theswe if running in submodule mode
		self.important_env_list = [
			"PROJECT_ROOT",
			"CHALLENGEREPOROOT",
 			"COMPOSEDIRECTORY",
 			"KUBECONFIGPATH",
		]
		# modify the structure of the program here by reassigning classes
		if DEBUG == True:
			debugyellow("setting  env")
		self._setenv()

		#establish the linkage between meeplabben and the cli
		# program execution flow goes sideways right here for a bit as the repo
		# is initialized

		# this item is a function in the menu, allowing you to call functions on the class
		if DEBUG == True:
			debugyellow("creating linkage class")
		self.ctfrepo = SandBoxyCTFdLinkage(
								challenges_folder=self._challengesfolder,
								masterlistlocation=self.masterlist,
								configobject=self.config
								)
		
		# challenge templates, change this to use your own with a randomizer
		#self.TEMPLATESDIR = Path(self._toolfolder , "ctfcli", "templates")

		# create/reinitialize a git repository
		#try:
			# we do this last so we can add all the created files to the git repo		
			# this is the git backend, operate this seperately
		#	self.gitops = SandboxyGitRepository(self._reporoot)
			#self.gitops.createprojectrepo()
		#except Exception:
		#	errorlogger("[-] Git Repository Creation Failed, check the logfile")

		# initialize the cluster managment class
		#try:
			#self.init_cluster()
		#except:
		#	errorlogger("[-] Cluster Initialization FAILED! Exiting program!")
		#	sys.exit()

	def init_cluster(self):
		'''
		starts a cluster with docker, defaults to "Kind"
		'''
		#self.cluster = ClusterHandler(self.tools_folder,self._challengesfolder)
		# check for kind binary and download if necessary
		#self.cluster.ensure_kind()
		# check for kubectl binary and download if necessary
		#self.cluster.ensure_kubectl()
		
	#def handle_cluster(self,cluster_object:ClusterHandler):
	#	'''
	#	Handles the cluster manager class
	#	'''
	#	self.cluster_instance = cluster_object

	def set_config(self):
		'''
		Sets the config file to self
		'''
		# bring in config functions
		if DEBUG == True:
			debugyellow("creating config class")
		self.config = Config(self.configfile)

	def _getenv(self):
		'''
		Retrieves neceessary env vars if running in submodule mode
		all variables should be a Path to a location nearby
		'''
		if DEBUG == True:
			debugyellow("Loading the following variables from the shell environment")
		for var_name in self.important_env_list:
			if DEBUG == True:
				debugblue(var_name)
		for each in self.important_env_list:
			if DEBUG == True:
				debugyellow("setting  env")
				debugyellow(f"SETTING {each} as {os.getenv(each)}")
			setattr(self,each, Path(os.getenv(each)))

	def run_standalone(self):
		'''
		init procedure for running outside the meeplabben environment \n
		to handle context switching between standalone tool usage with external repo \n
		and internal usage with built in repository
		'''
		if DEBUG == True:
			debugyellow("running in standalone mode")
		try:
			# set var to indicate folder hierarchy
			onelevelup = self._toolfolder.parent
			if DEBUG == True:
				debugyellow(f" one folder up : {onelevelup}")
			# if a folder named challenges is in the directory next to this one
			for item in os.listdir(onelevelup):
				# found folder
				if DEBUG == True:
					debugyellow(f"itterating - directory listing item: {item}")
				if os.path.isdir(item) and item == "challenges":
					yellowboldprint("[+] Challenge Folder Found alongside tool folder, presuming to be repository location")
					# set var to challenge folder location
					self._challengesfolder = os.path.join(onelevelup, "challenges")
					# set var to repository root
					self._reporoot = onelevelup
					if DEBUG == True:
						debuggreen(f"challenges folder at {self._challengesfolder}")
						debuggreen(f"repository root folder at {self._reporoot}")
					break
				# not the droid/folder we are looking for
				elif (os.path.isdir(item) and item != "challenges"):
					continue
				# not even a droid/folder
				elif not os.path.isdir(item):
					continue
			# folder one level up is empty?
			else:
				yellowboldprint("[!] Challenge folder not found Alongside tool folder, Exiting program!")
				raise Exception
		except Exception:
			errorlogger("[-] Error, cannot find repository! ")
	
	def run_as_submodule(self):
		'''
		init procedure for running as a submodule of meeplabben \n
		to handle context switching between standalone tool usage with external repo \n
		and internal usage with built in repository

		THIS MODE OF OPERATION SHOULD NOT BE USED UNTIL CLUSTER BOOTSTRAP PROCEDURES
		ARE FULLY COMPLETE!

		USE STANDALONE WITH CTDF SOFTWARE MANUALLY INSTALLED UNTIL THEN!
		'''
		# PROJECT_ROOT has already been set
		# so has other variables
		# get the env vars for the module
		if DEBUG == True:
			debugyellow("running in submodule mode")
		self._getenv()
		yellowboldprint(f"[+] Project root ENV variable is {self.PROJECT_ROOT}")

		# set the variable indicating the data repository
		self._reporoot = Path(self.PROJECT_ROOT,"data")
		yellowboldprint(f'[+] Repository root ENV variable is {self._reporoot}')
		
		# expected location of CHALLENGE repository
		# the location you store all the CHALLENGES for the project
		self._challengesfolder = Path(self._reporoot, "challenges")
		yellowboldprint(f'[+] Challenges root ENV variable is {self._challengesfolder}')
		
		# location of binaries used for project
		# ~/meeplabben/data/bin
		self.tools_folder = Path(self._reporoot, "bin")
		yellowboldprint(f"[+] Tooling is located at {self.tools_folder}")
		
		# location of the all important masterlist
		# # ~/meeplabben/data/masterlist.yaml
		self.masterlist = Path(self._reporoot, "masterlist.yaml")
		yellowboldprint(f'[+] Masterlist is expected to be at {self.masterlist}')
		
		# location of the config file
		# ~/meeplabben/config.cfg
		self.configfile = Path(self.PROJECT_ROOT, "config.cfg")
		yellowboldprint(f'[+] Config File is expected to be at {self.configfile}')
		
		# bring in config functions
		self.config = Config(self.configfile)
		self.set_config()
		
	def _setenv(self):
		"""
		Handles environment switching from being a 
		standlone module to being a submodule
		"""
		#PWD = Path(os.path.realpath("."))

		# where this tool is located
		self._toolfolder   = Path(os.path.dirname(__file__))
		greenprint(f"[+] Tool folder Located at {self._toolfolder}")

		if __name__ == "__main__":
			# TODO: make function to check if they put it next to
			#  an actual repository fitting the spec
			self.run_standalone()
		# not being run standalone
		# i.e. this tool is being used in the meeplabben environment
		else:
			self.run_as_submodule()

def main():
   fire.Fire(Ctfcli)

if __name__ == "__main__":
	main()
	#fire.Fire(Ctfcli)