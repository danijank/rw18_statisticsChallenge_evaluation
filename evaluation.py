#!/usr/bin/python3

import sys;
import os;
import tempfile;
import shutil;
# https://docs.python.org/3.5/library/subprocess.html
import subprocess;
# https://docs.python.org/3.5/library/resource.html#resource.getrusage
import resource;
import csv;

def getSize(path):
  total_size = 0
  for dirpath, dirnames, filenames in os.walk(path):
    for f in filenames:
      fp = os.path.join(dirpath, f)
      total_size += os.path.getsize(fp)
  return total_size

def convertOutput(output):
  return output.decode("utf-8").replace('\\n','\n').replace('\\t','\t');

def writeError(outputDir, groupName, returnCode, errorMessage):
  with open(os.path.join(outputDir,groupName + ".err"),'w') as file:
    file.write("return code: " + str(returnCode) + "\n")
    file.write(errorMessage);

def writeOutput(outputDir, groupName, output):
  with open(os.path.join(outputDir,groupName + ".out"),'w') as file:
    file.write(output);

def writeResult(outputDir, line):
  resultCSV = os.path.join(outputDir,"results.csv");
  if not os.path.exists(resultCSV):
    with open(resultCSV, 'w', newline='') as csvfile:
      writer = csv.writer(csvfile);
      writer.writerow(['group','hasError','hasTimeout','areResultsCorrect','avg. writing time (in msec)','memory consumption (in KBytes)', 'disk space (in Byte)']);
  with open(resultCSV, 'a+', newline='') as csvfile:
    writer = csv.writer(csvfile);
    writer.writerow(line);

def main(groupName, timeout):
  # adjust call dir
  callDir = os.path.dirname(os.path.realpath(__file__));
  os.chdir(callDir);
  
  #TODO remove
  # build project
  result = subprocess.run(["ant"], stdout=subprocess.PIPE, stderr=subprocess.PIPE);
  
  outputDir = os.path.join(tempfile.gettempdir(),"results");
  if not os.path.exists(outputDir):
    os.makedirs(outputDir);
  workingDir = os.path.join(tempfile.gettempdir(),"statistics_"+groupName);
  #inputDir = "../chunks";
  inputDir = "/home/janke/Dokumente/Promotion/conferences/ReasoningWebSummerSchool2018/miniExample/";
  #solutionDir = "../solution";
  solutionDir = "/tmp/solutionSmall";
  
  writingTimes = list();
  beforeInfo = resource.getrusage(resource.RUSAGE_CHILDREN);
  for repetition in range(0,10):
    if os.path.exists(workingDir):
      shutil.rmtree(workingDir)
    try:
      result = subprocess.run(["java", "-cp", "build/jar/*:lib/*", "rw2018.statisticsEvaluation.EvaluationWrite", "-i" , inputDir, "-w", workingDir], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout);
    except subprocess.TimeoutExpired:
      writeResult(outputDir, [groupName, 'False', 'True', '', '-1', '-1', '-1']);
      return;
    if result.returncode != 0:
      writeError(outputDir, groupName, result.returncode, convertOutput(result.stderr));
      writeResult(outputDir, [groupName, 'True', '', '', '-1', '-1', '-1']);
      return;
    output = convertOutput(result.stdout);
    if len(output) > 0:
      writeOutput(outputDir, groupName, output);
    afterInfo = resource.getrusage(resource.RUSAGE_CHILDREN);
    writingTimes.append(float(afterInfo.ru_utime)-float(beforeInfo.ru_utime) + float(afterInfo.ru_stime)-float(beforeInfo.ru_stime));
    beforeInfo = afterInfo;
  # measure writing time in seconds.miliseconds
  writingTimes = sorted(writingTimes[1:len(writingTimes)-1]);
  writingTime = sum(writingTimes)/len(writingTimes);
  # measures memory consumption in KBytes
  selfInfo = resource.getrusage(resource.RUSAGE_SELF);
  memoryConsumption = int(selfInfo.ru_maxrss);
  # measure directory size in Bytes
  dirSize = getSize(workingDir);
  
  # check correct solution
  result = subprocess.run(["java", "-cp", "build/jar/*:lib/*", "rw2018.statisticsEvaluation.CompareResults", "-s", solutionDir, "-i" , inputDir, "-w", workingDir], stdout=subprocess.PIPE, stderr=subprocess.PIPE);
  areResultsCorrect = True;
  if result.returncode != 0:
    writeError(outputDir, groupName, result.returncode, convertOutput(result.stderr));
    areResultsCorrect = False;
  
  # write results
  writeResult(outputDir, [groupName, 'False', 'False', str(areResultsCorrect), str(writingTime), str(memoryConsumption), str(dirSize)]);  
  
  # remove data
  shutil.rmtree(workingDir)

args = sys.argv;
if len(args) < 1 + 1:
  print("Missing arguments. Usage: python3 evaluation.py <groupName>");
else:
 main(args[1],timeout=60);