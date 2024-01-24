import os

KEYWORD = ['bug', 'error', 'fix', 'patch']

GIT_REPO_PATH = 'GitRepo/'
OUTPUT_PATH = 'OUTPUT/'
TOOL_PATH = 'Tools/'
PMD_PATH = TOOL_PATH + 'PMD-6.0.0/'
GIT_PROJECT_LIST = [projects.strip() for projects in open(GIT_REPO_PATH + 'GitRepoList.txt', 'r')]
JAVA_CATEGORY_LIST = ['']

if not os.path.exists(GIT_REPO_PATH):                   # create GIT_REPO path
    os.makedirs(GIT_REPO_PATH)

if not os.path.exists(OUTPUT_PATH):                     # create OUTPUT path
    os.makedirs(OUTPUT_PATH)

# if not os.path.exists(RELATED_ALERTS_PATH + 'BUGGY/'):  # RELATED_ALERT of BUGGY revision path
#     os.makedirs(RELATED_ALERTS_PATH + 'BUGGY/')
# if not os.path.exists(RELATED_ALERTS_PATH + 'CLEAN/'):  # RELATED_ALERT of CLEAN revision path
#     os.makedirs(RELATED_ALERTS_PATH + 'CLEAN/')