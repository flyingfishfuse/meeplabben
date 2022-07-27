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
		dictofcategories = {}
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
				dictofcategories[newcategory.name] = newcategory
		# for each category folder in the repository folder
		for category in dictofcategories.copy().values():
			# process through validation
			processedcategory = self._processcategory(category)
			dictofcategories.update(processedcategory)
		# assign all categories to repository class
		# using protoclass + dict expansion
		newrepo = Repository(**dictofcategories)
		# return this class to the upper level scope
		return newrepo

	def _processcategory(self,category:Category)-> Category:
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
		#get subfolder names in category directory
		#categoryfolder = getsubdirs(newcategory.location)
		# itterate over the individual challenges
		for challengefolder in category.dirlisting:
			# each in its own folder, name not required
			challengefolderpath = Path(self.challenges_folder,category.name, challengefolder)
			debuggreen(f"Found folder {challengefolderpath.name}")
			debugyellow(f'{challengefolderpath}')
			try:
				# load yaml and scan folder
				folderscanresults = self._processfoldercontents(challengefolderpath)
				if folderscanresults["type"] == "deployment":
					self._createdeployment(folderscanresults)
				elif folderscanresults["type"] == "challlenge":
					# create Challenge based off those
					newchallenge = self._createchallenge(folderscanresults)

				#assign challenge to category
				#newcategory._addchallenge(newchallenge)
				category._addchallenge(newchallenge)

			except Exception:
				errorlogger('[-] Error Creating Challenge!')
				continue
		return category

	def check_for_deployment(self,directory_list:list)->bool:
		'''
		Checks if challenge is a deployed challenge, if not, performs better validation
		in the next step
		
		'''
		#dirlisting = getsubdirs(directory)
		expanded_list = [name.stem for name in directory_list]
		if "deployment" in expanded_list:
			return True
		else:
			debugred("\"deployment\" folder not found, presuming to be standard challenge")
			return False

	def check_for_standard(self,list_of_items):
		'''
		checks if challenge is standard, non-deployed challenge

		'''
		truthyness = bool
		valid_items = []
		validationlist =[
						"handout",
						"solution",
						"challenge.yaml",
						#"README"
						]
		validationlistlength = len(validationlist)
		for item in list_of_items:
			if item in validationlist:
				truthyness = True
				# let the truthyness variable be set/remain as true
				debuggreen(f"[+] Found Valid Item {item}")
				valid = True
				# remove the item from the validation list
				#validdatalist.remove(item)
				valid_items.append(item)
			if item not in validationlist:
				truthyness = False
				debugyellow(f"[-] Found Extraneous item in challenge folder : {item} \n\
							  [-] This does not conform to specification for a challenge folder and in \n\
							  [-] future versions will raise an error and the folder will not be processed")

		if len(valid_items) == validationlistlength:
			debuggreen("[+] All Required files have been found in the specified folder")
			return truthyness
		else:
			errorlogger(f"[-] Missing {validationlistlength} required item/s, Contents of folder: \n\t {valid_items}\n rejecting entry")
			return False

	def validate_folder_contents(self,folder_contents):
		'''
		Validates the folder supplied
		'''

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
		#extract the category name for shitty hack
		category = folderpath.parent.stem
		#######################################################################
		# VALIDATION OF INDIVIDUAL CHALLENGES
		#######################################################################
		# begin scanning and if necessary, file parsing
		# to create new Challenge() or Deployment() class's from folder contents
		challenge_folder_contents_paths = {}
		# get directory listing of challenge folder
		folders_in_challenge_directory = getsubdirs(folderpath)
		challengedirlist = os.listdir(os.path.normpath(folderpath))
		# get the paths
		for item in challengedirlist:
			# get the path
			itempath = Path(os.path.abspath(os.path.join(folderpath,item)))
			# assign paths to dict as {filename:path}
			challenge_folder_contents_paths[str(itempath.stem).lower()] =  itempath

		#====================================================================
		#   DEPLOYMENT PROCESSING
		#====================================================================
		#if self.check_for_deployment(challengedirlist):
		if self.check_for_deployment(folders_in_challenge_directory):
			# this needs to be created to pass information down the chain
			challengetype = "deployment"
			debuggreen("[+] Deployment Challenge Processing")
			# begin processing the contents of deployment folder
			deployment_folder = challenge_folder_contents_paths.pop("deployment")
			try:
				self.processdeploymentfolder(deployment_folder)
			except Exception:
				errorlogger("[-] Failed to process this challenge, skipping!")

			# handout is not necessary, but suggested
			#debuggreen("[+] Deployment handout folder compressing to tarfile")
			#try:
			#	solution = _processfoldertotarfile(folder = challenge_folder_contents_paths.pop('handout'), 
			#										filename = 'solution.tar.gz')
			#except:
			#	errorlogger("[-] Failed to compress handout folder to tarfile")
			#	raise Exception
			
			#debuggreen("[+] Deployment solution folder compressing to tarfile")
			#try:
			#	handout  = _processfoldertotarfile(folder = challenge_folder_contents_paths.pop('solution'), 
			#										   filename = 'handout.tar.gz')
			#except:
			#	errorlogger("[-] Failed to compress solution folder to tarfile")
			#	raise Exception
			#else:
			#	yellowboldprint("[?] No handout material given in deployed challenge, presuming blackbox testing?") 

		#====================================================================
		#  NON-DEPLOYMENT PROCESSING
		#====================================================================
		elif self.check_for_standard(challengedirlist):
			challengetype = "challenge"
			debuggreen("[+] Standard Challenge processing")
			# handout/solution is necessary
			# pack up solution
			try:
				solution = _processfoldertotarfile(folder = challenge_folder_contents_paths.pop('handout'), 
												filename = 'solution.tar.gz')
			
			except:
				errorlogger("[-] Failed to compress handout folder to tarfile")
				raise Exception
			# pack up handout  
			try: 
				handout  = _processfoldertotarfile(folder = challenge_folder_contents_paths.pop('solution'), 
												filename = 'handout.tar.gz')
			except:
				errorlogger("[-] Failed to compress handout folder to tarfile")
				raise Exception
		else:
			errorlogger("[-] Something strange happened, throw a banana and try again?")
			raise Exception
		#######################################################################
		# POST VALIDATION FOLDER PROCESSING
		#######################################################################

		#if validated_challenge_folder_contents_paths.get("deployment") is None:
					  
		# start the linter
		linter = Linter()
		# pick out the challenge yaml
		# instance a Yaml class
		challengeyaml = Yaml().loadyaml(challenge_folder_contents_paths.pop("challenge"))
		# lint the challenge
		#TODO:shitty hack to get thins flowing properly
		# when everything is modified finally this can get removed
		# so far, the category folder has been the category name... but what if 
		# they are just tossing the wrong challenge in the wrong category?
		# here we replace the category name, fed to the function as the name of the folder
		# the challenge was residing in
		# with the category given in the challenge yaml
		#challengeyaml.update({"category": category})
		challengeyaml["category"] = category
		try:
			yamlcontents = linter.lintchallengeyaml(challengeyaml)
		except Exception:
			errorlogger("[-] Failure Linting Challenge yaml files")
			pass
		folderscanresults = {
			"category": category,
			"type":challengetype,
			"yaml":yamlcontents,
			"folderdata" : {
				#"service":"",
				"handout":handout, 
				"solution": solution
			}
		}
		# if its a deployed challenge, append the deployment folder to the dict
		if challengetype == "deployment":
			folderscanresults["folderdata"]["deployment"] = deployment_folder

		return folderscanresults

	def processdeploymentfolder(self,folderpath:Path)-> Path:
		'''
		Processes the contents of a deployment folder, inside a challenge folder 
		 Extracts the path of the dockerfile and deployment.yaml
		'''
		list_of_deployment_folder_files = getsubfiles(folderpath)
		if "Dockerfile" not in list_of_deployment_folder_files:
			errorlogger("[-] Dockerfile not found! Skipping this folder!")
			raise Exception
		if "deployment.yaml" not in list_of_deployment_folder_files:
			errorlogger("[-] deployment.yaml not found! Skipping this folder!")
			raise Exception
		if "service.yaml" not in list_of_deployment_folder_files:
			errorlogger("[-] service.yaml not found! Skipping this folder!")
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
