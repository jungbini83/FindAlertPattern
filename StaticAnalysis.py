# -*- encoding:utf-8 -*-
# Running static analysis (PMD, FindBugs..)
import os, re, subprocess, random
from collections import defaultdict, Counter, OrderedDict
from fileinput import filename
from GobalFilePath import *

BUG_TYPE        = ['BUGGY', 'CLEAN']

# 1. Run PMD against Buggy and Clean src code
def runPMD(PROJECT_NAME):
    
    PROJECT_PATH = GIT_REPO_PATH + PROJECT_NAME + '/'
        
    DN_PATH = PROJECT_PATH + 'DOWNLOAD/'
    SA_RESULT_PATH = PROJECT_PATH + 'SA_RESULT/'
    if not os.path.exists(SA_RESULT_PATH):                   # Static analysis result output path
        os.makedirs(SA_RESULT_PATH)
    
    cwd = os.getcwd()                                       # save current path
    for bugType in BUG_TYPE:
        
        os.chdir(PMD_PATH + 'bin/')                         # move to pmd binary path

        print (PROJECT_NAME + ' ' + bugType + ' analysis by PMD...\n')
        cmd_result = os.system('pmd -d ../../../'+ DN_PATH + bugType + '/' + ' -f csv -R rulesets/java/basic.xml,rulesets/java/braces.xml,rulesets/java/clone.xml,'+
                               'rulesets/java/codesize.xml,rulesets/java/comments.xml,rulesets/java/controversial.xml,rulesets/java/coupling.xml,rulesets/java/design.xml,'+
                               'rulesets/java/empty.xml,rulesets/java/finalizers.xml,rulesets/java/imports.xml,rulesets/java/j2ee.xml,rulesets/java/javabeans.xml,'+
                               'rulesets/java/junit.xml,rulesets/java/logging-jakarta-commons.xml,rulesets/java/logging-java.xml,rulesets/java/migrating.xml,'+
                               'rulesets/java/naming.xml,rulesets/java/optimizations.xml,rulesets/java/strictexception.xml,rulesets/java/strings.xml,rulesets/java/sunsecure.xml,'+
                               'rulesets/java/typeresolution.xml,rulesets/java/unnecessary.xml,rulesets/java/unusedcode.xml > ../../../' + SA_RESULT_PATH + bugType + '_PMD.txt')
        
        if not cmd_result == 0:
            print ('Error occurred...\n')
        
        os.chdir(cwd)                                       # restore previous path (project path)
        
        RESULT_FILE = open(SA_RESULT_PATH + bugType + '_PMD.txt', 'r')
        OUT_FILE = open(SA_RESULT_PATH + bugType + '_RESULT.txt', 'w')
              
        # parsing raw PMD output file to new format
        for line in RESULT_FILE:
             
            if (not line.startswith('Removed') and not line.startswith('\"Problem') and line.startswith('\"')):

                # Find result line of PMD
                alertToken = re.match('"(\d+)","(.*)","(.*)","(\d+)","(\d+)","(.*)","(.*)","(.*)"', line)
             
                ### Tokenize the result line ###
                if alertToken:
                    filename = alertToken.group(3).replace('\\', '/')       # repalce \\ to /
                    filename = filename[filename.rfind('/')+1:]
                    alertline = alertToken.group(5)
                    alertname = alertToken.group(8)                                                             
                     
                    OUT_FILE.write(filename + ',' + alertline + ',' + alertname + '\n')

        RESULT_FILE.close()
        OUT_FILE.close()

        os.remove(SA_RESULT_PATH + bugType + '_PMD.txt')                # remove raw pmd output file
                    
