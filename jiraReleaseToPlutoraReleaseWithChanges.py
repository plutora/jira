# python 2.7
# Create Plutora Releases from Jira Releases including Changes/Issues
# To use, you'll need to provide a valid Jira crendials file (jira.cfg): 
#	{
#		"username":"JiraLoginName",
#		"password":"JiraLoginPassword"
#	}
# and a credentials.cfg file for the Plutor login:
#	{
#	  "urls":{
#		"authUrl":"https://usoauth.plutora.com/",
#		"baseUrl":"https://usapi.plutora.com/"
#	  },
#	  "credentials": {
#		"client_id":"XXXXXXXXXXXXXXXXXXXXXXXXXX",
#		"client_secret":"YYYYYYYYYYYYYYYYYYYYYYYYYY",
#		"username":"PlutoraLoginName",
#		"password":"PlutoraLoginPassword"
#		}
#	}
# Where usoath and usapi should be replaced by ukoath and ukapi is you're
# using a UK-based Plutora instance, and auoath and uaapi if in Asia.
# Set a valid Release name and one of its Phase names below:
jiraProjectName = 'AP'

#---------------END of instructions--------------------------------------

# pip2 install jira
from jira import JIRA
import re
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'restApiLibrary'))
# github.com/plutora/restApiLibrary
import plutora
import json
import requests

# Jira Credentials - load from jira.cfg
# with open("jira.cfg") as data_file:
	# jiraCfg = json.load(data_file)
# j_url = jiraCfg["url"]
# j_user = jiraCfg["username"]
# j_password = jiraCfg["password"]

# Login to Plutora Jira instance
# jira = JIRA(server=j_url,basic_auth=(j_user,j_password))

# Get Jira releases
jiraReleases = requests.get('https://plutora.atlassian.net/rest/api/2/project/AP/versions', auth=('yash.zolmajdi@plutora.com', 'Funtime1995'))
jiraRelease = jiraReleases.json()[0]
jiraReleaseName = jiraRelease['name']

jiraIssues = requests.get('https://plutora.atlassian.net/rest/api/2/search?jql=fixVersion = ' + jiraReleaseName, auth=('yash.zolmajdi@plutora.com', 'Funtime1995'))
jiraIssue = jiraIssues.json()['issues'][0]
jiraKey = jiraIssue['key']
jiraName = jiraIssue['fields']['summary']

plutoraRelease = {
	"identifier": jiraReleaseName,
	"name": "Jira Version " + jiraReleaseName,
	"summary": "",
	"releaseTypeId": "90d030c3-04a4-4c59-9e4a-90928293b8d0",
	"releaseType": "Major",
	"location": "",
	"releaseStatusTypeId": "b723ec3f-2200-4c0b-aa98-eb381d049bfb",
	"releaseStatusType": "Draft",
	"releaseRiskLevelId": "bbc6670d-1414-48d9-ad35-fb1d1d5c21cf",
	"releaseRiskLevel": "Low",
	"implementationDate": "2017-12-31T00:00:00",
	"displayColor": "#ccffff",
	"organizationId": "a16c6d64-69d5-e711-80c1-bc764e049ceb",
	"organization": "Hospitality",
	"plutoraReleaseType": "Independent",
	"releaseProjectType": "NotIsProject",
	"additionalInformation": []
}
createdRelease = plutora.api('POST',"releases",data=plutoraRelease)
createdReleaseId = createdRelease['id']

# Add a system
# POST releases/{id}/systems
systemToAttach = {
	"systemId": "0d606b59-f6d5-e711-80c1-bc764e049ceb",
	"system": "Lux",
	"systemRoleType": "Impact",
	"systemRoleDependencyTypeId": "15767d33-5146-410b-8755-0b451335c79b",
	"systemRoleDependencyType": "Code Implementation Dependency"
}
plutora.api('POST',"releases/%s/systems" % createdReleaseId,data=systemToAttach)

changeId = plutora.guidByPathAndName('changes',jiraName)
# PUT changes/{id}/deliveryReleases/{releaseId}
releaseData = {
  "releaseId": createdReleaseId,
  "targetRelease": "true",
  "actualDeliveryRelease": "true"
}
plutora.api('put',"changes/%s/deliveryReleases/%s" % (changeId, createdReleaseId), releaseData )

exit()


# Select Release to apply the tasks/Activities to
releaseId = plutora.guidByPathAndName('releases',releaseName)
# Select target Release Phase for the Activities
DEV_phaseId = plutora.guidByPathAndName('workitemnames/phases',releasePhase)

# Retrieve Jira tasks
tasks = jira.search_issues(jql_str, startAt=0, maxResults=10, validate_query=True,
              fields=None, expand=None, json_result=None)
print "Found %d Jira tasks." % len(tasks)
# For each Jira task found
for task in tasks:
	print "Processing Jira task %s" % jira.issue(task.key)
	taskHandle = jira.issue(task.id)
	Title = taskHandle.raw['fields']['summary']
	Description = "Jira task %s" % jira.issue(task.key)
	EndDate = taskHandle.raw['fields']['duedate']
	# Only create Activities with due dates
	if (EndDate==None):
		break
	#print "%sT00:00:00" % EndDate

	activity = {
		'Title': Title,
		'Description': Description,
		'ActivityDependencyType': 'None',
		'Type': 'Activity',
		'Status': 'NotStarted',
		'AssignedToID': plutora.guidByPathAndName('users',releaseStakeholder,field="userName"),
		'AssignedWorkItemID': plutora.guidByPathAndName("releases/%s/phases" % releaseId, DEV_phaseId, field="workItemNameID"), # Phase
		'EndDate': "%sT00:00:00" % EndDate
	}
	plutora.api('POST',"releases/%s/activities" % releaseId ,data=activity)
