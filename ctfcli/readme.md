This tool 

I just forked the ctfcli repo to start reviewing the changes I can implement but the structure of the rewrite required some engineering changes, I need you to review the changes that I made for my own project to choose what should be merged. The rewrite is in the repository "flyingfishfuse/ctf_repository_manager" in the "ctfcli" folder.

I see you just started refactoring to a more OOP approach which is what I did. I wanted it to be modular and extensible. The documentation needs more work but it's mostly done. I am going to be spending the next few days reading the newest version of ctfcli to see how the structure changed. My version is explained in the readme of the main folder.... I *think* it works still but I may have made a few changes without testing when everything was hectic in my personal life.

I stopped coding for a while to focus on other areas of my life but I am needing to get back in to the game. 

The most important changes is the challenges repository MUST fit a SPECIFIC form, and the challenge.yaml MUST conform to the specification or it will be denied. I have reformatted a total of two years worth of challenges meant for the ctfd platform as an example. I am sure a script could be written to reformat other challenge repositories. 
The software also creates a "masterlist" consisting of python->yaml of the challenge repo that can be loaded into the tool.

#### Necessary Packages

    gitpython, docker-compose, python-docker, fire, cookiecutter
    pyyaml, Pygments, colorama, dotenv

#### usage

    - perform setup and create an admin account on CTFd before running this tool

    - You must set the url of the CTFd server in the config.cfg

        FIRST RUN, If you have not modified the repository this is not necessary!
        This will generate a Masterlist.yaml file that contains the contents of the 
        repository for loading into the program
        
        >>> host@server$> python ./ctfcli/ ctfcli init

#### Authentication

        you should provide token and url when running the tool, it will store 
        token only for a limited time. This is intentional and will not be changed
        This tool is capable of getting its own tokens given an administrative username and password

        for SINGLE operations, with NO authentication persistance:
        
        >>> host@server$> python ./ctfcli/ ctfcli --ctfdurl <URL> --ctfdtoken <TOKEN>

        for multiple operations, WITH authentication persistance:
        This configuraiton will be able to obtain tokens via CLI
        This is not advised if you are not using a cloud provider for the deployment
        
        >>> host@server$> python ./ctfcli/ ctfcli --adminusername moop --adminpassword password

#### To sync repository contents to CTFd Server:
        
        >>> host@server$> python ./ctfcli/ ctfcli syncrepository --ctfdurl <URL> --ctfdtoken <TOKEN>

        Replacing <URL> with your CTFd website url
        and replacing <TOKEN> with your CTFd website token
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

# Development criteria

### To generate Documentation:

    We use sphinx with google docstrings currently

    cd $DATAROOT/CTFd
    sphinx-apidoc.exe -f -o source ctfcli
    make html

### Challenges

    Challenge folders must contain a challenge.yaml file and "handout" and "solution" folders

### handouts and solutions

    Handouts and solutions should be in a folder named "handout" or "solution" 

    Handouts will be tar'd and gzipped if they are not already
        - if there is a single file, it will be uploaded as is
        - if there is a group of files, they will be put in a tar.gz archive
    
    Solutions must be complete-ish enough to teach how to do the thing
        - If there is a single file, it must be either a solution.md file or .tar.gz


## Creating a Dcoumentation Github Repo

    In ~/sandboxy/data/CTFD
        
        git init
        git add .
        <upload to git>
        lol

## Make a remote repository

    echo "# sandboxy_cods" >> README.md
    git init
    git add README.md
    git commit -m "first commit"
    git branch -M main
    git remote add origin https://github.com/mister-hai/sandboxy_docs.git
    git push -u origin main
