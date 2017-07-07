# python 2.7
# Create Plutora Release Activities from Jira Tasks
# To use, you'll need to provide valid Jira crendials and a credentials.cfg file for the Plutor login
# Also, make sure to reference a valid Release and Release Phase on lines 21 and 23

# Jira Credentials
j_user = 'provideAValidUserName'
j_password = 'provideAValidPassword'

# pip install jira
from jira import JIRA
import re
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'restApiLibrary'))
# github.com/plutora/restApiLibrary
import plutora

# Login to Plutora Jira instance
jira = JIRA(server='https://plutora.atlassian.net',basic_auth=(j_user,j_password))

# Select Release to apply the tasks/Activities to
releaseId = plutora.guidByPathAndName('releases','Test add issues from Jira')
# Select target Release Phase for the Activities
DEV_phaseId = plutora.guidByPathAndName('workitemnames/phases','DEV')

# Retrieve Jira tasks
jql_str = 'type = task and duedate>"2017-01-01"'
tasks = jira.search_issues(jql_str, startAt=0, maxResults=10, validate_query=True,
              fields=None, expand=None, json_result=None)
# For each Jira task found
for task in tasks:
	print "Processing Jira case %s" % jira.issue(task.key)
	taskHandle = jira.issue(task.id)
	Title = taskHandle.raw['fields']['summary']
	Description = "Jira case %s" % jira.issue(task.key)
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
		'AssignedToID': plutora.guidByPathAndName('users','greg.maxey@plutora.com',field="userName"),
		'AssignedWorkItemID': plutora.guidByPathAndName("releases/%s/phases" % releaseId, DEV_phaseId, field="workItemNameID"), # Phase
		'EndDate': "%sT00:00:00" % EndDate
	}
	plutora.api('POST',"releases/%s/activities" % releaseId ,data=activity)
