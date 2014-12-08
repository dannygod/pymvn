#!/usr/bin/env python

import hashlib
import optparse
import os
import sys

from pymvn import artifact, downloader, pom, utils


class MavenDownloader(downloader.FileDownloader):
  def __init__(self, mvn_server):
    if not mvn_server.endswith('/'):
      mvn_server = mvn_server + '/'
    downloader.FileDownloader.__init__(self, base=mvn_server)
  
  def Download(self, options, artifacts):
    for arti in artifacts:
      filename = arti.GetFilename(options.output_dir)
      artifact_path = arti.Path(with_filename=True)
      if not self._VerifyMD5(filename, artifact_path + '.md5'):
        self.Fetch(artifact_path, filename, options.quite)
      else:
        if not options.quite:
          print('%s is already up to date' % str(arti))
  
  def _VerifyMD5(self, filename, url_path):
    remote_md5 = self.Get(url_path, 'Failed to fetch MD5', lambda r: r.read())
    return utils.VerifyMD5(filename, remote_md5)
  

def DoMain(argv):
  usage = 'Usage: %prog [options] coordinate1 coordinate2 ...'
  parser = optparse.OptionParser(usage=usage)
  parser.add_option('--mvn-server', help='Custom maven server')
  parser.add_option('--output-dir', help='Directory to save downloaded files')
  parser.add_option('--print-only',
                    action='store_true',
                    default=False,
                    help='Only print paths of downloaded files')
  parser.add_option('--quite',
                    action='store_true',
                    default=False,
                    help='Do not output logs')

  options, args = parser.parse_args(argv)

  if not len(args):
    utils.PrintWarning('At least input a maven coordinates!')
    parser.print_help()
    return 2

  artifacts = []
  for coordiante in args:
    artifacts.append(artifact.Artifact.Parse(coordiante))

  # parse all dependencise according coordinate inputs.
  mvn_url = 'http://repo1.maven.org/maven2/' if not options.mvn_server else options.mvn_server
  d = MavenDownloader(mvn_url)
  download_artifacts = []
  for arti in artifacts:
    p = pom.Pom.Parse(d, arti)
    download_artifacts.extend(p.GetCompileNeededArtifacts())

  # slim the all in one dependencise list, we know we are doing here!
  download_artifacts = pom.Pom.Slim(download_artifacts)

  if options.print_only:
    utils.CheckOptions(options, parser, required=['output_dir'])
    return ' '.join([arti.GetFilename(options.output_dir) for arti in download_artifacts])
  
  d.Download(options, download_artifacts) 


if __name__ == '__main__':
  sys.exit(DoMain(sys.argv[1:]))