def bugRelatedLines(log_path):
    
    buggyFileInfo = OrderedDict()
    cleanFileInfo = OrderedDict()
    
    for line in open(log_path + 'BUG_RELATED.txt'):

        tokenLine = line.split(',')
        revDate = tokenLine[0]                                            # not used now
        filePath = tokenLine[1]
        fileName = filePath[filePath.rfind('/')+1:]
        buggyRevNum = tokenLine[2]
        cleanRevNum = tokenLine[3]
        
        if not buggyFileInfo.has_key('[' + buggyRevNum + ']' + fileName):        
            buggyFileInfo['[' + buggyRevNum + ']' + fileName] = list()
        else:
            continue
        if not cleanFileInfo.has_key('[' + cleanRevNum + ']' + fileName):
            cleanFileInfo['[' + cleanRevNum + ']' + fileName] = list()
        
        for bugLine in tokenLine[4:]:
            if bugLine.strip():                
                buggyFileInfo['[' + buggyRevNum + ']' + fileName].append(bugLine.split('-')[0].strip())            
                cleanFileInfo['[' + cleanRevNum + ']' + fileName].append(bugLine.split('-')[1].strip())
            
    return buggyFileInfo, cleanFileInfo

def getRevisionPair(log_path):
    
    RevPairDict = dict()
    for line in open(log_path + 'BUG_RELATED.txt'):

        tokenLine = line.split(',')
        filePath = tokenLine[1]
        fileName = filePath[filePath.rfind('/')+1:]
        buggyRevNum = tokenLine[2]
        cleanRevNum = tokenLine[3]
        
        RevPairDict['[' + buggyRevNum + ']' + fileName] = '[' + cleanRevNum + ']' + fileName
        
    return RevPairDict

# PMD ���Ͽ��� Warning ���� ���� ���� �������� �Լ�
def getWarningInfo(filePath):
    
    FileInfoDict = dict()
    for line in open(filePath):
        tokenLine = line.strip().split(',')        
        
        if not FileInfoDict.has_key(tokenLine[0]):
            FileInfoDict[tokenLine[0]] = defaultdict(list)
        
        FileInfoDict[tokenLine[0]][int(tokenLine[1])].append(tokenLine[2])
    
    return FileInfoDict

# Ư�� ����(Fix change)���� ���ݵ� warning �� �������� �Լ�
def getFixedWarningList(CATEGORY_LIST, violatedLines, warningInfoDict):
    
    bStartLine  = int(violatedLines.split('/')[0])                                       # Buggy File�� bug related ���� ����            
    bEndLine    = bStartLine + int(violatedLines.split('/')[1]) - 1                      # Buggy File�� bug related �� ����
    
    FixedWarnList = []            
    for BuggyLine, BuggyWarning in warningInfoDict.items():                              # Buggy/Clean ������ warning���� ��ȸ�ϸ鼭, Related ���ο� ���� FixedWarnList�� �߰�             
        if bStartLine <= BuggyLine <= bEndLine:
            for warning in BuggyWarning:
                if not warning in CATEGORY_LIST:    continue                             # CATEGORY_LIST�� ���� warning�̶�� ����
                FixedWarnList.append(warning)
    
    return FixedWarnList  

# Ư�� ����(Other)���� ���ݵ� warning �� �������� �Լ�
def getOtherFixedWarningList(CATEGORY_LIST, violatedLines, warningInfoDict):
    
    LineList = []
    for bugLines in violatedLines:
        StartLine  = int(bugLines.split('/')[0])                                        # Buggy File�� bug related ���� ����            
        EndLine    = StartLine + int(bugLines.split('/')[1])                            # Buggy File�� bug related �� ����
        
        for fixLine in range(StartLine, EndLine):                                       # Related Line�� ��� ����Ʈ�� �߰�
            LineList.append(fixLine)
            
    OtherList = []
    for BuggyLine, BuggyWarning in warningInfoDict.items():
        if not BuggyLine in LineList:
            for warning in BuggyWarning:
                if not warning in CATEGORY_LIST:    continue                             # CATEGORY_LIST�� ���� warning�̶�� ����
                OtherList.append(warning)
    
    return OtherList

