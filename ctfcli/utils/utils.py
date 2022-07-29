from genericpath import isdir
import sys
import yaml
import os
import pathlib
import logging
import traceback
import tarfile
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


#this is where everything is defined, the structure of the repo folders
validationdict = {
            "standard":["handout","solution","challenge.yaml", "README"],
            # if these exist, make a deployment instead
            "deployment": ["deployment","Dockerfile","metadata.yaml","README"]
    }
###############################################
# returns subdirectories , without . files/dirs
# name of the yaml file expected to have the challenge data in each subfolder
basechallengeyaml   = "challenge.yml"


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
challengeyamlbufferr = lambda category,challenge: open(os.path.join(category,challenge,basechallengeyaml),'r')
# open with write operation
challengeyamlbufferw = lambda category,challenge: open(os.path.join(category,challenge,basechallengeyaml),'r')
#loads a challenge.yaml file into a buffer
loadchallengeyaml =  lambda category,challenge: yaml.load(challengeyamlbufferr(category,challenge), Loader=yaml.FullLoader)
writechallengeyaml =  lambda category,challenge: yaml.load(challengeyamlbufferw(category,challenge), Loader=yaml.FullLoader)
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


def _processfoldertotarfile(folder:Path,filename='default')-> tarfile.TarFile:
    '''
    creates a tarfile of the provided folder 
    if a tarfile already exists, it simply returns that
    '''
    try:
        dirlisting = [item for item in Path(folder).glob('**/*')]
        #for each in dirlisting:
        #    if each.stem == ".gitignore":
        # folder is not empty
        if len(dirlisting) != 0:
                # first, scan for the file.tar.gz
                for item in dirlisting:
                    # if its a hidden file
                    if item.stem.startswith("."):# == ".gitignore":
                        continue
                    # if its a file without an extension
                    if len(item.suffixes) == 0 and item.is_file():
                        continue
                    # a directory
                    if item.is_dir():
                        continue
                    # if its named filename.tar.gz
                    elif item.suffixes[0] == '.tar' and item.suffixes[1] == '.gz' and item.stem == filename:
                        #return TarFile.open(item,"r:gz",item)
                        return item
                    #else:
                    #    continue
                # if its not there, create archive and add all files
                newtarfilepath = Path(folder,filename)
                with tarfile.open(newtarfilepath, "w:gz") as tar:
                    for item in dirlisting:
                        if item.is_dir():
                            tar.add(item)
                        else:
                            tar.addfile(tarfile.TarInfo(item.name), open(item))
                tar.close()
                return newtarfilepath
        elif len(dirlisting) == 0:
            #TODO: add manual tar upload to challenge by name
            yellowboldprint(f"[?] No files in {folder} Folder. This must be uploaded manually if its a mistake")
            # cheat code for exiting a function?
            return None
        else:
            redprint("[-] Something WIERD happened, throw a banana and try again!")
            raise Exception
    except Exception as e:
        errorlogger(f'[-] Could not process challenge: {e}')
