#!/usr/bin/env python
import os
import sys
import py2cy
import subprocess
from pathlib import Path
from py2cy import py_to_cy
from py2cy.constants import BUILD_EXT


def main():
    
    """This method gets called when py2cy is triggered, 
    purpose of this method is to identify the action and perform cython file creation"""
    
    try:
        subcommand = sys.argv[1]
        
        if "help" in subcommand:
            return ("""
                ---------------------------------------------------------------
                * Use any one of the below command for initiating cythonization
                
                1. py2cy <<absolute path of the setup.cfg>>
                2. py2cy from the directory where setup.cfg is present
                ---------------------------------------------------------------
                """)
        
        if "setup.cfg" not in subcommand.lower():
                return "ERROR!!!!! Absolute path of the setup.cfg must be provided"
        
        if Path(subcommand).is_file():
            pass
        else:
            return "ERROR!!!!! Path of the setup.cfg is incorrect"
    except IndexError:
        subcommand = f"{os.getcwd()}/setup.cfg"
        if not Path(subcommand).is_file():
            return "ERROR!!!!! Current working directory doesnt have setup.cfg file"

    py2cy.config_file_path=subcommand
    subprocess.run([py_to_cy.main(),BUILD_EXT])