def printTotalResult(SUMMARY_PATH, CATEGORY_LIST, resultDict, type):
    
    if 'bugrelated' in type:    fileName = SUMMARY_PATH + 'BUGRELATED_TOTAL_RESULT.csv'
    else:                       fileName = SUMMARY_PATH + 'OTHER_TOTAL_RESULT.csv'
        
    OUT_FILE = open(fileName, 'w')
    
    for fileName, wInfo in resultDict.items():
        OUT_FILE.write(fileName + ',')                                                        # Fix �Ǳ� ���� warning instance�� �� ������ ���
        for category in CATEGORY_LIST:
            if wInfo.has_key(category):
                OUT_FILE.write(str(wInfo[category]) + ',')
            else:
                OUT_FILE.write('0,')
        OUT_FILE.write('\n')
         
def printPrecision(SUMMARY_PATH, WEIGHT_ALPHA, CATEGORY_LIST, resultDict, totalDict, TrainFileList, type):
    
    OUT_FILE = open(SUMMARY_PATH + type + '_RESULT.csv', 'w')
    
    if 'BUGRELATED' in type:    ALPHA = WEIGHT_ALPHA                    # Bug related �� ��, alpha �� ����
    else:                       ALPHA = 1 - WEIGHT_ALPHA                # Others �� ��, alpha �� ����
    
    for fname, wInfo in resultDict.items():
        
        OUT_FILE.write(fname + ',')
        
        if not fname in TrainFileList:                                                                              # Train�� �ƴ� Test ������ ���� warning ���� ���� �״�� ���
            OUT_FILE.write(','.join([str(wInfo[category]) for category in CATEGORY_LIST]) + '\n')
        else:        
            for categoryName in CATEGORY_LIST:             
                if totalDict[fname][categoryName] == 0:                                                             # �и� 0�̸� 0
                    OUT_FILE.write('0,')                                             
                else:
                    Weight = float(wInfo[categoryName]) * ALPHA                                                  # Fix�� Warning�� ������ Alpha ���� ����                    
                    OUT_FILE.write(str(Weight) + ',')                                                    
            OUT_FILE.write('\n') 

