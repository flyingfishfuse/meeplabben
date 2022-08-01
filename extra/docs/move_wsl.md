
If you want to move WSL2 Linux distro from C: drive

    mkdir F:\WSL2_debian\

export Debian

    wsl --export Debian F:\WSL2_debian\debian.tar

Unregister the same distribution to remove it from the C: drive:

    wsl --unregister Debian

Import Debian

    mkdir F:\WSL2_Debian\

    wsl --import Debian D:\WSL2_Debian\ F:\WSL2_Debian\debian.tar

By default Debian will use root as the default user, to switch back to previous user

Go to the Debian App Folder run command to set default user

    cd %userprofile%\AppData\Local\Microsoft\WindowsApps
    
    Debian config --default-user <username>