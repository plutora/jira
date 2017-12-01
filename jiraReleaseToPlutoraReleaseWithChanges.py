# python 2.7
# Creates Plutora Releases from Jira Releases (Versions, fixVersion)
# Attaches the Plutora Changes corresponding to the Jira Issues associated with the Jira Release (i.e., Jira issues with the fixVersion of the Release) 
#
# Currently, only running on company.plutora.com several GUIDs are hardcoded:
	# "systemId": "0d606b59-f6d5-e711-80c1-bc764e049ceb","system": "Lux",
	# "systemRoleType": "Impact","systemRoleDependencyTypeId": "15767d33-5146-410b-8755-0b451335c79b",
	# "releaseTypeId": "90d030c3-04a4-4c59-9e4a-90928293b8d0","releaseType": "Major",
	# "releaseStatusTypeId": "b723ec3f-2200-4c0b-aa98-eb381d049bfb","releaseStatusType": "Draft",
	# "releaseRiskLevelId": "bbc6670d-1414-48d9-ad35-fb1d1d5c21cf","releaseRiskLevel": "Low",
	# "organizationId": "a16c6d64-69d5-e711-80c1-bc764e049ceb","organization": "Hospitality",

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
#
# Set a valid Release Jira Project Name:
jiraProjectName = 'AP'

#---------------END of instructions--------------------------------------

# pip2 install jira
#from jira import JIRA
import re
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'restApiLibrary'))
# github.com/plutora/restApiLibrary
import plutora
import json
import requests

# Jira Credentials - load from jira.cfg
with open("jira.cfg") as data_file:
	jiraCfg = json.load(data_file)
j_url = jiraCfg["url"]
j_user = jiraCfg["username"]
j_password = jiraCfg["password"]

# Login to Plutora Jira instance
# jira = JIRA(server=j_url,basic_auth=(j_user,j_password))

# Get Jira releases
# GET /rest/api/2/project/{projectIdOrKey}/versions
jiraReleasesResponse = requests.get(j_url + "/rest/api/2/project/"+ jiraProjectName +"/versions", auth=(j_user, j_password))
jiraReleases = jiraReleasesResponse.json()

# Get existing Plutora Releases
existingReleases = plutora.listToDict(plutora.api("GET","releases"), "identifier", "id")

# For each Jira Release
for jiraRelease in jiraReleases:
	jiraReleaseName = jiraRelease['name']
	jiraIssuesReponse = requests.get(j_url + "/rest/api/2/search?jql=fixVersion = " + jiraReleaseName, auth=(j_user, j_password))
	jiraIssues = jiraIssuesReponse.json()['issues']
	
	jiraIssueUrl = j_url + "/projects/" + jiraProjectName + "/versions/" + jiraRelease['id']
	
	plutoraRelease = {
		"identifier": jiraReleaseName,
		"name": "Jira Version " + jiraReleaseName,
		"summary": "<a href=\"%s\">%s</a>" % (jiraIssueUrl,jiraIssueUrl),
		"releaseTypeId": "90d030c3-04a4-4c59-9e4a-90928293b8d0",
		"releaseType": "Major",
		"location": "",
		"releaseStatusTypeId": "b723ec3f-2200-4c0b-aa98-eb381d049bfb",
		"releaseStatusType": "Draft",
		"releaseRiskLevelId": "bbc6670d-1414-48d9-ad35-fb1d1d5c21cf",
		"releaseRiskLevel": "Low",
		"implementationDate": "2018-12-31T00:00:00",
		"displayColor": "#ccffff",
		"organizationId": "a16c6d64-69d5-e711-80c1-bc764e049ceb",
		"organization": "Hospitality",
		"plutoraReleaseType": "Independent",
		"releaseProjectType": "NotIsProject",
		"additionalInformation": []
	}
	if 'releaseDate' in jiraRelease:
		plutoraRelease["implementationDate"]=jiraRelease['releaseDate']
	if 'description' in jiraRelease:
		plutoraRelease["summary"] += "<div>%s</div>" % jiraRelease['description']


	# Add a system
	# POST releases/{id}/systems
	systemToAttach = {
		"systemId": "0d606b59-f6d5-e711-80c1-bc764e049ceb",
		"system": "Lux",
		"systemRoleType": "Impact",
		"systemRoleDependencyTypeId": "15767d33-5146-410b-8755-0b451335c79b",
		"systemRoleDependencyType": "Code Implementation Dependency"
	}

	if jiraReleaseName in existingReleases:
		createdReleaseId = existingReleases[jiraReleaseName]
		plutoraRelease["id"] = createdReleaseId
		print "Updating Plutora Release \"%s\"" % jiraReleaseName
		plutora.api('PUT',"releases/" + createdReleaseId,data=plutoraRelease)
	else:
		print "Creating Plutora Release \"%s\"" % jiraReleaseName
		createdRelease = plutora.api('POST',"releases",data=plutoraRelease)
		createdReleaseId = createdRelease['id']
		# TODO: test for whether the system is attached and move outside of this clause
		print "\tAttaching System \"%s\"" % "Lux"
		plutora.api("POST","releases/%s/systems" % createdReleaseId,data=systemToAttach)

	# PUT changes/{id}/deliveryReleases/{releaseId}
	releaseData = {
	  "releaseId": createdReleaseId,
	  "targetRelease": "true",
	  "actualDeliveryRelease": "true"
	}

	# Get existing Plutora Releases
	existingChanges = plutora.listToDict(plutora.api("GET","changes"), "name", "id")
	# Attach all Changes to release
	for jiraIssue in jiraIssues:
		jiraName = jiraIssue['fields']['summary']
		if jiraName in existingChanges:
			changeId = plutora.guidByPathAndName('changes',jiraName)
			print "\tAttaching Plutora Change \"%s\"" % jiraName
			plutora.api('put',"changes/%s/deliveryReleases/%s" % (changeId, createdReleaseId), releaseData )
		else:
			print "\t" + "\"" + jiraName + "\"" + " does not exist in Plutora Changes, skipping for Plutora Release " + jiraReleaseName