def summaryPMDOutput(PROJECT_NAME, CATEGORY_LIST, divRatio, divideType):

    sa_path = PROJECT_NAME + '/STATIC_ANALYSIS/'
    log_path = PROJECT_NAME + '/COMMIT_LOG/'

    # 1-1. Get bug-related lines from Buggy, Clean src code
    buggyRelatedLines, cleanRelatedLines = bugRelatedLines(log_path)
    buggyRelatedFiles = buggyRelatedLines.keys()
    
    # 1-2. Divide train, test dataset using divRatio from Buggy src code
    TrainFileRatio = int(len(buggyRelatedLines.keys()) * divRatio)
    
    # dividing typy= (normal: divide train and test src code by time sequence), (random: divide randomly train and test src code)
    if 'normal' in divideType:
        TrainFileList = [fileName for fileName in buggyRelatedFiles[TrainFileRatio+1:]]
    elif 'random' in divideType:
        TrainFileList = random.sample(buggyRelatedFiles, TrainFileRatio)

    # 1-3. Get pairs including Buggy, Clean revision number
    RevPairDict = getRevisionPair(log_path)

    # 2. Get warnings from Buggy and Clean src code
    BuggyFileInfoDict = getWarningInfo(sa_path + 'BUGGY_RESULT.txt')
    CleanFileInfoDict = getWarningInfo(sa_path + 'CLEAN_RESULT.txt')
        
    REL_FINAL_COUNTER = dict()                          # Dictinary including warnings from bug related srr code
    OTHER_FINAL_COUNTER = dict()                        # Dictinary including warnings from bug free src code
    REL_TotalTotalCounter = dict()                      # # of warnings in bug related src code
    OTHER_TotalTotalCounter = dict()                    # # of warnings in bug free src code
    for fileName, violatedLineList in buggyRelatedLines.items():
        
        if not BuggyFileInfoDict.has_key(fileName): continue                            # �ش� ������ Buggy/CleanFileInfoDict�� ���ٸ�, ������ �����̹Ƿ� ����
        if not CleanFileInfoDict.has_key(RevPairDict[fileName]): continue
        if not cleanRelatedLines.has_key(RevPairDict[fileName]): continue                            # �ϳ��� buggy ��������, �ΰ� �̻��� clean �������� �ִٸ�, �ϳ��� ����ǹǷ� clean revision�� ���� ���� ����. �̶��� �׳� �Ѿ
        
        ################################################################    
        #####             0. ���� ���� �ʱ�ȭ �ϴ� ����            #####
        ################################################################
        
        REL_TotalTotalCounter[fileName] = Counter()
        OTHER_TotalTotalCounter[fileName] = Counter()            
        
        BuggyInfoDict = BuggyFileInfoDict[fileName]                                                     # �ش� Buggy/Clean File ���� �ҷ�����
        CleanInfoDict = CleanFileInfoDict[RevPairDict[fileName]]                                    
        
        REL_FINAL_COUNTER[fileName] = OrderedDict((category,0) for category in CATEGORY_LIST)
        OTHER_FINAL_COUNTER[fileName] = REL_FINAL_COUNTER[fileName].copy()            
        
        ################################################################    
        ##### 1. Bug-Related line�� Fixed Warning�� ��� �ϴ� ���� #####
        ################################################################
        
        rLineIdx = 0         
        while rLineIdx < len(violatedLineList):
            
            try: 
                # Buggy/Clean File�� Bug related�ȿ��� ���ݵ� Warning ī��Ʈ ����
                BuggyCounter = Counter(getFixedWarningList(violatedLineList[rLineIdx], BuggyInfoDict))            
                CleanCounter = Counter(getFixedWarningList(cleanRelatedLines[RevPairDict[fileName]][rLineIdx], CleanInfoDict))                     
                TotalCounter = BuggyCounter.copy()                                                                     # ���� Fix�Ǳ� �� �� Warning ������ ���� (Precision�� ���� �� ������ ����)
                REL_TotalTotalCounter[fileName] += TotalCounter                                                        # �ش� ���Ͽ��� ���ݵ� ��ü Warning ������ ����
                
                BuggyCounter.subtract(CleanCounter)                                                                    # Buggy - Clean�� �ϰ� �Ǹ�, Clean���� ������ ���ڸ�ŭ BuggyCounter�� ��� ��(-���� ������ Clean���� �þ ���̹Ƿ� ����)
    
                for category, fixedNum in ((k,v) for k,v in BuggyCounter.items() if v > 0):                             # v=Fix�� Warning�� ����, 0���� Ŀ�� ������ �� ����
                    REL_FINAL_COUNTER[fileName][category] += int(fixedNum)                                              # Alpha ���� Precision�� ���� �� ���Ѵ�
                    
                rLineIdx += 1
            
            except IndexError:
                
                rLineIdx += 1
                continue
            
        ##########################################################    
        ##### 2. Other line�� Fixed Warning�� ��� �ϴ� ���� #####
        ##########################################################
    
        buggyOtherList = getOtherFixedWarningList(buggyRelatedLines[fileName], BuggyInfoDict)        
        cleanOtherList = getOtherFixedWarningList(cleanRelatedLines[RevPairDict[fileName]], CleanInfoDict)
        
        BuggyCounter = Counter(buggyOtherList)                                                                      # Warning���� ī�����ϱ�
        CleanCounter = Counter(cleanOtherList)         
        TotalCounter = BuggyCounter.copy()                                                                          # �ʱ� Warning ī���� ���ڸ� ����(Precision�� ���� �� ������ ����)
        OTHER_TotalTotalCounter[fileName] += TotalCounter                                                           # ��ü Counter�� ����
        
        BuggyCounter.subtract(CleanCounter)                                                                         # Buggy - Clean�� �ϰ� �Ǹ�, Clean���� ������ ���ڸ�ŭ BuggyCounter�� ��� ��(-���� ������ Clean���� �þ ���̹Ƿ� ����)
        
        for category, fixedNum in ((k,v) for k,v in BuggyCounter.items() if v > 0):                                 # v=Fix�� Warning�� ����, 0���� Ŀ�� ������ �� ����
            OTHER_FINAL_COUNTER[fileName][category] += int(fixedNum)
        
    # Bug realted ���� �Ǵ� Other�� Fix�� Warning Precision ���
    printPrecision(REL_FINAL_COUNTER, REL_TotalTotalCounter, TrainFileList, 'BUGRELATED')
    printPrecision(OTHER_FINAL_COUNTER, OTHER_TotalTotalCounter, TrainFileList, 'OTHER')
    
    # Bug realted ���� �Ǵ� Other�� ��� Warning ���� ���
    printTotalResult(REL_TotalTotalCounter, 'bugrelated')
    printTotalResult(OTHER_TotalTotalCounter, 'other')
            
    return TrainFileList
            
