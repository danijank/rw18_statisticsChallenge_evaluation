#!/usr/bin/python3

import sys;
import os;
import tempfile;
import shutil;
# https://docs.python.org/3.5/library/subprocess.html
import subprocess;
import csv;
import evaluation;
import generateResults;

def build(groupName, url, workingDir, outputDir):
  oldDir = os.getcwd();
  try:
    if not os.path.exists(workingDir):
      os.makedirs(workingDir);
    os.chdir(workingDir);
    myEnv = os.environ.copy();
    myEnv["GIT_TERMINAL_PROMPT"] = "0";
    result = subprocess.run(["git", "clone", url, groupName], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=myEnv);
    if result.returncode != 0:
      evaluation.writeError(outputDir, groupName, result.returncode, evaluation.convertOutput(result.stderr));
      return 1;
    
    repDir = os.path.join(workingDir,groupName);
    os.chdir(repDir);
    result = subprocess.run(["mvn", "clean", "package"], stdout=subprocess.PIPE, stderr=subprocess.PIPE);
    if result.returncode != 0:
      evaluation.writeError(outputDir, groupName, result.returncode, evaluation.convertOutput(result.stderr));
      return 1;
    
    os.chdir(oldDir);
    
    originalJarFile = os.path.join(repDir,"target","statistics.jar");
    targetJarFile = os.path.join(oldDir,"lib","statistics.jar");
    if os.path.exists(targetJarFile):
      os.remove(targetJarFile);
    os.rename(originalJarFile, targetJarFile);
    result = subprocess.run(["ant"], stdout=subprocess.PIPE, stderr=subprocess.PIPE);
    if result.returncode != 0:
      evaluation.writeError(outputDir, groupName, result.returncode, evaluation.convertOutput(result.stderr));
      return 1;
    
    return 0;
  finally:
    os.chdir(oldDir);
    if os.path.exists(workingDir):
      shutil.rmtree(workingDir)

def main(groupsCSV="groups.csv",workingDir=os.path.join(tempfile.gettempdir(),"buildRW18")):
  # adjust call dir
  callDir = os.path.dirname(os.path.realpath(__file__));
  os.chdir(callDir);
  
  outputDir = os.path.abspath(os.path.join(os.getcwd(), os.pardir,"results"));
  if not os.path.exists(outputDir):
    os.makedirs(outputDir);
  
  with open(groupsCSV, 'r', newline='') as csvfile:
    reader = csv.reader(csvfile);
    next(reader, None)  # skip the headers
    for row in reader:
      groupName = row[0];
      url = row[1]
      groupMembers = row[2:len(row)];
      print("group: "+groupName);
      returnValue = build(groupName,url,workingDir,outputDir);
      if returnValue != 0:
        evaluation.writeResult(outputDir, [groupName, 'True', '', '', '', '-1', '-1', '-1']);
        print("  build failed!");
        continue;
      print("  build finished")
      # evaluate
      result = subprocess.run(["python3","evaluation.py",groupName,outputDir], stdout=subprocess.PIPE, stderr=subprocess.PIPE);
      if result.returncode != 0:
        evaluation.writeError(outputDir, groupName, result.returncode, evaluation.convertOutput(result.stderr));
        print("  evaluation failed");
        continue;
      print("  evaluation succeeded");
  generateResults.main();
  
  
if __name__ == "__main__":
  args = sys.argv;
  if len(args) == 1 + 1:
    main(args[1]);
  else:
    main();