#!/usr/bin/python

from threading import Thread
import datetime
import os
import re
import shutil
import socket
import sys
import time
import types

import pkgutil


# initialize the socket callback interface so we have it
# available..
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind((socket.gethostname(), pkgutil.PORT_CREATOR))
serversocket.listen(16)



class Options:
    def __init__(self):
        self.qtVersion = None
        self.packageRoot = None
        self.qtJambiVersion = "4.4.0_01"
        self.p4User = "qt";
        self.p4Client = "qt-builder";
options = Options()



class Package:
    def __init__(self, platform, arch, license):
        self.license = license
        self.platform = platform
        self.arch = arch
        self.binary = False
        self.removeDirs = [
            "ant", 
            "autotestlib",
            "com/trolltech/autotests",
            "com/trolltech/benchmarks",
            "com/trolltech/extensions",
            "com/trolltech/manualtests",
            "com/trolltech/tests",
            "cpp",
            "dist",
            "doc/config",
            "doc/src",
            "launcher_launcher",
            "libbenchmark",
            "scripts",
            "tools",
            "whitepaper"
            ]
        self.removeFiles = [
            ]
        self.removePatterns = [
            re.compile("CRT"),
            re.compile("Makefile$"),
            re.compile("Makefile.Debug$"),
            re.compile("Makefile.Release$"),
            re.compile("\\.a$"),
            re.compile("\\.class$"),
            re.compile("\\.debug$"),
            re.compile("\\.exp$"),
            re.compile("\\.ilk$"),
            re.compile("\\.lib$"),
            re.compile("\\.log$"),
            re.compile("\\.manifest$"),
            re.compile("\\.o$"),
            re.compile("\\.obj$"),
            re.compile("\\.pch$"),
            re.compile("\\.pdb$"),
            re.compile("\\[\\/]debug$"),
            re.compile("\\[\\/]release$"),
            re.compile("\\_debuglib\\."),
            re.compile("com_trolltech.*\\.lib$"),
            re.compile("task(.bat)?$")
            ]
        self.mkdirs = [
            "include"
            ]
        self.copyFiles = [
            # Include files...
            ["qtjambi/qtjambi_core.h", "include"],
            ["qtjambi/qtjambi_cache.h", "include"],
            ["qtjambi/qtjambi_global.h", "include"],
            ["qtjambi/qtjambilink.h", "include"],
            ["qtjambi/qtjambifunctiontable.h", "include"],

            # text files for main directory...
            "dist/readme.html",
            "dist/install.html",
            "dist/changes-" + options.qtJambiVersion
            ]
        self.licenseHeader = readLicenseHeader(self.license)

        if self.license == pkgutil.LICENSE_COMMERCIAL:
            self.setCommercial()
        elif self.license == pkgutil.LICENSE_EVAL:
            self.setEval()
        elif self.license == pkgutil.LICENSE_GPL:
            self.setGpl()
        else:
            raise "bad license type:" + self.license
        

    def setBinary(self):
        self.binary = True

    def setMacBinary(self):
        self.setBinary()
        self.copyFiles.append("dist/mac/qtjambi.sh")
        self.copyFiles.append("dist/mac/designer.sh")
        self.compiler = "gcc"
        self.make = "make"
        self.platformJarName = "qtjambi-macosx-gcc-" + options.qtJambiVersion + ".jar"

    def setWinBinary(self):
        self.setBinary()
        self.copyFiles.append("dist/win/designer.bat")
        if self.arch == pkgutil.ARCH_64:
            self.copyFiles.append(["dist/win/qtjambi64.exe", "qtjambi.exe"])
            self.platformJarName = "qtjambi-win64-msvc2005x64-" + options.qtJambiVersion + ".jar"
        else:
            self.copyFiles.append("dist/win/qtjambi.exe")
            self.platformJarName = "qtjambi-win32-msvc2005-" + options.qtJambiVersion + ".jar"
            
        if self.license == pkgutil.LICENSE_GPL:
            self.compiler = "mingw"
            self.make = "mingw32-make"
        else:
            self.compiler = "msvc2005"
            self.make = "nmake"
        self.removeDirs.append("lib")
        self.copyFiles.append(["generator/release/generator.exe", "bin"])        

    def setLinuxBinary(self):
        self.setBinary()
        self.copyFiles.append("dist/linux/designer.sh")
        self.copyFiles.append("dist/linux/qtjambi.sh")
        self.compiler = "gcc"
        self.make = "make"
        if self.arch == pkgutil.ARCH_64:
            self.platformJarName = "qtjambi-linux64-gcc-" + options.qtJambiVersion + ".jar"
        else:
            self.platformJarName = "qtjambi-linux32-gcc-" + options.qtJambiVersion + ".jar"

    def setCommercial(self):
        self.copyFiles.append("dist/LICENSE")

    def setGpl(self):
        self.copyFiles.append("dist/LICENSE.GPL")

    def setEval(self):
        self.copyFiles.append("dist/LICENSE.EVAL")

    def name(self):
        arch = self.arch
        if self.arch == pkgutil.ARCH_UNIVERSAL:
            arch = ""
        return "qtjambi-" + self.platform + arch + "-" + self.license + "-" + options.qtJambiVersion;

    def writeLog(self, list, subname):
        logName = os.path.join(options.packageRoot, ".%s.%s" % (self.name(), subname))
        pkgutil.debug("   - log into: " + logName)
        log = open(logName, "w")
        log.write("\n".join(list))
        log.close()
        
