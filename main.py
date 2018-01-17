# -*- encoding:utf-8 -*-
import os, random
import SearchCommitLog, StaticAnalysis
from GobalFilePath import *

# for git_project in GIT_PROJECT_LIST:
#     SearchCommitLog.downloadGitPorject(git_project)
#     SearchCommitLog.searchCommitLog(git_project, KEYWORD)
#     SearchCommitLog.downloadRev(git_project)

StaticAnalysis.runPMD(PRJECT_LIST[0])
      
### 3. Extracting Alert Patterns 
#extractAlertPattern()
# transARFFfile4Apriori()