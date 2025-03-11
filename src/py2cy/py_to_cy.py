import sys
import py2cy
import platform
import configparser
import os,subprocess,glob
from distutils.core import setup
from Cython.Build import cythonize
from Cython.Distutils import build_ext
from configparser import NoSectionError
from distutils.extension import Extension
from shutil import ignore_patterns, copytree, rmtree
from py2cy.constants import BUILD_EXT

def main():
    
    sys.argv[1]=BUILD_EXT
    try:
        nthreads = 0
        # identify the platform where the script is getting executed
        platform_ = platform.system()
        # Reading properties file    
        config = configparser.RawConfigParser()
        config.read(py2cy.config_file_path)
        
        if platform_ == 'Linux':
            nthreads = int(config.get('NThreads', 'nThreads'))
        # source code path to be obfuscated
        pkg_for_obfuscation = config.get('SourcePath', 'pkg_for_obfuscation')
        pkg_for_obfuscation = pkg_for_obfuscation.replace('\\', '/')
        
        # creating a backup before obfuscation
        fromDirectory = pkg_for_obfuscation
        toDirectory = pkg_for_obfuscation + '_cython'
        if os.path.isdir(toDirectory):
            rmtree(toDirectory)
        copytree(fromDirectory, toDirectory, ignore=ignore_patterns('.git'))  
        
        # files and packages to be excluded/included for obfuscation
        files_to_exclude = list(filter(None, config.get('FilesToExclude', 'files_to_exclude').split(',')))
        pkgs_to_exclude = list(filter(None, config.get('PkgsToExclude', 'pkgs_to_exclude').split(',')))
        files_to_include = list(filter(None, config.get('FilesToInclude', 'files_to_include').split(',')))
        pkgs_to_include = list(filter(None, config.get('PkgsToInclude', 'pkgs_to_include').split(',')))
    
    except FileNotFoundError as e:
        raise FileNotFoundError('Check the Keys and values in the setup file') from e
    except NoSectionError as e:
        raise NoSectionError('Check the setup file for the key') from e
    except Exception as e:
        raise
    
    # This will override the values set for exclude condition to None
    if len(files_to_include) != 0 or len(pkgs_to_include) != 0:
        files_to_exclude = []
        pkgs_to_exclude = []
    
    
    def scansubdir(dir_):
        """Identifying the list of directories to cythonize"""
        '''should be recursive if there are submodules inside modules'''
        subdirs = []
        for f in os.listdir(dir_):
            p = os.path.join(dir_, f)
            if f is not None and os.path.isdir(p) and not f.startswith('.')\
            and not f.startswith('__'):
                subdirs.append(p.replace(os.path.sep, '.'))
        return subdirs
    
    
    # This execution is not mandatory
    subdirs = scansubdir(toDirectory)
    
    
    def scandir(dir_, files=[]):
        """Identifying the list of files to cythonize"""
        for f in os.listdir(dir_):
            if f == '__init__.py' or f in files_to_exclude or f in pkgs_to_exclude:
                continue
            p = os.path.join(dir_, f)
            
            if include_file_flag:
                file_flag = True
            else:
                file_flag = True if f in files_to_include else False 
                        
            if os.path.isfile(p) and p.endswith('.py') and file_flag:
                files.append(p.replace(os.path.sep, '.')[:-3])
            elif os.path.isdir(p):
                scandir(p, files)
        return files
    
     
    def make_extension(ext_name):
        """creating extension which is used to cythonize"""
        ext_set_name = ext_name.replace('.', os.path.sep)
        ext_path = ext_set_name + '.py'
        
        if platform_ == 'Windows':
            ext_set_name = ext_name
            
        return Extension(
            ext_set_name,
            [ext_path],
        )
    
        
    def scandir_include(dir_, files=[]):
        """Identifying the list of files to cythonize"""
        for f in os.listdir(dir_):
            if f == '__init__.py':
                continue
            p = os.path.join(dir_, f) 
            if os.path.isfile(p) and p.endswith('.py'):
                compare_list = p.partition('_cython')[2]
                compare_list = compare_list.replace('\\', '/').lstrip('/').split('/')
                if any(e in pkgs_to_include for e in compare_list):
                    _, file = os.path.split(p)
                    files.append(file)
            elif os.path.isdir(p):
                scandir_include(p, files)
        return files
    
    
    # flag to determine the packages to include to cythonize 
    include_dir_flag = True if len(pkgs_to_include) == 0 else False 
    
    # identify the files in the given packages to append with files_to_include list
    if not include_dir_flag:    
        dir_files = scandir_include(toDirectory)
        files_to_include.extend(dir_files)
        
    # flag to determine the files to include to cythonize 
    include_file_flag = True if len(files_to_include) == 0 else False
    
    # list of files to cythonize
    extNames = scandir(toDirectory)
    extensions = [make_extension(name) for name in extNames]
    c_extension = ','.join([e.sources[0] for e in extensions])
    ext_files = c_extension.split(",")
    c_extension = tuple(c_extension.split(","))
    
    cythonize(c_extension, nthreads=nthreads)
    setup(
        name=toDirectory,
        packages=subdirs,
        cmdclass={BUILD_EXT: build_ext},
        ext_modules=extensions
    )
    
    # Intermediate files to be deleted
    for file_ in ext_files:
        print(file_)
        os.remove(file_)
        os.remove(file_.replace('.py', '.c'))
        if platform_ == 'Linux':
            subprocess.check_call(['strip','-s']+ glob.glob(file_.replace('.py', '.*.so')))
            #os.system('strip -s ' + file_.replace('.py', '.*.so'))
    
    # build folder to be deleted if present
    build_dir = os.path.join(os.getcwd(), 'build')
    if os.path.exists(build_dir):
        rmtree(build_dir)        
        sys.exit(0)
    sys.exit(0)