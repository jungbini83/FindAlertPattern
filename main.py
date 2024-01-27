# -*- encoding:utf-8 -*-
import os, random
import SearchCommitLog
import StaticAnalysis
import ExtractAlertPattern
from GobalFilePath import *

# for git_project in GIT_PROJECT_LIST:
#     SearchCommitLog.downloadGitPorject(git_project)
#     SearchCommitLog.searchCommitLog(git_project, KEYWORD)
    # SearchCommitLog.downloadRev(git_project)
    # SearchCommitLog.remove_project_dir(git_project)

PMD_PROJECT_LIST = ['wiremock']

# StaticAnalysis.runPMD(PMD_PROJECT_LIST[0])
trainFileList = StaticAnalysis.summaryPMDOutput(PMD_PROJECT_LIST[0], CATEGORY_LIST, 0.3, 'normal' )
StaticAnalysis.divideTrainTest(PMD_PROJECT_LIST[0], trainFileList)
      
### 3. Extracting Alert Patterns 
# ExtractAlertPattern.extractAlertPattern(PMD_PROJECT_LIST[0])
# transARFFfile4Apriori()