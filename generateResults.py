#!/usr/bin/python3

import sys;
import os;
import csv;
import functools;
import matplotlib;
matplotlib.use('Agg');
import matplotlib.pyplot as plt;

def addToResults(results, baseline, candidate):
    baselineTime = float(baseline[5]);
    baselineMemory = int(baseline[6]);
    baselineDisk = int(baseline[7]);
    candTime = float(candidate[5]);
    candMemory = int(candidate[6]);
    candDisk = int(candidate[7]);
    
    time = (candTime - baselineTime) / baselineTime * 100;
    memory = (candMemory - baselineMemory) / float(baselineMemory) * 100;
    disk = (candDisk - baselineDisk) / float(baselineDisk) * 100;
    totalScore = time + memory + disk;
    
    result = [time, candTime, memory, candMemory, disk, candDisk, totalScore];
    
    results[candidate[0]] = result;

def compareResults(this, other):
  thisV = this[1];
  otherV = other[1];
  # compare total score
  comparison = thisV[len(thisV)-1] - otherV[len(otherV)-1];
  if comparison == 0:
    # compare time %
    comparison = thisV[0] - otherV[0];
    if comparison == 0:
      # compare memory %
      comparison = thisV[2] - otherV[2];
      if comparison == 0:
        # compare disk %
        comparison = thisV[4] - otherV[4];
      if comparison == 0:
        # compare group names
        comparison = -1 if this[0].lower() < other[0].lower() else (1 if this[0].lower() > other[0].lower() else 0);
  return comparison;

def compareTuples(this, other):
  # compare value
  comparison = this[1] - other[1];
  if comparison == 0:
    # compare group names
    comparison = -1 if this[0].lower() < other[0].lower() else (1 if this[0].lower() > other[0].lower() else 0);
  return comparison;

def createPlot(data, ylabel, filename):
  teams = list(map(lambda x: x[0], data));
  barData = list(map(lambda x: x[1], data));
  # pick colors
  sortedTeams = sorted(teams);
  teamColors = {};
  #colormap = plt.cm.get_cmap('Dark2');
  colormap = plt.cm.gist_ncar
  colors = [colormap(i) for i in (x/len(teams) for x in range(0, len(teams)))];
  for team, color in zip(sortedTeams, colors):
    teamColors[team] = color;
  colorList = list(map(lambda x:teamColors[x], teams));
  
  N = len(barData);
  x = range(N);
  width = 1/1.5;
  plt.bar(x, barData, width, color=colorList, align='center');
  plt.xticks(x, teams, rotation='vertical');
  plt.xlabel("Teams");
  plt.ylabel(ylabel);
  plt.axhline(color='black');
  plt.axvline(x=x[teams.index('baseline')],color='red',linewidth=3);
  ymin, ymax = plt.ylim();
  if ymax < 10.:
    ymax = 10.;
  if ymax in barData:
    ymax += 5;
  if ymin > -10.:
    ymin = -10.;
  if ymin in barData:
    ymin -= 5;
  plt.ylim(ymin,ymax);
  plt.tight_layout();
  plt.savefig(filename);
  plt.close();