packages = []



# Reads the license header from /dist/license_....txt and returns it
def readLicenseHeader(license):
    if license == pkgutil.LICENSE_GPL:
        name = "gpl_header.txt"
    elif license == pkgutil.LICENSE_EVAL:
        name = "eval_header.txt"
    elif license == pkgutil.LICENSE_COMMERCIAL:
        name = "commercial_header.txt"
    name = "%s/../dist/%s" % (options.startDir, name)
    file = open(name, "r")
    content = file.read()
    file.close()
    return content



# Sets up all the various packages to be built into the global
# variable "packages"
def setupPackages():

    if options.buildWindows:
        if options.build64:
            if options.buildCommercial:
                win64 = Package(pkgutil.PLATFORM_WINDOWS, pkgutil.ARCH_64, pkgutil.LICENSE_COMMERCIAL)
                win64.setWinBinary()
                win64.buildServer = "aeryn.troll.no"
                packages.append(win64)

    if options.buildMac:
        if options.buildCommercial:
            macMoney = Package(pkgutil.PLATFORM_MAC, pkgutil.ARCH_UNIVERSAL, pkgutil.LICENSE_COMMERCIAL)
            macMoney.setMacBinary()
            macMoney.buildServer = "lyta.troll.no"
            packages.append(macMoney)
        if options.buildGpl:
            macGpl = Package(pkgutil.PLATFORM_MAC, pkgutil.ARCH_UNIVERSAL, pkgutil.LICENSE_GPL)
            macGpl.setMacBinary()
            macGpl.buildServer = "lyta.troll.no"
            packages.append(macGpl)
        if options.buildEval:
            macEval = Package(pkgutil.PLATFORM_MAC, pkgutil.ARCH_UNIVERSAL, pkgutil.LICENSE_EVAL)
            macEval.setMacBinary()
            macEval.buildServer = "lyta.troll.no"
            packages.append(macEval)

    if options.buildLinux:
        if options.buildCommercial:
            linuxMoney = Package(pkgutil.PLATFORM_LINUX, pkgutil.ARCH_UNIVERSAL, pkgutil.LICENSE_COMMERCIAL)
            linuxMoney.setLinuxBinary()
            linuxMoney.buildServer = "haavard.troll.no"
            packages.append(linuxMoney)
        if options.buildGpl:
            linuxGpl = Package(pkgutil.PLATFORM_LINUX, pkgutil.ARCH_UNIVERSAL, pkgutil.LICENSE_GPL)
            linuxGpl.setLinuxBinary()
            linuxGpl.buildServer = "haavard.troll.no"
            packages.append(linuxGpl)
        if options.buildEval:
            linuxEval = Package(pkgutil.PLATFORM_LINUX, pkgutil.ARCH_UNIVERSAL, pkgutil.LICENSE_EVAL)
            linuxEval.setLinuxBinary()
            linuxEval.buildServer = "haavard.troll.no"
            packages.append(linuxEval)

    




