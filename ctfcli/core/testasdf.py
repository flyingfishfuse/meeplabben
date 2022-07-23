validationdict = {
    #validationdict["standard"]
                "standard" :   [
                        "handout",
                        "solution",
                        "challenge.yaml",
                        #"README"
                        ],
                # if these exist, make a deployment instead
                #validationdict["deployment"]
                "deployment": [
                        "handout",
                        "solution",
                        "deployment"
                        "challenge.yaml",
                        #"README"
                        ]
}
for standard,deployment in validationdict["standard"],validationdict["deployment"]:
    print(f"standard : {standard}")
    print(f"deployment : {deployment}")
    