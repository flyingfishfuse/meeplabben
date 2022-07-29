# meeplabben
ctf manager and deployer

# Hierarchical overview of repository

1. `masterlist.yaml` MUST be at the top of the hierarchy in the `/PROJECT_ROOT/data` folder

2. A challenge is structured as thus:

        Challenge_Category/                     (required, any name allowed)
        ├── standard_challenge_name/            (required, any name allowed)
        │   ├── challenge.yaml                  (required, yaml extension important)      
        │   ├── handout/                        (optional)
        │   └── solution/                       (optional)
        |
        ├── deployed_challenge_name/            (required, any name allowed)
        │   ├── challenge.yaml                  (required, yaml extension important)      
        │   ├── deployment/                     (required, capitalization important)
        |   |   ├── service.yml                 (required, yml extension important)
        |   |   ├── deployment.yml              (required, yml extension important)
        |   |   ├── Dockerfile                  (required, capitalization important)
        |   |   └── Deployment_data_folder/     (optional, any name allowed)
        │   ├── handout/                        (optional)
        │   └── solution/                       (optional)

#### THE CATEGORY OF THE CHALLENGE WILL REFLECT THE FOLDER IT RESIDES IN IF THE CATEGORY FOLDER IS "CRYPTO", THE CATEGORY TAG IN CHALLENGE.YAML  WILL CHANGE TO "CRYPTO", This will not change any time soon!
####
<br>

3. deployed challenges MUST have a folder named 

        deployment

4. this folder named "deployment" MUST have the `service.yaml `and `metadata.yml` AND `Dockerfile`, all software to be exploited MUST be in a subfolder

5. deployed challenges can be blackbox, i.e. no solution or handout

# Instructions!

## to initialize a new repository:
    
1. place challenges, organized by category into /data/challenges

2. run the command:

        python3 ./cli ctfrepo init


## To run the default repository

1. navigate to the project folder in a bash terminal (start.sh is BASH script, incompatible with FISH)

2. run the start.sh script and choose 
        
        init cluster

3. choose the option

        run meeplabben
    
4. The UI should be running on localhost now (127.0.0.1:8000/ctf)

## To deploy challenge containers

1. 