def divideTrainTest(STATIC_ANALYSIS_PATH, SUMMARY_PATH, CATEGORY_LIST, TrainFileList):
    
    TRAIN_NUM = 0
    TEST_NUM = 0
    
    FILE_MERGE_TRAIN_OUT = open(STATIC_ANALYSIS_PATH + 'MERGE_RESULT(TRAIN).csv', 'w')
    FILE_MERGE_TEST_OUT = open(STATIC_ANALYSIS_PATH + 'MERGE_RESULT(TEST).csv', 'w')
    
    RevPairDict = getRevisionPair()                                                                                 # Buggy, Clean revision number Pair ���ϱ�
    
    BugRelated_TrainDict    = dict()
    Other_TrainDict         = dict()    
    BugRelated_TestDict     = dict()
    Other_TestDict          = dict()  
    for TYPE in ['BUGRELATED', 'OTHER']:
        
        FILE_TEST_OUT   = open(SUMMARY_PATH + TYPE + '_RESULT(TEST).csv', 'w')
        FILE_TRAIN_OUT  = open(SUMMARY_PATH + TYPE + '_RESULT(TRAIN).csv', 'w')

        testFileList    = []
        trainFileList   = []
        for line in open(SUMMARY_PATH + TYPE + '_RESULT.csv'):
            if line.split(',')[0] in TrainFileList:                                                # Train/Test ���� �����ϱ�
                trainFileList.append(line)
            else:
                testFileList.append(line)        
        
        for line in trainFileList:                                                                  # Train ���� ���� ��ȯ
            trainFileName = line.split(',')[0]
            trainWInfoList = [float(i) for i in line.strip().split(',')[1:-1]]
        
            if TYPE == 'BUGRELATED':            BugRelated_TrainDict[trainFileName]    = trainWInfoList
            else:                               Other_TrainDict[trainFileName]         = trainWInfoList
        
        for line in testFileList:                                                                   # Test ���� ���� ��ȯ
            testFileName = line.split(',')[0]
            testWInfoList = [int(i) for i in line.strip().split(',')[1:]]                         # Test�� ���� �������� ������ �ʾ����Ƿ� �Ǽ��� ���� �� ����. ���� int()�� ������ ���ٸ�, �̻��� ����            
        
            if TYPE == 'BUGRELATED':            BugRelated_TestDict[testFileName]    = testWInfoList
            else:                               Other_TestDict[testFileName]         = testWInfoList
        
        FILE_TEST_OUT.write(''.join(testFileList))    
        FILE_TRAIN_OUT.write(''.join(trainFileList))
        
    FILE_MERGE_TRAIN_OUT.write('FileName,' + ','.join([cList for cList in CATEGORY_LIST]) + '\n')
    for fName, wInfoList in BugRelated_TrainDict.items():                                                   # Train ���պ�(BugRelated+Others) ����� 
        
        if Other_TrainDict.has_key(fName):            
            sumWInfoList = [float(x) + float(y) for x,y in zip(wInfoList,Other_TrainDict.get(fName))]       # BugRelated ����� Others ����� ���ϱ�
        else:
            sumWInfoList = wInfoList
        
        FILE_MERGE_TRAIN_OUT.write(fName + ',' + ','.join([str(i) for i in sumWInfoList]) + '\n')
        
        TRAIN_NUM += 1        
        
    FILE_MERGE_TEST_OUT.write('FileName,' + ','.join([cList for cList in CATEGORY_LIST]) + '\n')
    for fName, wInfoList in BugRelated_TestDict.items():                                                    # Test ���պ��� ��¥ Bug Fixed ��츸 �����Ѵ�
        
        FILE_MERGE_TEST_OUT.write(fName + ',' + ','.join([str(i) for i in wInfoList]) + '\n')               # ���� Bug related fix ����
        
        TEST_NUM += 1
        
    print ('Train Files Number: ' + str(TRAIN_NUM) + ', Test Files Number: ' + str(TEST_NUM))
        