# Sets up the client spec and performs a complete checkout of the
# tree...
def prepareSourceTree():

    # remove and recreat dir and cd into it...
    shutil.rmtree(options.packageRoot)
    os.makedirs(options.packageRoot)
    os.chdir(options.packageRoot)

    # set up the perforce client...
    tmpFile = open("p4spec.tmp", "w")
    tmpFile.write("Root: %s\n" % (options.packageRoot))
    tmpFile.write("Owner: %s\n" % options.p4User)
    tmpFile.write("Client: %s\n" % options.p4Client)
    tmpFile.write("View:\n")
    tmpFile.write("        //depot/qtjambi/%s/...  //qt-builder/qtjambi/...\n" % options.qtJambiVersion)
    tmpFile.close()
    os.system("p4 -u %s -c %s client -i < p4spec.tmp" % (options.p4User, options.p4Client) );
    os.remove("p4spec.tmp")

    # sync p4 client spec into subdirectory...
    pkgutil.debug(" - syncing p4...")
    os.system("p4 -u %s -c %s sync -f //%s/... > .p4sync.buildlog" % (options.p4User, options.p4Client, options.p4Client))



# Creates the build script (.bat or .sh), zips up the file and sends it off to the
# build server
def packageAndSend(package):
    pkgutil.debug("packaging and sending: %s..." % package.name())
    
    os.chdir(options.packageRoot)

    if os.path.isdir("tmptree"):
        shutil.rmtree("tmptree")
        
    shutil.copytree("qtjambi", "tmptree");

    pkgutil.debug(" - creating task script")
    if package.platform == pkgutil.PLATFORM_WINDOWS:
        buildFile = open("tmptree/task.bat", "w")
        buildFile.write("call qt_pkg_setup %s %s %s\n" % (package.compiler, options.qtVersion, package.license))
        buildFile.write("call ant\n")
        buildFile.write(package.make + " clean\n")
    else:
        buildFile = open("tmptree/task.sh", "w")
        buildFile.write("qt_pkg_setup %s %s %s\n" % (package.compiler, options.qtVersion, package.license))
        buildFile.write("ant\n")
        buildFile.write(package.make + " clean \n")
    buildFile.close()
                        
    zipFile = os.path.join(options.packageRoot, "tmp.zip")
    pkgutil.debug(" - compressing...")
    pkgutil.compress(zipFile, os.path.join(options.packageRoot, "tmptree"))
    pkgutil.debug(" - sending %s to host: %s.." % (package.name(), package.buildServer))
    pkgutil.sendDataFileToHost(package.buildServer, pkgutil.PORT_SERVER, zipFile)



# performs the post-compilation processing of the package
def postProcessPackage(package):
    pkgutil.debug("Post process package " + package.name())

    pkgutil.debug(" - uncompressing...")
    package.packageDir = options.packageRoot + "/" + package.name()
    pkgutil.uncompress(package.dataFile, package.packageDir);

    os.chdir(package.packageDir)

    if os.path.isfile("FATAL.ERROR"):
        print "\nFATAL ERROR on package %s" % (package.name())
        return;

    shutil.copy(package.packageDir + "/.task.log", options.packageRoot + "/." + package.name() + ".tasklog");

    pkgutil.debug(" - creating directories...")
    for mkdir in package.mkdirs:
        os.makedirs(mkdir)
    
    pkgutil.debug(" - copying files around...")
    copyFiles(package)
    
    pkgutil.debug(" - deleting files and directories...")
    removeFiles(package)

    # unjar docs into doc directory...
    pkgutil.debug(" - doing docs...")
    os.makedirs("doc/html")
    os.chdir("doc/html")
    os.system("jar -xf %s/qtjambi-javadoc-%s.jar" % (options.startDir, options.qtJambiVersion) )
    os.chdir(package.packageDir)

    expandMacroes(package)

    # unpack the platform .jar to get the correct binary content into
    # the package...
    os.system("jar -xf %s" % package.platformJarName)
    shutil.rmtree("%s/META-INF" % package.packageDir)

    bundle(package)



