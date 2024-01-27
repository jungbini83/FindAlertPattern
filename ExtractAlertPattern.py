# -*- encoding:utf-8 -*-
from GobalFilePath import *

def saveAlertPattern(SAResults, StartLine, EndLine):        
         
        patternList = list()                    
        for saItem in SAResults:
            tokenedStr = saItem.strip().split(',')
             
            if StartLine <= int(tokenedStr[1]) <= EndLine:
                patternList.append(tokenedStr[2])                
             
        return patternList
         
def extractAlertPattern(PROJECT_NAME):

    COMMIT_LOG_PATH = OUTPUT_PATH + PROJECT_NAME + '/COMMIT_LOG/'
    SA_RESULT_PATH  = OUTPUT_PATH + PROJECT_NAME + '/SA_RESULT/'
    RELATED_ALERTS_PATH = OUTPUT_PATH + PROJECT_NAME + '/RELATED/'

    if not os.path.exists(RELATED_ALERTS_PATH):
        os.makedirs(RELATED_ALERTS_PATH)

    BuggySAResultList = [resultFile for resultFile in open(SA_RESULT_PATH + 'BUGGY_RESULT.txt')]        
    CleanSAResultList = [resultFile for resultFile in open(SA_RESULT_PATH + 'CLEAN_RESULT.txt')]
     
    BUGGY_OUTPUT_FILE     = open(RELATED_ALERTS_PATH + 'BUGGY_OUTPUT.txt', 'w')
    CLEAN_OUTPUT_FILE     = open(RELATED_ALERTS_PATH + 'CLEAN_OUTPUT.txt', 'w')
 
    for relatedLines in open(COMMIT_LOG_PATH + 'BUG_RELATED.txt'):
         
        tokenedStr  = relatedLines.split(',') 
         
        fileName    = tokenedStr[1]             # 파일명
        buggyRevNum = tokenedStr[2]             # Buggy 파일 revision 번호
        cleanRevNum = tokenedStr[3]             # Clean 파일 revision 번호    
        relatedLines = tokenedStr[4:]           # Buggy 및 Clean 파일에서 Bug-related 라인들
         
        buggyFileName = '[' + buggyRevNum + ']' + fileName[fileName.rfind('/')+1:]
        cleanFileName = '[' + cleanRevNum + ']' + fileName[fileName.rfind('/')+1:]
         
        buggySAItems   = [item.strip() for item in BuggySAResultList if buggyFileName in item]
        cleanSAItems   = [item.strip() for item in CleanSAResultList if cleanFileName in item]
         
        if not buggySAItems:                continue
         
        for relatedLine in relatedLines:
             
            if relatedLine.strip() == '':   continue                                        # Bug-related 라인이 없다면 다음 파일로 넘기기
             
            relatedLinePair = relatedLine.split('-')                                        # 하나의 Related 라인 쌍 (Buggy파일 and Clean파일)        
             
            buggyStartLine  = int(relatedLinePair[0].split('/')[0])                         # Buggy 파일의 Bug-related 시작 라인
            buggyEndLine    = buggyStartLine + int(relatedLinePair[0].split('/')[1])        # Buggy 파일의 Bug-related 끝 라인
             
            cleanStartLine  = int(relatedLinePair[1].split('/')[0])                         # Clean 파일의 Bug-related 시작 라인
            cleanEndLine    = buggyStartLine + int(relatedLinePair[1].split('/')[1])        # Clean 파일의 Bug-related 끝 라인
             
            buggyPatternList = saveAlertPattern(buggySAItems, buggyStartLine, buggyEndLine)
            cleanPatternList = saveAlertPattern(cleanSAItems, cleanStartLine, cleanEndLine)
             
            BUGGY_OUTPUT_FILE.write(','.join(buggyPatternList) + '\n')            
            CLEAN_OUTPUT_FILE.write(','.join(cleanPatternList) + '\n')   
             
def transARFFfile4Apriori():
     
    CATEGORY_LIST = [ruleset[ruleset.find(',')+1:].strip() for ruleset in open('./PMD_Rules(5.3.1).csv')]            # Category 리스트를 답고 있는 전역 변수
    VAR_LIST    = ['high', 'low']
     
    if not os.path.exists(DATA_MINING_PATH):
        os.makedirs(DATA_MINING_PATH)
         
    BUGGY_OUTPUT_FILE = open(DATA_MINING_PATH + 'BUGGY_AlertPatern.arff', 'w')
    BUGGY_OUTPUT_FILE.write('@relation BUGGY_PATTERN\n')
    for category in CATEGORY_LIST:
        BUGGY_OUTPUT_FILE.write('@attribute \'' + category + '\' { t}\n')
    BUGGY_OUTPUT_FILE.write('@data\n')
     
    for alerts in open(RELATED_ALERTS_PATH + '/BUGGY/OUTPUT.txt'):
         
        tokenedAlerts = alerts.strip().split(',')
         
        AlertList = list()
        for category in CATEGORY_LIST:
             
            if category in tokenedAlerts:
                AlertList.append('t')
            else:
                AlertList.append('?')
         
        BUGGY_OUTPUT_FILE.write(','.join(AlertList) + '\n')