# Warning�� Fix�� �Ǳ� �� ���� warning�� �� ������ ����(Bug related + Others ���)
def mergeTotalFile(STATIC_ANALYSIS_PATH, SUMMARY_PATH, CATEGORY_LIST, TrainFileList):
    
    TRAIN_TOTAL_FILE    = open(STATIC_ANALYSIS_PATH + 'MERGE_RESULT(TRAIN-TOTAL).csv', 'w')
    TEST_TOTAL_FILE     = open(STATIC_ANALYSIS_PATH + 'MERGE_RESULT(TEST-TOTAL).csv', 'w')
        
    BugRelatedDict = {}    
    for line in open(SUMMARY_PATH + 'BUGRELATED_TOTAL_RESULT.csv'):                                       # BugRelatedDict�� Warning ���� ������ �ֱ�
        fileName    = line.split(',')[0]
        BugRelatedDict[fileName] = [int(x) for x in line.strip().split(',')[1:-1]]

    OtherDict = {}        
    for line in open(SUMMARY_PATH + 'OTHER_TOTAL_RESULT.csv'):                                            # OtherDict�� Warning ���� ������ �ֱ�
        fileName    = line.split(',')[0]                    
        OtherDict[fileName] = [int(x) for x in line.strip().split(',')[1:-1]]
        
    TRAIN_TOTAL_FILE.write('FileName,' + ','.join([cList for cList in CATEGORY_LIST]) + '\n')
    TEST_TOTAL_FILE.write('FileName,' + ','.join([cList for cList in CATEGORY_LIST]) + '\n')
    
    # Train��� Test���� ���� ����� ����: Train�� Fixed Bug + Others Warning���� ��� ����������, 
    # Test�� Fixed Bug ���� ī�����Ͽ��� ������ ���߿� Precision�� ���ϱ����� ������ Total ������ �޶�� �Ѵ�
    for fName, wInfoList in BugRelatedDict.items():                                                             # ���պ�(BugRelated+Others) ����� 
        
        if OtherDict.has_key(fName):            
            TrainSumWInfoList = [sum(i) for i in zip(wInfoList,OtherDict.get(fName))]                           # BugRelated ����� Others ����� ���ϱ�
        else:
            TrainSumWInfoList = wInfoList
        
        TestSumWInfoList = wInfoList        
        
        if fName in TrainFileList:
            TRAIN_TOTAL_FILE.write(fName + ',' + ','.join([str(i) for i in TrainSumWInfoList]) + '\n')
        else:
            TEST_TOTAL_FILE.write(fName + ',' + ','.join([str(i) for i in TestSumWInfoList]) + '\n')        
                
def remove_duplicates(values):
    output = []
    seen = set()
    for value in values:        
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output