def main(resultCSV=os.path.abspath(os.path.join(os.getcwd(),"results","results.csv")), outputDir=os.path.abspath(os.path.join(os.getcwd(),"results"))):
  # adjust call dir
  callDir = os.path.dirname(os.path.realpath(__file__));
  os.chdir(callDir);
  
  buildErrors = set();
  executionErrors = set();
  timeouts = set();
  incorrectResults = set();
  results = {} # maps groupName to [exTime%, exTime, memory%, memory, disk%, disk, totalScore]
  
  with open(resultCSV, 'r', newline='') as csvfile:
    reader = csv.reader(csvfile);
    next(reader, None)  # skip the headers
    baseline = next(reader, None) # read baseline data
    addToResults(results,baseline,baseline);
    for row in reader:
      if row[1] == 'True':
        buildErrors.add(row[0]);
      elif row[2] == 'True':
        executionErrors.add(row[0]);
      elif row[3] == 'True':
        timeouts.add(row[0]);
      elif row[4] == 'False':
        incorrectResults.add(row[0]);
      else:
        addToResults(results, baseline, row);
  
  buildErrors = sorted(buildErrors);
  executionErrors = sorted(executionErrors);
  timeouts = sorted(timeouts);
  incorrectResults = sorted(incorrectResults);
  
  resultList = [(k,v) for k,v in results.items()];
  resultList = sorted(resultList, key=functools.cmp_to_key(compareResults), reverse=False);
  
  total = list(map(lambda x: (x[0], x[1][len(x[1])-1]),resultList));
  
  executionTime = list(map(lambda x: (x[0], x[1][0]),resultList));
  executionTime = sorted(executionTime, key=functools.cmp_to_key(compareTuples));
  
  memory = list(map(lambda x: (x[0], x[1][2]),resultList));
  memory = sorted(memory, key=functools.cmp_to_key(compareTuples));
  
  disk = list(map(lambda x: (x[0], x[1][4]),resultList));
  disk = sorted(disk, key=functools.cmp_to_key(compareTuples));
  
  if not os.path.exists(outputDir):
    os.makedirs(outputDir);
  
  createPlot(total, 'Total Performance Change [%]', os.path.join(outputDir,'totalScore.svg'));
  createPlot(executionTime, 'Execution Time Change [%]', os.path.join(outputDir,'executionTime.svg'));
  createPlot(memory,'Memory Consumption Change [%]', os.path.join(outputDir,'memory.svg'));
  createPlot(disk,'Disk Consumption Change [%]', os.path.join(outputDir,'disk.svg'));
  
  outputFile = os.path.join(outputDir, "results.html");
  with open(outputFile,'w') as output:
    output.write("""<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>Results of Statistics Competition</title>
    <style>
      h1, h2, figure {
        text-align: center;
      }
      
      figcaption {
        font-size: 1.5em;
        font-weight: bold;
      }
      
      table, th, td { 
        border-collapse: collapse;
        padding:0.3em 0.5em; 
      }
      
      table {
       text-align: center;
       margin-left:auto; 
       margin-right:auto;
      }
      
      th, caption { 
        background-color: #666; 
        color: #fff; 
        border: 1px solid #666;
      }
      
      td {
       background-image: linear-gradient(#f9f9f9, #e3e3e3);
       border-left: 1px solid #666;
       border-right: 1px solid #666;
      }
      
      #baseline td {
       background-image: none;
       background-color: #ffffff;
       border-left: 1px solid #666;
       border-right: 1px solid #666;
       font-weight: bold;
      }
      
      td[colspan]:not([colspan="1"]) {
        text-align: center;
      }
      
      tfoot {
        border-bottom: 1px solid #666;
      }
      
      caption {
        font-size: 1.5em;
        border-radius: 0.5em 0.5em 0 0;
        padding: 0.5em 0 0 0
      }
      
      /* 3. und 4. Spalte rechtsbündig */
      td:nth-of-type(3),td:nth-of-type(4) {
        text-align: right;
      }
      
      tbody tr:hover td,
      tfoot tr:hover td,
      #baseline:hover td {
        background-image: none;
        background-color: #888;
        color: #fff;
      }
    </style>
  </head>
  <body>
    <h1>Results of Statistics Competition</h1>""");
    # output results
    output.write("""
    <table>
      <caption>Ranking</caption>
      <thead>
        <tr>
          <th>Rank</th>
          <th>Team</th>
          <th>Execution Time (in sec)</th>
          <th>Memory Consumption (in KB)</th>
          <th>Disk Consumption (in MB)</th>
          <th>Total Performance Change</th>
        </tr>
      </thead>
      <tbody>""");
    for rank, result in enumerate(resultList):
      if result[0] == "baseline":
        output.write("\n        <tr id=\"baseline\">");
      else:
        output.write("\n        <tr>");
      output.write("\n          <td>" + str(rank+1) + "</td>");
      output.write("\n          <td>" + result[0] + "</td>");
      output.write("\n          <td>" + str(result[1][1]) + " = " + ("+" if result[1][0] > 0 else "") + str(result[1][0]) + "%</td>");
      output.write("\n          <td>" + str(result[1][3]) + " = " + ("+" if result[1][2] > 0 else "") + str(result[1][2]) + "%</td>");
      output.write("\n          <td>" + str(result[1][5]/1024/1024) + " = " + ("+" if result[1][4] > 0 else "") + str(result[1][4]) + "%</td>");
      output.write("\n          <td>" + ("+" if result[1][6] > 0 else "") + str(result[1][6]) + "</td>");
      output.write("\n        </tr>");
    # output incorrect results
    if len(incorrectResults) > 0:
      for team in incorrectResults:
        output.write("\n        <tr>");
        output.write("\n          <td>incorrect</td>");
        output.write("\n          <td>" + team + "</td>");
        output.write("\n          <td colspan=\"4\"><a href=\"" + team + ".err\">get error log</a></td>");
        output.write("\n        </tr>");
    # output timeouts
    if len(timeouts) > 0:
      for team in timeouts:
        output.write("\n        <tr>");
        output.write("\n          <td>timeouts</td>");
        output.write("\n          <td>" + team + "</td>");
        output.write("\n          <td colspan=\"4\"></td>");
        output.write("\n        </tr>");
    # output execution errors
    if len(executionErrors) > 0:
      for team in executionErrors:
        output.write("\n        <tr>");
        output.write("\n          <td>exception</td>");
        output.write("\n          <td>" + team + "</td>");
        output.write("\n          <td colspan=\"4\"><a href=\"" + team + ".err\">get error log</a></td>");
        output.write("\n        </tr>");
    # output build errors
    if len(buildErrors) > 0:
      for team in buildErrors:
        output.write("\n        <tr>");
        output.write("\n          <td>build-err</td>");
        output.write("\n          <td>" + team + "</td>");
        output.write("\n          <td colspan=\"4\"><a href=\"" + team + ".err\">get error log</a></td>");
        output.write("\n        </tr>");
    output.write("""
      </tbody>
      <tfoot>
        <tr>
        </tr>
      </tfoot>
    </table>""");
    
    # output images
    output.write("""
    <figure>
      <figcaption>Team ranking based on total performance change</figcaption>
      <img src="totalScore.svg" alt="totalScore.svg"/>
    </figure>""");
    output.write("""
    <figure>
      <figcaption>Team ranking based on execution time change</figcaption>
      <img src="executionTime.svg" alt="executionTime.svg"/>
    </figure>""");
    output.write("""
    <figure>
      <figcaption>Team ranking based on memory consumption change</figcaption>
      <img src="memory.svg" alt="memory.svg"/>
    </figure>""");
    output.write("""
    <figure>
      <figcaption>Team ranking based on disk consumption change</figcaption>
      <img src="disk.svg" alt="disk.svg"/>
    </figure>""");
    
    output.write("""
  </body>
</html>""");


if __name__ == "__main__":
  args = sys.argv;
  if len(args) == 1 + 2:
    main(args[1],args[2]);
  elif len(args) == 1 + 1:
    main(args[1]);
  else:
    main();