# Zips or tars the final content of the package into a bundle in the
# users root directory...
def bundle(package):
    if package.platform == pkgutil.PLATFORM_WINDOWS:
        pkgutil.compress("%s/%s.zip" % (options.startDir, package.name()), package.packageDir)
    else:
        os.system("tar -czf %s/%s.tar.gz %s" % (options.startDir, package.name(), package.packageDir))
    


# Locates all text files and expands the $LICENSE$ macroes and similar
# located in them
def expandMacroes(package):
    thisYear = "%d" % datetime.date.today().year
    patterns = [
        [ re.compile("\\$THISYEAR\\$"), thisYear ],
        [ re.compile("\\$TROLLTECH\\$"), "Trolltech ASA" ],
        [ re.compile("\\$PRODUCT\\$"), "Qt Jambi" ],
        [ re.compile("\\$LICENSE\\$"), package.licenseHeader ],
        [ re.compile("\\$CPP_LICENSE\\$"), package.licenseHeader ],
        [ re.compile("\\$JAVA_LICENSE\\$"), package.licenseHeader ]
        ]
    extensions = [
        re.compile("\\.cpp$"),
        re.compile("\\.h$"),
        re.compile("\\.java"),
        re.compile("\\.html"),
        re.compile("\\.ui"),
        re.compile("LICENSE")
        ]
    for (root, dirs, files) in os.walk(package.packageDir):
        for relfile in files:
            file = os.path.join(root, relfile)
            replace = False
            for ext in extensions:
                if ext.search(file):
                    replace = True
            if replace:
                handle = open(file, "r")
                content = handle.read()
                handle.close()
                check = False
                for (regex, replacement) in patterns:
                    content = re.sub(regex, replacement, content)
                handle = open(file, "w")
                handle.write(content)
                handle.close()



# Moves the package content around, such as copying the license files
# from dist etc. This is mostly specified the variable moveFiles in
# the package object.
def copyFiles(package):
    copylog = []
    for m in package.copyFiles:
        if isinstance(m, types.ListType): 
            (source, target) = m;
            shutil.copy(source, target);
            copylog.append("%s -> %s" % (source, target))
        else:
            shutil.copy(m, package.packageDir)
            copylog.append("%s -> root" % m)
    package.writeLog(copylog, "copylog");



# Removing all the unwanted content... The package contains two variables,
# removeDirs and removeFiles which are used to kill content. removeDirs is removed
# recursivly and brutally. In addition to the predefined content, we search for a number
# of regexp patterns and remove that content too.
def removeFiles(package):
    for (root, dirs, files) in os.walk(package.packageDir, False):
        for pattern in package.removePatterns:
            for relfile in files:
                file = os.path.join(root, relfile)
                if pattern.search(file):
                    package.removeFiles.append(file)
            for reldir in dirs:
                dir = os.path.join(root, reldir)
                if pattern.search(dir):
                    package.removeDirs.append(dir)

    rmlist = [];
    for fileToRemove in package.removeFiles:
        try:
            if os.path.isfile(fileToRemove):
                os.remove(fileToRemove)
                rmlist.append("remove file: " + fileToRemove);
        except:
            pkgutil.debug("Failed to delete file: " + fileToRemove)
            
    for dirToRemove in package.removeDirs:
        try:
            if os.path.isdir(dirToRemove):
                shutil.rmtree(dirToRemove)
                rmlist.append("remove dir: " + dirToRemove)
        except:
            pkgutil.debug("Failed to delete directory: " + dirToRemove)

    package.writeLog(rmlist, "removelog")



