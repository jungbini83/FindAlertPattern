# -*- encoding:utf-8 -*-
# 특정 키워드와 날짜로 commit 로그를 검색
import os
import time, shutil
from git import *                   # GitPython 패키지를 받아야 함
from GobalFilePath import *
import stat

global GIT_REPO_PATH
global SA_RESULT_PATH
global RELATED_ALERTS_PATH
global DATA_MINING_PATH
        
def downloadGitPorject(PROJECT_ADDR):
    
    PROJECT_NAME    = PROJECT_ADDR[PROJECT_ADDR.rfind('/')+1:PROJECT_ADDR.rfind('.git')]    
    
    print ('Cloning ' + PROJECT_NAME + '...')
    try:
        Repo.clone_from(PROJECT_ADDR, 'GitRepo/' + PROJECT_NAME)
    except GitCommandError:
        pass

    print ('done.')
        
def searchCommitLog(PROJECT_ADDR, KEYWORD):

    PROJECT_NAME    = PROJECT_ADDR[PROJECT_ADDR.rfind('/')+1:PROJECT_ADDR.rfind('.git')]        
    PROJECT_PATH    = GIT_REPO_PATH + PROJECT_NAME + '/'
    COMMIT_LOG_PATH = OUTPUT_PATH + PROJECT_NAME + '/COMMIT_LOG/'

    if not os.path.exists(COMMIT_LOG_PATH):
        os.makedirs(COMMIT_LOG_PATH)    
        
    OUTFILE = open(COMMIT_LOG_PATH + 'BUG_RELATED.txt', 'w')
    
    repo = Repo(PROJECT_PATH, odbt=GitCmdObjectDB)                          # 다운 받은 Repository Tree 검색         

    try:
        commit_list = [commit for commit in repo.iter_commits('main')]        # main 브랜치 commit 리스트 받기
    except:
        commit_list = [commit for commit in repo.iter_commits('master')]  # main 브랜치 commit 리스트 받기
    
    for commit_index in range(1,len(commit_list)):
        
        findKeyword = False;
        for keyword in KEYWORD:                                             # commit message에 찾고자 하는 keyword가 있는지 검사 
            if keyword in commit_list[commit_index].message:
                findKeyword = True
                break                
        
        if findKeyword:                                                     # keyword가 있으면 진행
        
            # commit 한 revision 전/후 diff 뜨기
            diff_list = commit_list[commit_index].diff(commit_list[commit_index-1], create_patch=True)      
            
            for diff_item in diff_list.iter_change_type('M'):                       # Rename, add, delete 코드 말고 오로지 수정(modified)된 commit만 검색
                
                if not diff_item.a_path.endswith('.java'):                          # Java 파일이 아니면 다음으로 pass
                    continue
                
                buggyFileSHA = str(diff_item.a_blob)[0:7]                           # Buggy revision First 7 SHA code
                cleanFileSHA = str(diff_item.b_blob)[0:7]                           # Clean revision First 7 SHA code
                
                ### find changed lines ###
                diffInfo = str(diff_item.diff).split('\\n')
                changedLines = list()
                for line in diffInfo:                        
                    if "@@" in line:
                        changedLines.append(str(line[line.find('-')+1:line.find('+')-1]).replace(',', '/') + '-' + str(line[line.find('+')+1:line.rfind('@@')-1]).replace(',', '/'))                
                
                OUTFILE.write(time.strftime("%Y-%m-%d", time.gmtime(commit_list[commit_index].committed_date)) + ',' + diff_item.a_path + ',' + buggyFileSHA + ',' + cleanFileSHA + ',' + ','.join(changedLines) + '\n')
            
    OUTFILE.flush()        
    OUTFILE.close()
    
def downloadRev(PROJECT_ADDR):
    
    PROJECT_NAME = PROJECT_ADDR[PROJECT_ADDR.rfind('/')+1:PROJECT_ADDR.rfind('.git')]
    PROJECT_PATH = GIT_REPO_PATH + PROJECT_NAME + '/'
    COMMIT_LOG_PATH = '../../' + OUTPUT_PATH + PROJECT_NAME + '/COMMIT_LOG/'
    DOWNLOAD_PATH = '../../' + OUTPUT_PATH + PROJECT_NAME + '/DOWNLOAD'
    BUGGY_DOWNLOAD_PATH   = DOWNLOAD_PATH + '/BUGGY/'
    CLEAN_DOWNLOAD_PATH   = DOWNLOAD_PATH + '/CLEAN/'

    cwd = os.getcwd()
    os.chdir(PROJECT_PATH)

    if os.path.exists(BUGGY_DOWNLOAD_PATH): shutil.rmtree(BUGGY_DOWNLOAD_PATH)
    os.makedirs(BUGGY_DOWNLOAD_PATH)
    if os.path.exists(CLEAN_DOWNLOAD_PATH): shutil.rmtree(CLEAN_DOWNLOAD_PATH)
    os.makedirs(CLEAN_DOWNLOAD_PATH)

    num_lines = sum(1 for line in open(COMMIT_LOG_PATH + 'BUG_RELATED.txt'))              # Count modified revision files
    
    ### download specific revision files ###
    readLineNum = 0
    for line in open(COMMIT_LOG_PATH + 'BUG_RELATED.txt', 'r'):
        
        readLineNum += 1
        
        buggyRevisionNum = line.split(',')[2]                   # buggy file SHA
        cleanRevisionNum = line.split(',')[3]                   # clean file SHA
        filePath    = line.split(',')[1]                        # file path
        fileName    = filePath[filePath.rfind('/')+1:]          # file name  
        
        # if the file exist, skip downloading
        if os.path.exists(BUGGY_DOWNLOAD_PATH + '[' + buggyRevisionNum + ']' + fileName):                        
            continue
        if os.path.exists(CLEAN_DOWNLOAD_PATH + '[' + str(cleanRevisionNum) + ']' + fileName):        
            continue                
        
        # download buggy revision file
        cmd_result = os.system('git show ' + buggyRevisionNum + ' > ' + BUGGY_DOWNLOAD_PATH + '[' + buggyRevisionNum + ']' + fileName)        
        if not cmd_result == 0:
            print ('error occurred for buggy revision file...\n')
            pass
        else:
            # download clean revision file if buggy revision file is downloaded successfully
            cmd_result = os.system('git show ' + cleanRevisionNum + ' > ' + CLEAN_DOWNLOAD_PATH + '[' + cleanRevisionNum + ']' + fileName)
            if not cmd_result == 0:
                print ('error occurred for buggy revision file...\n')
                os.remove(BUGGY_DOWNLOAD_PATH + '[' + buggyRevisionNum + ']' + fileName)
                pass
            else:
                print (BUGGY_DOWNLOAD_PATH + '[' + buggyRevisionNum + ']' + fileName + ' (' + str(round((float(readLineNum)/num_lines)*100,2)) + '%)')
                
    os.chdir(cwd)

def on_rm_error(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)

def remove_project_dir(PROJECT_ADDR):
    PROJECT_NAME = PROJECT_ADDR[PROJECT_ADDR.rfind('/') + 1:PROJECT_ADDR.rfind('.git')]
    PROJECT_PATH = GIT_REPO_PATH + PROJECT_NAME + '/'

    shutil.rmtree(PROJECT_PATH, onerror=on_rm_error)                     # remove cloned repository