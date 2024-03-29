from genericpath import isdir
from logging import exception
import os
from pathlib import Path
from xmlrpc.client import Boolean
from ctfcli.core.yamlstuff import Yaml
from ctfcli.core.category import Category

from ctfcli.core.challenge import Challenge
from ctfcli.core.deployment import Deployment

from ctfcli.core.repository import Repository
from ctfcli.core.masterlist import Masterlist
from ctfcli.core.apisession import APIHandler
from ctfcli.utils.lintchallenge import Linter
from ctfcli.utils.utils import _processfoldertotarfile, getsubfiles
from ctfcli.utils.utils import getsubdirs,redprint,DEBUG
from ctfcli.utils.utils import errorlogger,yellowboldprint,debuggreen,logger
from ctfcli.utils.utils import debugblue,debuggreen,debugred,debugyellow

from ctfcli.utils.utils import validationdict
###############################################################################
#
###############################################################################

class SandboxyCTFdRepository():
	"""
	Backend to CTF Repository
	"""
	def __init__(self,
				challenges_folder:Path,
				masterlistlocation
				):
		self.masterlistlocation = masterlistlocation
		self.challenges_folder = challenges_folder
		self.allowedcategories = list
		try:
			debuggreen(" Instancing a SandboxyCTFdRepository()")
			super(SandboxyCTFdRepository, self).__init__()
		except Exception as e:
			errorlogger(f"[-] FAILED: Instancing a SandboxyCTFdLinkage(){e}")

	def _addmasterlist(self, masterlist:Masterlist):
		'''
		Adds a masterlist file to self
		'''
		setattr(self,'masterlist',masterlist)
		
	def _createrepo(self, allowedcategories)-> Repository:
		'''
		Performs all the actions necessary to create a repository
		From the Challenges Folder in the DATAROOT

		Creates the masterlist and Repository objects

		Returns:
		Masterlist, Repo (Tuple): Two new data objects

		'''
		debuggreen("Starting Repository Scan")
		self.dictofcategories = {}
		# get subdirectories in repository, these are the category folders
		repocategoryfolders = getsubdirs(self.challenges_folder)
			#debuggreen(f"[+] Categories: {[f'{folder}\n' for folder in repocategoryfolders]}")
		# itterate over folders in challenge directory
		for category in repocategoryfolders:
			categorypath = Path(os.path.join(self.challenges_folder, category))
			# if its a repository category folder in aproved list
			if category.stem in allowedcategories:
				# process the challenges in that category
				debuggreen(f"Found Category folder {categorypath.name}")
				#create a new Category and assign name based on folder
				newcategory = Category(categorypath.name,categorypath)   
				# this dict contains the entire repository now
				self.dictofcategories[newcategory.name] = newcategory
		# for each category folder in the repository folder
		for category in self.dictofcategories.copy().values():
			# process through validation
			processedcategory = self._processcategory(category)
			self.dictofcategories.update({processedcategory.name:processedcategory})
		# assign all categories to repository class
		# using protoclass + dict expansion
		#newrepo = Repository(**self.dictofcategories)
		# return this class to the upper level scope
		return  Repository(**self.dictofcategories)

	def _processcategory(self,newcategory:Category)-> Category:
		'''
		Itterates over a Category folder to add challenges to the database

		IF challenge is a "deployed" challenge, it will create a node in
		the cluster designated in the configuration file or as given on 
		the command line when the masterlist is created on "first run"
		during the initial file scan
			"category": category,
			"type":challengetype, # "deployment" or "challenge"
			"yaml":yamlcontents,
			"folderdata" : {
				"deployment": "",
				"service":"",
				"handout":handout, 
				"solution": solution
			}
		'''
		self.newcategory = newcategory
		#get subfolder names in category directory
		#categoryfolder = getsubdirs(newcategory.location)
		# itterate over the individual challenges
		for challengefolder in self.newcategory.dirlisting:
			# each in its own folder, name not required
			challengefolderpath = Path(self.challenges_folder,self.newcategory.name, challengefolder)
			debuggreen(f"Found folder {challengefolderpath.name}")
			debugyellow(f'{challengefolderpath}')
			try:
				# load yaml and scan folder
				folderscanresults = self._processfoldercontents(challengefolderpath)
				if folderscanresults["type"] == "deployment":
					self._createdeployment(folderscanresults)
				elif folderscanresults["type"] == "challenge":
					# create Challenge based off those
					newchallenge = self._createchallenge(folderscanresults)

				#assign challenge to category
				#newcategory._addchallenge(newchallenge)
				self.newcategory._addchallenge(newchallenge)

			except Exception:
				errorlogger('[-] Error Creating Challenge!')
				continue
		return self.newcategory

	def _check_for_deployment(self,folder_path:Path)->bool:
		'''
		Checks if challenge is a deployed challenge, if not, performs better validation
		in the next step
		
		'''
		# just because?
		if not folder_path:
			directory = self.folder_being_scanned
		else:
			directory = folder_path

		expanded_list = {name.stem:name for name in directory.iterdir()}
		if "deployment" in expanded_list and expanded_list["deployment"].is_dir():
			# set challenge type
			debugyellow("Deployment Folder Found, processing deployment files")
			self.challengetype = "deployment"
			# validate contents
			self.processdeploymentfolder(expanded_list["deployment"])
			# set var for data extraction
			self.deployment_folder = expanded_list["deployment"]
			self._check_for_standard(directory)
			return True

		else:
			debugred("\"deployment\" folder not found, presuming to be standard challenge")
			return False

	def _check_for_standard(self,folder_path:Path):
		'''
		checks if challenge is standard, non-deployed challenge
		Designed to allow for missing items, if all are missing, this returns FALSE \n
		If the challenge.yaml is missing, it returns FALSE regardless if "handout" or "solution" \n
		folders are present. 
		
		ALL extraneous items are currently SKIPPED!\n
		If its not part of the homework or solution, its irelevant!

		EXTRA ITEMS WILL CAUSE THE CHALLENGE TO BE REJECTED!
		THIS WILL NOT BE CHANGED!

		Follow the schema!
		'''
		debuggreen("Standard Challenge processing")
		valid_items = []
		validationlist =[
						"handout",
						"solution",
						"challenge.yaml",
						#"README"
						]
		validationlistlength = len(validationlist)

		try:
			if not folder_path:
				directory = self.folder_being_scanned
			else:
				directory = folder_path

			for item in directory.iterdir():
					# if its in the list
					if item.name in validationlist:
						# let the truthyness variable be set/remain as true
						truthyness = True
						debuggreen(f"Found Valid Item : {item.name}")
						valid_items.append(item)
						# handout and solution are always folders, they get zipped
						# to allow for more than one file to be part of both
						if item == "handout" and item.is_dir():
							self._package_handout(item)

						if item == "solution" and item.is_dir():
							self._package_solution(item)

						# validate the challenge yaml
						if item.name == "challenge.yaml" and item.is_file():
							self.yaml_contents = self.lint_challenge_yaml(item)

					elif item.stem not in validationlist:
						debugyellow(f"[-] Found Extraneous item in challenge folder : {item.name} \n\
									  [-] This does not conform to specification for a challenge folder")
					else:
						errorlogger("[-] ERROR! unecpected condition in _check_for_standard(), check the logfile ")
						raise Exception

			self.challengetype = "challenge"
			debuggreen("All Required files have been found in the specified folder")
		except:
			errorlogger(f"[-] Missing {validationlistlength} required item/s, Contents of folder: \n\t {valid_items}\n rejecting entry")
			errorlogger("[-] Failed to process challenge folder, check the logs")
			return False

	def lint_challenge_yaml(self, path_to_yaml:Path):
		'''
		Performs validation on the challenge.yaml file during folder processing
		'''
		
		#if validated_challenge_folder_contents_paths.get("deployment") is None:
					  
		# start the linter
		linter = Linter()
		# pick out the challenge yaml
		# instance a Yaml class
		challengeyaml = Yaml().loadyaml(path_to_yaml)
		#TODO:shitty hack to get things flowing properly
		# so far, the category folder has been the category name... but what if 
		# they are just tossing the wrong challenge in the wrong category?
		# here we replace the category name, fed to the function as the name of the folder
		# the challenge was residing in
		# with the category given in the challenge yaml

		#since it should only EVER be in a direct subfolder of a category folder
		# the except should NEVER be triggered so if it IS
		# SOMETHING is HORRIBLY wrong
		challengeyaml["category"] = path_to_yaml.parent.parent.stem

		# begin linting the file
		try:
			yamlcontents = linter.lintchallengeyaml(challengeyaml)
		except Exception:
			errorlogger("[-] Failure Linting challenge.yaml file!")
			pass
		return yamlcontents

	def _processfoldercontents(self, folderpath:Path)-> dict:
		"""
		Performs linting of challenge spec file and compresses the solution/handout folders

		Arguments are the following:
			folderpath:Path  folder path

		
		TODO: if category folder name does not match challenge category
			as given in yaml, reject or move to correct folder

		Returns the processed folder contents in the following format

		>>>	folderscanresults = {
		>>>		"category": category,
		>>>		 "type":challengetype,
		>>>		"yaml":yamlcontents,
		>>>		"folderdata" : {
		>>>			"handout":handout, 
		>>>			"solution": solution
		>>>		}
		>>>	}

		"""
		# allowance for commandline usage of follow up functions
		self.folder_being_scanned = folderpath
		#######################################################################
		# VALIDATION OF INDIVIDUAL CHALLENGES
		#######################################################################
		#extract the category name for shitty hack
		self.category = self.folder_being_scanned.parent.stem
		#====================================================================
		#   DEPLOYMENT PROCESSING
		#
		#====================================================================
		#if self.check_for_deployment(challengedirlist):
		if self._check_for_deployment(self.folder_being_scanned):
			debuggreen("Deployment Challenge Processed successfully")
		else:
		#====================================================================
		#  NON-DEPLOYMENT PROCESSING
		#====================================================================
			self._check_for_standard(self.folder_being_scanned)

		#######################################################################

		finalized_results = self._package_challenge()
		return finalized_results

	def _package_challenge(self):
		'''
		final step in validation, collates data into dict for feeding
		the Deployment() or Challenge() initializers
		'''
		try:
			folderscanresults = {
				"category": self.category,
				"type":self.challengetype,
				"yaml":self.yaml_contents,
				"folderdata" : {
					"handout":getattr(self,"handout", None),
					"solution": getattr(self,"solution",None)
				}
			}
		except Exception:
			errorlogger("[-] Failed to package challenge")

		# if its a deployed challenge, append the deployment folder to the dict
		if self.challengetype == "deployment":
			folderscanresults["folderdata"]["deployment"] = self.deployment_folder

		return folderscanresults

	def processdeploymentfolder(self,folderpath:Path)-> Path:
		'''
		Processes the contents of a deployment folder, inside a challenge folder 
		 Extracts the path of the dockerfile and deployment.yaml
		'''
		list_of_deployment_folder_files = [item.name for item in folderpath.iterdir() if item.is_file()]
		
		#list_of_deployment_folder_files = getsubfiles(folderpath)
		if "Dockerfile" not in list_of_deployment_folder_files:
			errorlogger("[-] Dockerfile not found! Skipping this folder!")
			raise Exception
		if "deployment.yml" not in list_of_deployment_folder_files:
			errorlogger("[-] deployment.yaml not found! Skipping this folder!")
			raise Exception
		if "service.yml" not in list_of_deployment_folder_files:
			errorlogger("[-] service.yaml not found! Skipping this folder!")
			raise Exception


	def _package_solution(self, path_to_folder:Path):
		'''
		packages the solution folder into a tar file for distribution
		'''
		# handout/solution is necessary
		# pack up solution
		try:
			debuggreen("Packaging solution to tarfile")
			self.solution = _processfoldertotarfile(folder = path_to_folder, 
											   filename = 'solution.tar.gz')
			debuggreen("Folder successfully packaged into tar file")
			
		except:
			errorlogger("[-] Failed to compress handout folder to tarfile")
			raise Exception

	def _package_handout(self, path_to_folder:Path):
		'''
		pack up handout folder into a tar file for distribution
		'''
		try: 
			debuggreen("Packaging handout to tarfile")
			self.handout  = _processfoldertotarfile(folder = path_to_folder, 
											   filename = 'handout.tar.gz')
			debuggreen("Folder successfully packaged into tar file")
		except:
			errorlogger("[-] Failed to compress handout folder to tarfile")
			raise Exception

	def _createdeployment(self, folderdata:dict[str,Path]) -> Deployment:
		"""
		Creates a DeploymentChallenge() from a challenge folder containing a dockerfile 
		or a kubernetes spec
		
		Uses the following json container schema
		folderscanresults = {
				"category": category,
				"type":challengetype,
				"yaml":yamlcontents,
				"folderdata" : {
					"deployment": deployment_folder_path,
					"service":"",
					"handout":handout, 
					"solution": solution
				}
			}
		"""
		# create the challenge in the repository
		newdeployment = Deployment(
				category = folderdata.get("category"),
				handout=  folderdata.get("folderdata")["handout"],
				solution=  folderdata.get("folderdata")["solution"],
				deployment = folderdata.get("folderdata")["deployment"],
				#service = folderdata.get("folderdata")["service"],
				#readme = folderdata.get("folderdata")['README']
				)
			#load the challenge yaml dict into the class
		newdeployment._initdeployment(**folderdata.get("yaml"))
		return newdeployment

	def _createchallenge(self, folderdata:dict) -> Challenge:
		'''
		Create a new Challenge() class based on the results of the folder scan
		if the folder scan was successful
		Args:
			folderscanresults (dict): representation of folder data
		'''
		# create the challenge in the repository
		newchallenge = Challenge(
				category = folderdata.get("category"),
				handout=  folderdata.get("folderdata")["handout"],
				solution=  folderdata.get("folderdata")["solution"],
				#readme = folderdata.get("folderdata")['README']
				)
			#load the challenge yaml dict into the class
		newchallenge._initchallenge(**folderdata.get("yaml"))
		return newchallenge
		# generate challenge based on folder contents

	def _setcategory(self, repo:Repository, category:Category):
		"""
		Adds a Category to the class
		We are adding classes to this class with "setattr"
		"""
		setattr(repo, category.name, category)
		
	def _getcategory(self,repo:Repository, category:str)-> Category:
		"""
		Returns The Category
		
		Args:
			repo (Repository) : Repository object created by masterlist
			category (str): the name of the category to return the challenges from
		
		Returns: 
		"""
		# for each item in class
		for selfmember in dir(repo):
			# if its a Category, and not a hidden class attribute or function
			if (type(selfmember) == Category):#in CATEGORIES) and (selfmember.startswith("__") != True):
				return getattr(repo,selfmember)
				

	def listcategories(self):
		"""
		Lists all categories
		"""
		selflist = vars(self)
		categorylist = []
		for item in selflist:
			if type(item) == Category:
				categorylist.append(item)

	def removecategory(self, category:str):
		"""
		Removes a category from the repository

		Args:

			category (str): Name of the category to unlink
		"""

	def addcategory(self, category:Path):
		"""
		Adds a Category to the repository

		Args:
			category (Path): path to category folder, in category level of repository
		"""		
		#TODO: add entry to masterlist.yaml

	def synccategory(self):
		"""
	Updates all challenges in CTFd with the versions in the repository
	Operates on the entire category 
		"""
		#call 
	
	def _listchallenges(self):
		"""
		Returns a list of all the installed challenges

		This is for local only, and is called by self.listchallenges()
		"""

	def listchallenges(self, ctfdurl, ctfdtoken, remote=False):
		"""
		NOT IMPLEMENTED YET

		Lists the challenges installed to the server
		Use 
		>>> --remote=False 
		to check the LOCAL repository
		For git operations, use `gitops` or your preferred terminal workflow

		Args:
			remote (bool): If True, Checks CTFd server for installed challenges
		"""
		if remote == True:
			self.setauth(ctfdurl,ctfdtoken)#,adminusername,adminpassword)
			apicall = APIHandler( ctfdurl, ctfdtoken)
			challenges = apicall.get(apicall._getroute('challenges', admin=True), json=True).json()["data"]
			print(challenges)
		elif remote == False:
			#self.listsyncedchallenges()
			pass

	def removechallenge(self):
		"""
		Removes a challenge from the repository
		Does not delete files, only unlinks
		"""

	def syncchallenge(self):
		"""
		
		"""
	def updaterepository(self, challenge):
		"""
	Updates the repository with any new content added to the category given
	if it doesnt fit the spec, it will issue an error	
	Try not to let your repo get cluttered
		"""
