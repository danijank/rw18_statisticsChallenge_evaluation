package rw2018.statisticsEvaluation;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;

import java.io.File;
import java.util.Arrays;

import rw2018.statistics.StatisticsDB;
import rw2018.statistics.impl.StatisticsDBImpl;
import rw2018.statisticsEvaluation.baseImpl.StatisticsDBBaseImpl;

/**
 * Checks whether the statistics are collected correctly.
 * 
 * @author Daniel Janke &lt;danijankATuni-koblenz.de&gt;
 *
 */
public class CompareResults {

  public static void compareStatistics(File solutionDir, int numberOfChunks, File workingDir) {
    try (StatisticsDB solution = new StatisticsDBBaseImpl();
            StatisticsDB candidate = new StatisticsDBImpl();) {
      solution.setUp(solutionDir, numberOfChunks);
      candidate.setUp(workingDir, numberOfChunks);

      for (int resourceId = 1; true; resourceId++) {
        long[] solFrequencies = solution.getFrequencies(resourceId);
        if (solFrequencies == null) {
          break;
        }
        long[] candFrequencies = candidate.getFrequencies(resourceId);
        if ((candFrequencies == null) || !Arrays.equals(solFrequencies, candFrequencies)) {
          throw new RuntimeException(
                  "The candidate does not have the correct results. For resource " + resourceId
                          + " it returned\n" + Arrays.toString(candFrequencies)
                          + "\nwhereas the correct solution is\n"
                          + Arrays.toString(solFrequencies));
        }
      }
    }
  }

  public static void main(String[] args) throws ParseException {
    Option help = new Option("h", "help", false, "print this help message");
    help.setRequired(false);

    Option solution = Option.builder("s").longOpt("solution").hasArg().argName("solutionDirectory")
            .desc("the directory in which the correct solution is stored").required(true).build();

    Option input = Option.builder("i").longOpt("input").hasArg().argName("inputDirectory")
            .desc("the directory in which the encoded chunks are stored").required(true).build();

    Option working = Option.builder("w").longOpt("workingDir").hasArg().argName("workingDirectory")
            .desc("the working directory in which the statistics database will be persisted")
            .required(true).build();

    Options options = new Options();
    options.addOption(help);
    options.addOption(solution);
    options.addOption(input);
    options.addOption(working);

    CommandLineParser parser = new DefaultParser();
    try {
      CommandLine cLine = parser.parse(options, args);

      if (cLine.hasOption("h")) {
        CompareResults.printUsage(options);
        return;
      }

      File workingDir = new File(cLine.getOptionValue('w'));
      File solutionDir = new File(cLine.getOptionValue('s'));
      File inputDir = new File(cLine.getOptionValue('i'));

      CompareResults.compareStatistics(solutionDir, inputDir.listFiles().length, workingDir);

    } catch (ParseException e) {
      CompareResults.printUsage(options);
      throw e;
    }
  }

  private static void printUsage(Options options) {
    HelpFormatter formatter = new HelpFormatter();
    formatter.printHelp(
            "java " + CompareResults.class + " [-h] -i <inputDir> -s <solutionDir> -w <workingDir>",
            options);
  }

}