def waitForResponse():
    packagesRemaining = len(packages)
    pkgutil.debug("Waiting for build server responses...")
    
    while packagesRemaining:
        (sock, (host, port)) = serversocket.accept()
        pkgutil.debug(" - got response from %s:%d" % (host, port))
        match = False
        for pkg in packages:
            pkgutil.debug("   - matching %s vs %s... " % (pkg.buildServer, host))
            if socket.gethostbyname(pkg.buildServer) == host:
                pkg.dataFile = options.packageRoot + "/" + pkg.name() + ".zip"
                pkgutil.getDataFile(sock, pkg.dataFile)
                postProcessPackage(pkg)
                match = True
        if match:
            packagesRemaining = packagesRemaining - 1


def shortcutPackageBuild():
    setupPackages()
    
    print "deleting old crap..."

    if os.path.isdir("/tmp/package-builder/qtjambi-win64-commercial-4.4.0_01"):
        shutil.rmtree("/tmp/package-builder/qtjambi-win64-commercial-4.4.0_01")

    packages[0].dataFile = "/tmp/package-builder/qtjambi-win64-commercial-4.4.0_01.zip"
    postProcessPackage(packages[0])
    
    return 0

        


# The main function, parses cmd line arguments and starts the pacakge
# building process...
def main():
    options.buildMac = True;
    options.buildWindows = True;
    options.buildLinux = True;
    options.build32 = True;
    options.build64 = True;
    options.buildEval = True;
    options.buildGpl = True;
    options.buildCommercial = True;
    
    for i in range(0, len(sys.argv)):
        arg = sys.argv[i];
        if arg == "--qt-version":
            options.qtVersion = sys.argv[i+1]
        elif arg == "--package-root":
            options.packageRoot = sys.argv[i+1]
        elif arg == "--qt-jambi-version":
            options.qtJambiVersion = sys.argv[i+1]
        elif arg == "--no-mac":
            options.buildMac = False;
        elif arg == "--no-win":
            options.buildWindows = False;
        elif arg == "--no-linux":
            options.buildLinux = False;
        elif arg == "--no-eval":
            options.buildEval = False;
        elif arg == "--no-gpl":
            options.buildGpl = False;
        elif arg == "--no-commercial":
            options.buildCommercial = False;
        elif arg == "--no-32bit":
            options.build32 = False;
        elif arg == "--no-64bit":
            options.build64 = False;
        elif arg == "--verbose":
            pkgutil.VERBOSE = 1

    options.startDir = os.getcwd()

    pkgutil.debug("Options:")
    print "  - Qt Version: " + options.qtVersion
    print "  - Package Root: " + options.packageRoot
    print "  - Qt Jambi Version: " + options.qtJambiVersion
    print "  - P4 User: " + options.p4User
    print "  - P4 Client: " + options.p4Client
    print "  - buildMac: %s" % options.buildMac
    print "  - buildWindows: %s" % options.buildWindows
    print "  - buildLinux: %s" % options.buildLinux
    print "  - buildEval: %s" % options.buildEval
    print "  - buildGpl: %s" % options.buildGpl
    print "  - buildCommercial: %s" % options.buildCommercial
    print "  - build32: %s" % options.build32
    print "  - build64: %s" % options.build64

    pkgutil.debug("preparing source tree...")
    prepareSourceTree()

    pkgutil.debug("configuring packages...");
    setupPackages()
    pkgutil.debug(" - %d packages in total..." % len(packages))

    # Package and send all packages, finish off by closing all sockets
    # to make sure they are properly closed...
    for package in packages:
        packageAndSend(package)

    waitForResponse()

    

if __name__ == "__main__":
    main()