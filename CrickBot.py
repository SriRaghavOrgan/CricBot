# -*- coding: utf-8 -*-
"""
Created on Fri Jul 14 15:29:12 2017

@author: Sriram
"""

# -*- coding: utf-8 -*-
"""
Created on Sun Jun 18 12:50:12 2017

@author: Sriram
"""

import os
from bs4 import BeautifulSoup
import requests
import re
import logging
import urllib

import random

from datetime import datetime, timedelta
from datetime import date as date
from difflib import SequenceMatcher
from collections import Counter

# Grab the Bot OAuth token from the environment.
BOT_TOKEN = os.environ["BOT_TOKEN"]

prevMessage = None
# Define the URL of the targeted Slack API resource.
# We'll send our replies there.
SLACK_URL = "https://slack.com/api/chat.postMessage"

Tutorial = {
        "tut_1" : "Live Matches now",
        "tut_2" : "Matches this week/next week/last week",
        "tut_3" : "Matches today/tomorrow/yesterday",
        "tut_4" : "Matches scheduled today/tomorrow",
        "tut_5" : "Matches scheduled this week/next week",
        "tut_6" : "Matches on 07-03-2017",
        "tut_7" : "Matches on week 07-03-2017",
        "tut_8" : "#matches this week/next week/last week",
        "tut_9" : "#matches today/tomorrow/yesterday",
        "tut_10" : "Teams which won today/yesterday",
        "tut_11" : "Teams which won this week/last week",
        "tut_12" : "Teams which lost today/yesterday",
        "tut_13" : "Teams which lost this week/last week",
        "tut_14" : "Drawn matches played today/yesterday",
        "tut_15" : "Abandoned matches today/yesterday",
        "tut_16" : "International matches today/tomorrow/yesterday",
        "tut_17" : "International matches this week/last week/next week",
        "tut_18" : "one-day matches this week/last week/next week",
        "tut_19" : "Test Matches this week/next week/last week",
        "tut_20" : "Ground name/country"
        }

internationalTeams = {
        "australia" : ["aus","australia","aussies","aussy","kangaroo"],
        "india" : ["ind","india","indians"],
        "pakistan" : ["pak","pakistan","pakistans"],
        "england" : ["eng","england","english"],
        "south africa" : ["sa","south africa","south africans","sas","chokers","southafrica","saf"],
        "new zealand" : ["new zea","newzea","nz","kiwi","kiwis","newzealand"],
        "sri lanka" : ["sl","sri lanka","srilanka","srilankans"],
        "west indies" : ["wi ","west indies","indies","carribeans","carribean"],
        "zimbabwe" : ["zim","zimbabwe","zimbabwes"],
        "bangladesh" : ["ban","bangla","bangladesh"],
        "kenya" : ["ken","kenya","kenyans"],
        "ireland" : ["ire","ireland","irel"],
        "canada" : ["canada","can","canadas"],
        "netherland" : ["nether","net","netherlands","neth"],
        "scotland" : ["scot","scotland","scotlands","scots","scots"],
        "afghanistan" : ["afg","afgh","afghans","afghanistan"],
        "usa" : ["usa","united states","us"]
        }

day = {
       "weeks" : ["current week","this week","last week","next week"],
       "days" : [" now","currently","current","live","today","yesterday","tomorrow"]
      }

gender = {
        "women" : ["women","womens","women's","female"]
        }

status = {
        "won" : ["win","winning","won","winner","victory","trimph","succeed","succeeding","succeeded","victorious"],
        "lost" : ["lose","lost","losing","loser","fail","failed","fails"],
        "abandoned" : ["abandoned","abandon","stopped","stop","halt","halted"],
        "drawn" : ["drawn","tie","draw"],
        "scheduled" : ["schedule","scheduled","scheduling","schedules"],
        "noresult" : ["no result", "no results"]
        }

category = {
        "international" : ["international","inter national", "icc","internationals","inter-national"],
        "county" : ["county", "domestic"],
        "t20" : ["twenty20", "twenty 20", "t20" , "t 20"],
        "odi" : ["odi","one-day","one day"],
        "test" : ["test","tests"],
        "under19" : ["under-19s","under-19","under19s","u19","u-19"],
        }

misc = {
        "number" : ["#","number of", "no of", "how many","#matches","#match","# matches"],
        }

result = {
        "matches" : ["matches","match"],
        "teams" : ["teams","team"],
        "series" : ["series","tournaments","tournament","championships","championship"],
        "ground" : ["ground","stadium","park","grounds"],
        "url" : ["url","link","website"],
        "overs" : ["over","overs"],
        "wickets" : ["wicket","wickets"]
        }

statusMessage = {
        "won" : ["{0} beat {1}"," {0} cruise to victory over {1}", "{0} crush {1}", "{0} defeat {1}"],
        "lost" : ["{0} lose" ,"{0} was defeated "]
        }

updateMessage = ["1. Whenever there is a wicket.","2. After every 5 overs","3. Whenever a batsman scores half-century/century",
                 "4. Whenever the runs in an over exceeds 10 runs","5. If there's a six", "6. When the match starts"]

preferenceTemplate = {"1" : False, "2" : False, "3" : False, "4" : False, "5" : False, "6" : False, "oldMatch" : None, "channelId" : None, "matchInfoList"  : None}

userPreferences = {
        "user001" : None
        }


def extractTeams(internationalTeams, response):
    
    teamsInResponse = None
    
    for key, values in internationalTeams.items():
        for value in values:
            if value in response:
                if teamsInResponse == None:
                    teamsInResponse = key
                elif teamsInResponse != key:
                    teamsInResponse +=  "$$" + key
                    break
                    
    return teamsInResponse
    
def checkStringPresenceInResponse(tempDict, tempString):
    for key, values in tempDict.items():
        for value in values:
            if value in tempString.lower():
                return key + "$$" + value;
    return None

def calculateSimilarity(string1, string2):
    return SequenceMatcher(None, string1, string2).ratio()

def checkDateMatch(string):
    dateRegExp = re.search("([0-9]{2}-[0-9]{2}-[0-9]{4})",string)
    if dateRegExp:
        return dateRegExp.group(1).strip()
    return None

def returnFormattedDate(string):
    return datetime.strptime(str(string), '%Y-%m-%d').strftime('%Y-%m-%d')  

def returnDate(d):
    if d > 0:
        newDate = date.today() + timedelta(days = d)
    else:
        newDate = date.today() + timedelta(days = d)
        
    return returnFormattedDate(newDate)

def combineList(listOne, listTwo, response):
    
    combinedList = []
    
    for valueOne in listOne:
        for valueTwo in listTwo:
            combinedList.append(valueOne + " " + valueTwo)
        
    return combinedList + listTwo            


def getMatchInfoList(userDay, cricDate):
    # Initializations
    matchInfoList = []
    
    try:
        respDate = "today"
        tempStr = userDay.split("$$")
        
        if tempStr[0] == "days":
            if cricDate != None:
                respDate = cricDate
            elif tempStr[1] == "today" or tempStr[1] == "current" or tempStr[1] == "currently" or tempStr[1] == "live":
                respDate = "today"
            elif tempStr[1] == "yesterday":
                respDate = returnDate(-1)
            elif tempStr[1] == "tomorrow":
                respDate = returnDate(1)
            
            matchPortInstance = MatchInfoPortfolio("day", respDate)
            matchInfoList = matchPortInstance.getMatchInfo()
        
        elif tempStr[0] == "weeks":
            if cricDate != None:
                respDate = cricDate
            elif tempStr[1] == "this week" or tempStr[1] == "current week":
                respDate = "current week"
            elif tempStr[1] == "last week":
                respDate = returnDate(-7)
            elif tempStr[1] == "next week":
                respDate = returnDate(7)
            
            matchPortInstance = MatchInfoPortfolio("week", respDate)
            matchInfoList = matchPortInstance.getMatchInfo()
        
        return matchInfoList
    
    except Exception as e:
        print(e)
        print ("Looks like there's a bug, let me troubleshoot and see why am I not able to tell you waht ")

def getMatchByGenderList(matchInfoList, userGender):
    
    matchList = []
    flag = False
    
    try:
        tempGender = userGender.split("$$")
        if matchInfoList != None and len(matchInfoList) != 0:
            for genderValue in gender[tempGender[0]]:
                for match in matchInfoList:
                    if genderValue in match.matchCategory.lower():
                        matchList.append(match)
                        flag = True
                
                if flag:
                    print("Checking here")
                    return matchList
        
        return matchInfoList
    
    except Exception as e:
        print(e)
        print("Getting match list with this filter seems to be problem !")
        
            
def getUserStatusMatchList(matchInfoList, userStatus, userTeam):

    matchList = []
    
    try:
        tempStatus = userStatus.split("$$")
        
        if matchInfoList != None and len(matchInfoList) != 0:
            for match in matchInfoList:
                if match.isCompleted:
                    if tempStatus[0] == "won" and not match.matchAbandoned and not match.matchNoResults and not match.matchDrawn:
                        matchList.append(match)                            
                    elif tempStatus[0] == "lost" and not match.matchAbandoned and not match.matchNoResults and not match.matchDrawn:
                        matchList.append(match)
                    elif tempStatus[0] == "drawn" and match.matchDrawn:
                        matchList.append(match)
                    elif tempStatus[0] == "abandoned" and match.matchAbandoned:
                        matchList.append(match)
                    elif tempStatus[0] == "noresult" and match.matchNoResults:
                        matchList.append(match)
                        
                else:
                    if tempStatus[0] == "scheduled":
                        matchList.append(match)
                        
            return matchList
        
        else:
            print (" There's an issue here" )
    
    except Exception as e:
        print(e)
        print ("Arrgh ! Looks like an issue in here. Couldn't fetch the details")

   
def getuserCategoryMatchList(matchInfoList, userCategory):
    
    matchList = []
    flag = False
    
    try:
        tempCategory = userCategory.split("$$")
                
        if len(matchInfoList) != 0:
            if tempCategory[0] == "test":
                for match in matchInfoList:
                    if match.matchType == "Test":
                        matchList.append(match)
            
            else:
                for categoryValue in category[tempCategory[0]]:
                    for match in matchInfoList:
                        if categoryValue in match.matchCategory.lower():
                            matchList.append(match)
                            flag = True
                
                if flag == True:
                     return matchList
    
        return matchList

    except Exception as e:
        print(e)
        print ("I just messed up with match categories !")
        
def getuserMiscMatchList(matchInfoList, userMisc):
    
    try:
        tempMisc = userMisc.split("$$")
        
        if matchInfoList == None or len(matchInfoList) == 0:
            print ("Looks like no matches were played")
        
        else:   
            if tempMisc[0] == "number":
                return len(matchInfoList)
            elif tempMisc[0] == "ground":
                for match in matchInfoList:
                    print(match.matchInfo)
            elif tempMisc[0] == "url":
                for match in matchInfoList:
                    print(match.matchurl)
                
    except Exception as e:
        print (e)
        print ("Ground names ??!! Uff, I don't see I could fetch the ground details. I'm sorry :(")
        
def getTeamSpecificMatchList(matchInfoList, userTeam):
    
    tempTeams = userTeam.split("$$")
    matchList = []
    
    try:
        if matchInfoList != None and len(matchInfoList) != 0:
            for match in matchInfoList:
                if len(tempTeams) == 1:
                    if match.teamOne.lower() in tempTeams[0] or match.teamTwo.lower() in tempTeams[0]:
                        print(match.teamOne +" Vs " + match.teamTwo)
                        matchList.append(match)
                    
                elif len(tempTeams) == 2:
                    if (match.teamOne.lower() in tempTeams[0] and match.teamTwo.lower() in tempTeams[1]) or (match.teamTwo.lower() in tempTeams[0] and match.teamOne.lower() in tempTeams[1]):
                        print(match.teamOne + " vs " + match.teamTwo)
                        matchList.append(match)
                        
            return matchList
        
        else:
            print ("There are no matches in my list !! Sorry that I couldn't give you an answer")
            
    except Exception as e:
        print(e)
        print("I find some problem in understanding the team name you just typed !")
        
def showUserResults(matchInfoList, userResult, userStatus, userDay):
    
    tempList = []
    tempStatus = None
    tempDay = None

    try:
        tempResult = userResult.split("$$")
        if userDay != None:
            tempDay = userDay.split("$$")
        if userStatus != None:
            tempStatus = userStatus.split("$$")
        
        if matchInfoList == None or len(matchInfoList) == 0:
            print (" I don't have any search results to show you now !")
            
        else:
            if tempResult[0] == "teams":
                count = 0
                for match in matchInfoList:
                    count +=1
                    if userStatus != None and tempStatus[0] == "won":
                        randNumber = random.randint(-1,3)
                        tempMessage = statusMessage["won"][randNumber].format(match.matchWinTeamName, match.matchLoseTeamName)
                        if tempDay[0] == "weeks":
                            tempMessage += " on " + match.matchDate
                            
                        tempList.append(str(count) + ". " + tempMessage)
                        
                        
                    elif userStatus != None and tempStatus[0] == "lost":
                        randNumber = random.randint(-1,1)
                        tempMessage = statusMessage["lost"][randNumber].format(match.matchLoseTeamName)
                        if tempDay[0] == "weeks":
                            tempMessage += " on " + match.matchDate
                            
                        tempList.append(str(count) + ". " + tempMessage)
                    
                    else:
                        tempList.append(str(count) + ". " + match.teamOne)
                        count += 1
                        tempList.append(str(count) + ". " + match.teamTwo)
                
                tempList.insert(0, "Well, the teams are here: ")
                return "\n".join(tempList)
            
            elif tempResult[0] == "matches":         
                count = 0
                for match in matchInfoList:
                    if match.teamOne != None and match.teamTwo != None:
                        if tempDay[0] == "weeks":
                            count += 1
                            tempList.append(str(count) + "." + match.teamOne + " Vs " + match.teamTwo + " on " + match.matchDate)
                        else:
                            count += 1
                            tempList.append(str(count) + "." + match.teamOne + " Vs " + match.teamTwo)
                            
                if tempList != None and len(tempList) != 0:
                    if len(tempList) == 1:
                        tempList.insert(0, "Well, the number of matches played is here  :\n" )
                        return "\n".join(tempList)
                    else:
                        tempList.insert(0, "Well, the number of matches played here are : \n" )
                        return "\n".join(tempList)
        
    
    except Exception as e:
        print(e)
        print("I don't have any search results to show you now !")
                
        
        
class MatchInfoPortfolio():
    
    def __init__(self, view, date):
        self.view = view
        self.date = date
        self.matchInfoUrl = "http://www.espncricinfo.com/ci/engine/match/index.html"
        self.soupInstance = self.getSoupInstance(view,date)
        self.matchType = self.getMatchType()
        self.matchInformation = self.getMatchInformation()
        self.matchList = []

    def getSoupInstance(self, view, date):
        if view == "day":
            if date != "today":
                date = "date="+date
                self.matchInfoUrl = self.matchInfoUrl + "?" + date
        elif view == "week":
            if date == "current week":
                self.matchInfoUrl = self.matchInfoUrl+"?view=week"
            else:
                date = "date="+date
                self.matchInfoUrl = self.matchInfoUrl+"?"+date+";"+"view=week"
        
        print(self.matchInfoUrl)
        return Utility.getBeautifulSoupInstance(self.matchInfoUrl)
            
    def getMatchType(self):
        if self.date == "today":
            return self.soupInstance.find("section", {"id" : "live-match-data"}).find_all("div", {"class" : "match-section-head"})
        else:
            return self.soupInstance.find("section", {"class" : "matches-content"}).find_all("div", {"class" : "match-section-head"})
    
    def getMatchInformation(self):
        if self.date == "today":
            return self.soupInstance.find("section", {"id" : "live-match-data"}).find_all("section", {"class" : "matches-day-block"})
        else:
            return self.soupInstance.find("section", {"class" : "matches-content"}).find_all("section", {"class" : "matches-day-block"})
    
    def getMatchInfo(self):
        for matchType,matchInfo in zip( self.matchType, self.matchInformation):
            allMatches = matchInfo.find_all("section", {"class" : "default-match-block"})
            for individualMatchSection in allMatches:
                matchInfo = MatchInfo(matchType.text, individualMatchSection)
                self.matchList.append(matchInfo)
                
        return self.matchList
    
class MatchInfo():
    
    def __init__(self, matchCategory, matchSection):
        
        self.matchSection = matchSection
        self.matchCategory = matchCategory
        self.matchType = None

        self.isCompleted = False        
        self.matchWinWickets = None
        self.matchWinBallsRemaining = None
        self.matchWinRuns = None
        self.matchWinTeamName = None
        self.matchLoseTeamName = None
        self.matchDrawn = False
        self.matchNoResults = False
        self.matchAbandoned = False
        
        self.isLive = self.isMatchLive()
        self.matchDate = self.getMatchDate()
        self.matchNumber = self.getMatchNumber()
        self.matchInfo = self.getMatchInfo()
        self.teamOne = self.getTeamName("innings-info-1")
        self.teamTwo = self.getTeamName("innings-info-2")        
        self.teamOneScore = self.getTeamScore("innings-info-1")
        self.teamTwoScore = self.getTeamScore("innings-info-2")
        self.teamOneWickets = self.getTeamWickets("innings-info-1")
        self.teamTwoWickets = self.getTeamWickets("innings-info-2")
        self.teamOneOvers = self.getTeamOvers("innings-info-1")
        self.teamTwoOvers = self.getTeamOvers("innings-info-2")
        self.matchStatus = self.getMatchStatus()
        self.matchURL = self.getMatchURL()
        self.matchGMT = None
        
        self.firstInningsURL = self.getFirstInningsURL()
        self.secondInningsURL = self.getSecondInningsURL()
        
        self.firstInningsObject = None
        self.secondInningsObject = None

        
    def isMatchLive(self):
        try:
            spanLive = self.matchSection.find("span", {"class" : "live-icon"})
            if spanLive:
                return True
            else:
                return False
        
        except Exception as e:
            return False
    
    def getMatchDate(self):
        
        matchDate = None
        try:
            allTags = self.matchSection.find_all()
            for eachTag in allTags:
                
                OtherMatchesdateRegExp = re.search('((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [0-9]{1,2},[ ]?[0-9]{4})', eachTag.text.strip())
                testMatchdateRegExp = re.search('((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [0-9]{1,2}-[0-9]{1,2},[ ]?[0-9]{4})', eachTag.text.strip())
                if OtherMatchesdateRegExp:
                    self.matchType="Others"
                    matchDate = OtherMatchesdateRegExp.group(1).strip()
                    break
                    #return OtherMatchesdateRegExp.group(1).strip()
                elif testMatchdateRegExp:
                    self.matchType = "Test"
                    matchDate =  testMatchdateRegExp.group(1).strip()
                    break
            
            return matchDate
                
        except Exception as e:
            return "Error"

    def getMatchNumber(self):  
        
        try:
            matchNumberText = self.matchSection.find("span", {"class" : "match-no"}).find("a").text
            matchNumberResult = re.search('([0-9]{1,3}(st|th|nd|rd)) (ODI|Test|Match) at', matchNumberText)                                        
            if matchNumberResult:
                return matchNumberResult.group(1)
            else:
                return None
            
        except Exception:
            return None
    
    def getMatchInfo(self):
        
        try:
            matchInfoText = self.matchSection.find("span", {"class" : "match-no"}).find("a").text
            matchInfoResult = re.search(' at (.*)', matchInfoText)                                        
            if matchInfoResult:
                return matchInfoResult.group(1).strip()
            else:
                return None
            
        except Exception:
            return None
        
    def  getTeamName(self, attribute):
        
        try:
            teamInfoText = self.matchSection.find("div", {"class" : attribute}).text.strip()
            teamInfoResult = re.search('([-a-zA-Z0-9 ]+)    ',teamInfoText)
            if teamInfoResult:
                return teamInfoResult.group(1)
            else:
                return teamInfoText
        except Exception:
            return None
        
    def getTeamScore(self, attribute):
        
        try:
            scoreInfoText = self.matchSection.find("div", {"class" : attribute}).find("span",{"class" : "bold"}).text.strip()
            if "Test" not in self.matchType:
                scoreInfoResult = re.search('^([0-9]+)(\/)?', scoreInfoText) 
                if scoreInfoResult:
                    return scoreInfoResult.group(1)
                else:
                    return scoreInfoResult
                
        except Exception:
            return None

    def getTeamWickets(self, attribute):
        
        try:
            wicketText = self.matchSection.find("div", {"class" : attribute}).find("span",{"class" : "bold"}).text.strip()
            if "Test" not in self.matchType:
                wicketResult = re.search('/([0-9]|10) ', wicketText) 
                allWicketsResult = re.search('([0-9]+) \(', wicketText)
                if wicketResult:
                    return wicketResult.group(1)
                elif allWicketsResult:
                    return "All Out"
                else:                    
                    return wicketResult
                
        except Exception:
            return None
    
    def getTeamOvers(self, attribute):
        
        try:
            scoreInfoText = self.matchSection.find("div", {"class" : attribute}).find("span",{"class" : "bold"}).text.strip()
            if "Test" not in self.matchType:
                scoreInfoResult = re.search('\(([0-9]{0,3}(\.[0-6])?)', scoreInfoText)
                if scoreInfoResult:
                    return scoreInfoResult.group(1)
                else:
                    return scoreInfoResult
                
        except Exception:
            return None
        
    def getMatchStatus(self):

        try:
            matchStatusText = self.matchSection.find("div", {"class" : "match-status"}).find("span",{"class" : "bold"}).text
            gmtTimeText = self.matchSection.find("div", {"class" : "match-status"}).text
            
            if "Test" not in self.matchType:
                matchStatusResult = re.search('Match scheduled to begin at [0-9]{2}:[0-9]{2} local time', matchStatusText)
                matchWinWicketsResult = re.search('(.*) won by (.*) \((with [0-9]{0,3} ball(s)?) remaining\)', matchStatusText)
                matchWinRunsResult = re.search('(.*) won by ([0-9]{1,3}) run(s)?', matchStatusText)
                matchDrawnResult = re.search('Match drawn', matchStatusText)
                matchNoResult = re.search('No result', matchStatusText)
                matchAbandoned = re.search('Match abandoned', matchStatusText)
                
                if matchStatusResult:
                    matchStatusResult = re.search('(\(.*\))', gmtTimeText)
                    gmtTimeResult = re.search("([0-9]{2}:[0-9]{2}.*(?=GMT))",gmtTimeText)
                    if gmtTimeResult:
                        self.matchGMT = gmtTimeResult.group(1)
                    else:
                        self.matchGMT = None
                    return matchStatusResult.group(1)
                
                elif matchWinWicketsResult:
                    self.isCompleted = True
                    self.matchWinTeamName = matchWinWicketsResult.group(1).strip()
                    self.matchWinWickets = matchWinWicketsResult.group(2).strip()
                    self.matchWinBallsRemaining = matchWinWicketsResult.group(3).strip()
                    self.matchWinRuns = None
                    if self.matchWinTeamName in self.teamOne:
                        self.matchLoseTeamName = self.teamTwo
                    else:
                        self.matchLoseTeamName = self.teamOne
                        
                elif matchWinRunsResult:
                    self.isCompleted = True
                    self.matchWinTeamName = matchWinRunsResult.group(1).strip()
                    self.matchWinRuns =  matchWinRunsResult.group(2).strip()
                    self.matchWinWickets = None
                    self.matchWinBallsRemaining = None
                    if self.matchWinTeamName in self.teamOne:
                        self.matchLoseTeamName = self.teamTwo
                    else:
                        self.matchLoseTeamName = self.teamOne
                
                elif matchDrawnResult:
                    self.isCompleted = True
                    self.matchDrawn = True
                
                elif matchNoResult:
                    self.isCompleted = True
                    self.matchNoResults = True
                    
                elif matchAbandoned:
                    self.isCompleted = True
                    self.matchAbandoned = True
                
            return matchStatusText
            
        except Exception as e:
            return None   
        
    def getMatchURL(self):
        
        try:
            matchUrlText = self.matchSection.find("span", {"class" : "match-no"}).find("a")['href']
            matchUrlText = "http://www.espncricinfo.com" + matchUrlText            
            return matchUrlText
        
        except Exception:
            return None
        
    def getFirstInningsURL(self):
        return self.matchURL +  "?innings=1;view=commentary"
    
    def getSecondInningsURL(self):
        return self.matchURL + "?innings=2;view=commentary"
    
    def firstInningsObject(self):
        soup = Utility.getBeautifulSoupInstance(self.firstInningsURL)
        commentaryDivision = soup.find_all("div", {"class": "commentary-event"})
        
        self.firstInningsObject = Innings(self.teamOne,self.teamTwo, self.firstInningsURL, commentaryDivision)
        return self.firstInningsObject
    
    def secondInningsObject(self):
        soupInstance = Utility.getBeautifulSoupInstance(self.secondInningsURL)
        commentaryDivision = soupInstance.find_all("div", {"class": "commentary-event"})
        
        self.secondInningsObject = Innings(self.teamOne,self.teamTwo, self.firstInningsURL, commentaryDivision)
        return self.secondInningsObject

class Innings():
    
    def __init__(self, battingTeam, bowlingTeam, inningsURL, commentsDivision):
        self.isCompleted = False
        self.battingTeam = battingTeam
        self.bowlingTeam = bowlingTeam
        self.noFours = 0
        self.noSixeers = 0
        self.overs = 0
        self.wideBalls = 0
        self.noBalls = 0
        self.legBye = 0
        self.penalty = 0
        self.runs = 0
        self.wickets = 0
        self.inningsURL = inningsURL
        self.commentsDivision = commentsDivision
        self.oversDictionary = {}
        self.batsmenDict = {}
        self.bowlersDict = {}
        
    def addOverNumber(self):
        self.overs += 1
        
    def addWides(self, wideRuns):
        self.wideBalls += wideRuns
    
    def addNoBalls(self, noBallRuns):
        self.noBalls += noBallRuns
    
    def addLegByes(self):
        self.legBye += 1
        
    def addPenalty(self, runs):
        self.penalty += runs
    
    def addRuns(self, runs):
        self.runs += int(runs)
        if runs == 4:
            self.noFours += int(runs)
        elif runs == 6:
            self.noSixers += int(runs)
    
    def addWickets(self):
        self.wickets += 1
    
    def addOverObjects(self):
        tempRuns = 0
        isWicket = False
        batsman = None
        bowler = None
        ballObjects = []
        
        for commentDivision in self.commentsDivision:

            if isWicket:
                Utility.wicketDetails(batsman, commentDivision)
                bowler.addWicketBatsmanName(batsman.batsmanName, batsman.wicketType)
                isWicket = False
                continue
            
            print(commentDivision)
            ball = Ball(commentDivision)
            if ball.batsmanName not in self.batsmenDict:
                batsman = Batsman(ball.batsmanName)
                self.batsmenDict[ball.batsmanName] = batsman
            else:
                batsman = self.batsmenDict[ball.batsmanName]
                
            if ball.bowlerName not in self.bowlersDict:
                bowler = Bowler(ball.bowlerName)
                self.bowlersDict[ball.bowlerName] = bowler
            else:
                bowler = self.bowlersDict[ball.bowlerName]
                
            if ball.getBallNumber() == 6:
                
                tempRuns += ball.runs
                
                ballObjects.append(ball)
                batsman.addBallObjects(ball.getCommentOversDiv(),ball)
                
                if ball.getOverNumber() not in self.oversDictionary:
                    over = Over()
                    over.setBowlerName(ball.bowlerName)
                    
                    over.setOverNumber(ball.getOverNumber())
                    self.addOverNumber()                    
                    
                    for ball in ballObjects:
                        
                        over.setOverRuns(ball.runs)
                        bowler.addRuns(ball.runs)
                        self.addRuns(ball.runs)
                        
                        batsman = self.batsmenDict[ball.batsmanName]
                        
                        if not ball.isWide and not ball.isNoBall:
                            batsman.addRunsScored(ball.runs)
                            # Do not add these extras to batsman runs
                        
                        if ball.isWide:
                            over.addOverWides(ball.wideRuns)
                            self.addWides(ball.wideRuns)
                            bowler.addWides(ball.wideRuns)
                        
                        if ball.isNoBall:
                            over.addOverNoballs(ball.noBallRuns)
                            self.addNoBalls(ball.noBallRuns)
                            bowler.addNoBalls(ball.noBallRuns)
                        
                        if ball.isLegBye:
                            over.setLegByes(ball.getLegByes())                        
                            self.addLegByes()
                        
                        if ball.isWicket:
                            over.addOverWickets()
                            self.addWickets()
                    
                    over.setBallObjects(ballObjects)                      
                    self.oversDictionary[over.overNumber] = over
                    
                    bowler.addOversCount()
                    bowler.addOvers(over)
                    if tempRuns == 0:
                        bowler.addMaidenOvers()
                    else:
                        tempRuns = 0
                        
                    ballObjects = []
                    
                else:
                    print("Here is the error.Kindly check here - Error")
            else:
                if ball.isWicket:
                    isWicket = True
                    
                ballObjects.append(ball)
                tempRuns += ball.runs
                batsman.addBallObjects(ball.getCommentOversDiv(),ball)
                
   
class Over():
    
    def __init__(self):
        self.overNumber = 0
        self.overBowlerName = None
        self.overRuns = 0
        self.overWides = 0
        self.overNoballs = 0
        self.overWickets = 0
        self.ballObjects = []
        
    def setOverNumber(self, overNumber):
        self.overNumber = overNumber
        
    def setBowlerName(self, bowlerName):
        self.overBowlerName = bowlerName
    
    def setOverRuns(self, run):
        self.overRuns += int(run)
    
    def addOverWides(self, wideRuns):
        self.overWides += wideRuns
    
    def addOverNoballs(self, noBallRuns):
        self.overNoballs += noBallRuns
    
    def addOverWickets(self):
        self.overWickets += 1

    def setBallObjects(self, ballObjects):
        self.ballObjects = ballObjects

class Batsman():

    def __init__(self, batsmanName):
        self.batsmanName = batsmanName
        self.ballsPlayed = 0
        self.runsScored = 0
        self.strikeRate = 0
        self.runsInFours = 0
        self.runsInSixers = 0
        self.runsInSingles = 0 
        self.runsInDoubles = 0
        self.runsInThrees = 0
        self.dotBalls = 0
        self.minutesPlayed = 0
        self.isOut = False
        self.wicketType = None
        self.wicketFielder = None
        self.wicketBowler = None
        self.ballDictionary = {}
        
    def setBowlerName(self, bowlerName):
        self.wicketBowler = bowlerName
    
    def addBallsPlayed(self):
        self.ballsPlayed += 1
        
    def addRunsScored(self, run):
        self.runsScored += int(run)
        self.ballsPlayed += int(1)
        
        if run == 0:
            self.dotBalls += 1
        elif run == 1:
            self.runsInSingles += 1
        elif run  == 2:
            self.runsInDoubles += 1
        elif run == 3:
            self.runsInThrees +=1
        elif run == 4:
            self.runsInFours += 1
        elif run == 6:
            self.runsInSixers += 1
    
    def setMinutesPlayed(self, minutes):
        self.minutesPlayed = minutes
    
    def addBallObjects(self, over, ballObject):
        if over in self.ballDictionary:
            self.ballDictionary[over] = ballObject
        else:
            self.ballDictionary[over] = ballObject
        
class Bowler():
    
    def __init__(self, bowlerName):
        
        self.bowlerName = bowlerName
        self.noBalls = 0
        self.wides = 0
        self.maidenOvers = 0
        self.oversCount = 0
        self.runs = 0
        self.economyRate = 0
        self.dotBalls = 0
        self.runsInSingles = 0
        self.runsInDoubles = 0
        self.runsInThrees = 0
        self.runsInFours = 0
        self.runsInSixers = 0
        self.wicketBatsman = {}
        self.oversDict = {}
        
    def addNoBalls(self, noBalls):
        self.noBalls += noBalls
    
    def addWides(self, wides):
        self.wides += int(wides)
    
    def addMaidenOvers(self):
        self.maidenOvers += int(1)
    
    def addOversCount(self):
        self.oversCount += int(1)
    
    def addRuns(self, run):
        self.runs += int(run)
        
        if run == 0:
            self.dotBalls += 1
        elif run == 1:
            self.runsInSingles += 1
        elif run  == 2:
            self.runsInDoubles += 1
        elif run == 3:
            self.runsInThrees += 1
        elif run == 4:
            self.runsInFours += 1
        elif run == 6:
            self.runsInSixers += 1
        
    def addWicketBatsmanName(self, batsmanName, wicketType):
        self.wicketBatsman[batsmanName] = wicketType
        
    def addOvers(self, overObject):
        self.oversDict[self.oversCount] = overObject
    
    def getOverDict(self, overNumber):
        return self.oversDict[overNumber]
    
class Ball():
    
    def __init__(self, commentaryDiv):
        self.commentaryDiv= commentaryDiv
        self.commentText = self.getCommentTextDiv()
        self.commentOvers = self.getCommentOversDiv()
        self.commentImportant = self.getCommentImportantSpan()
        self.bowlerName = self.getBowlerName()
        self.batsmanName = self.getBatsmanName()
        self.overNumber = self.getOverNumber()
        self.ballNumber = self.getBallNumber()
        self.isWicket = False
        self.isWide = False
        self.wideRuns = 0
        self.isNoBall = False
        self.noBallRuns = 0
        self.isLegBye = False
        self.runs = self.getRuns()

    def getCommentOversDiv(self):
        commentOversDiv = self.commentaryDiv.find("div", {"class" : "commentary-overs"})
        if commentOversDiv:
            return commentOversDiv.text.lower()
        else:
            return "error"
        
    def getCommentTextDiv(self):
        commentTextDiv = self.commentaryDiv.find("div", {"class" : "commentary-text"})
        if commentTextDiv:
            return commentTextDiv.text
        else:
            return "error"
    
    def getCommentImportantSpan(self):
        commentImportantSpan = self.commentaryDiv.find("div", {"class" : "commentary-text"}).find("span",  {"class" : "commsImportant"})
        if commentImportantSpan:
            return commentImportantSpan.text.lower()
        else:
            return "error"
        
    def getBowlerName(self):
        try:
            ballDetail = self.commentText.split(",")[0]
            m = re.search("([a-zA-Z]+)(?= to)", ballDetail)
            return m.group(0)
        
        except Exception:
            return None    
    
    def getBatsmanName(self):
        try:
            ballDetail = self.commentText.split(",")[0]
            m = re.search("(?<=to )([a-zA-Z ]+)", ballDetail)
            return m.group(0)
        
        except Exception:
            return None
    
    def getOverNumber(self):
        try:
            return int(self.commentOvers.split(".")[0])+1
        except Exception:
            return None
    
    def setWicket(self):
        self.isWicket = True
        
    def getBallNumber(self):
        try:
            return int(self.commentOvers.split(".")[1])
        except Exception:
            return "error"
    
    def getRuns(self):
        
        try:
            if self.commentImportant != "error":
                runText = (self.commentImportant).lower()
                runText = runText.strip()
                if runText == "out" or runText == "OUT":
                    self.setWicket()
                    return 0
                elif runText == "four":
                    return 4
                elif runText == "six":
                    return 6
            
            runText = self.commentText.split(",")[1]
            runText = runText.lower()
            runText = runText.strip()
            #print(runText) 
            try:
                m = re.search('^([0-9]) wide(s)?$', runText)
                self.wideRuns = int(m.group(1))
                self.isWide = True
            
            except Exception as e:
                self.isWide = False
            
            try:    
                regexp = re.compile(r'^[0-9] no ball(s)?$')
                if regexp.search(runText):
                    self.isNoBall = True
                    self.noBallRuns = int(1)
            
            except Exception as e:
                self.isNoBall = False
                
            try:
                regexp = re.compile(r'^\(no ball\) [0-9] run(s)?')
                if regexp.search(runText):
                    self.isNoBall = True
                    self.noBallRuns = int(2)
            
            except Exception as e:
                self.isNoBall = False
                
            m = re.search("[0-9]+[ ]*run(s)?", runText)
            runText = m.group(0)
            
            if runText == "0" or runText == "0" or runText == "0 runs" or runText == "no run" or runText == "zero" or "zero" in runText:
                return 0
            elif runText == "1" or "1 run" in runText or runText == "one" or "one" in runText:
                return 1
            elif runText == "2" or  "2 run" in runText or runText == "two" or "two" in runText:
                return 2
            elif runText == "3" or  "3 run" in runText or runText == "three" or "three" in runText:
                return 3
            elif runText == "4" or "4 run" in runText or runText == "four" or "four" in runText:
                return 4
            elif runText == "5" or "5 run" in runText or runText == "5 runs" or runText == "five" or "five" in runText:
                return 5
            elif runText == "6" or "6 run" in runText or runText == "6 runs" or runText == "six" or "six" in runText:
                return 6
            else:
                print(Utility.textToNumber(runText))
                return Utility.textToNumber(runText)
                
        except Exception:
            return 0
            

class Utility():
    
    @staticmethod
    def textToNumber(runText):
        try:
            if runText == "7" or runText == "7 run" or runText == "7 runs" or runText == "seven" or "seven" in runText:
                return 7
            elif runText == "8" or runText == "8 run" or runText == "8 runs" or runText == "eight" or "eight" in runText:
                return 8
            elif runText == "9" or runText == "9 run" or runText == "9 runs" or runText == "nine" or "nine" in runText:
                return 9
            elif runText == "10" or runText == "10 run" or runText == "10 runs" or runText == "ten" or "ten" in runText:
                return 10
            else:
                 m = re.search("([0-9]+)", runText)
                 return int(m.group(1))
             
        except Exception:
            return "error" 
    
    def wicketDetails(batsman, commentDiv):
        
        try:
            wicketText = commentDiv.find("div", {"class" : "commentary-text"}).text
            
            batsman.isOut = True            
            m = re.search("SR: ([0-9\.]+)",wicketText)
            batsman.strikeRate = m.group(1)
            
            catchWicketRegExp = re.compile(r'[a-zA-Z ]+ c [a-zA-Z ]+ b [a-zA-Z ]+')
            runoutWicketRegExp = re.compile(r'[a-zA-Z ]+ run out [0-9]+ ')
            lbwWicketRegExp = re.compile(r'[a-zA-Z ]+ lbw [a-zA-Z ]+')
            bowledWicketRegExp = re.compile(r'[a-zA-Z ]+ b [a-zA-Z ]+')
            hitWicketRegExp = re.compile(r'[a-zA-Z ]+ hit wicket b [a-zA-Z ]+')
            
            if catchWicketRegExp.search(wicketText):                                
                # Batsman Name
                m = re.search("([a-zA-Z ]+) c ", wicketText)
                batsman.batsmanName = m.group(1).strip()
                  
                # Catch - FielderName
                m = re.search(" c ([a-zA-Z ]+) b ", wicketText)
                batsman.wicketType = "Catch"
                batsman.wicketFielder = m.group(1).strip()
                  
                # BowlerName
                m = re.search(" b ([a-zA-Z ]+) [0-9]+", wicketText)
                batsman.wicketBowler = m.group(1).strip()
              
              
            elif runoutWicketRegExp.search(wicketText):
                #Batsman Name
                m = re.search("([a-zA-Z ]+) run out", wicketText)
                batsman.batsmanName = m.group(1).strip()
                
                batsman.wicketFielder = None
                batsman.wicketBowler = None
                batsman.wicketType = "Run Out"

            elif lbwWicketRegExp.search(wicketText):
                #Batsman name
                m = re.search("([a-zA-Z ]+) lbw ", wicketText)
                batsman.batsmanName = m.group(1).strip()
                
                m = re.search(" lbw b ([a-zA-Z ]+)", wicketText)
                batsman.wicketBowler = m.group(1).strip()
                
                batsman.wicketFielder = None
                batsman.wicketType = "LBW"
                
            elif bowledWicketRegExp.search(wicketText):
                
                #Batsman Name
                m = re.search("([a-zA-Z ]+) b ", wicketText)
                batsman.batsmanName = m.group(1).strip()
                
                m = re.search(" b ([a-zA-Z ]+)", wicketText)
                batsman.wicketBowler = m.group(1).strip()
                
                batsman.wicketFielder = None
                batsman.wicketType = "Bowled"
                
            elif hitWicketRegExp.search(wicketText):
                
                #Batsman Name
                m = re.search("([a-zA-Z ]+) hit wicket ", wicketText)
                batsman.batsmanName = m.group(1).strip()
                
                #Bowler Name
                m = re.search(" hit wicket b ([a-zA-Z ]+)", wicketText)
                batsman.wicketBowler = m.group(1).strip()
                
                batsman.wicketFielder = None
                batsman.wicketType = "Hit Wicket"
            
            #Batsman RunScored
            m = re.search(" ([0-9]+) ", wicketText)
            batsman.runsScored = int(m.group(1).strip())
          
            #Batsman total Number of Minutes Played
            #m = re.search(" \(([0-9]+)m ", wicketText)
            #batsman.minutesPlayed = m.group(1).strip()
         
            # Batsman total Number of balls played
            m = re.search("m ([0-9]+)b ", wicketText)
            batsman.ballsPlayed = int(m.group(1).strip())
          
            # Batsman runs in Fourrs
            m = re.search(" ([0-9]+)x4 ", wicketText)
            batsman.runsInFours = int(m.group(1).strip())
          
            #Batsman runs in Sixers
            m = re.search(" ([0-9]+)x6\)", wicketText)
            batsman.runsInSixers = int(m.group(1).strip())
            
        except Exception as e:
            print (e)
    
    def getBeautifulSoupInstance(url):
        urlPage = requests.get(url)
        return BeautifulSoup(urlPage.text, "html.parser")
         

def postMessage(message, BOT_TOKEN, channel_id):
    
    data = urllib.parse.urlencode((("token", BOT_TOKEN),("channel", channel_id),("text", message)))
    data = data.encode("ascii")

    request = urllib.request.Request(SLACK_URL, data=data, method="POST")
    request.add_header( "Content-Type", "application/x-www-form-urlencoded")
        
    urllib.request.urlopen(request).read()
    return "200 OK"

        
def handler(data, context):
    """Handle an incoming HTTP request from a Slack chat-bot.
    """
    # Grab the Slack event data.
    slack_event = data['event']
    
    
    # We need to discriminate between events generated by 
    # the users, which we want to process and handle, 
    # and those generated by the bot.
    if "bot_id" in slack_event:
        logging.warn("Ignore bot event")
    else:
        # Get the text of the message the user sent to the bot,
        # and reverse it.
        text = slack_event["text"]
        
        if "user" in slack_event:
            userId = slack_event["user"]
            channelId = slack_event["channel"]
            print (userId + " ::: " + channelId)
            
            if userPreferences[userId] is None:
                preferenceTemplate["channelId"] = channelId
                userPreferences[userId] = preferenceTemplate
                
                if text == "update":
                    message = "Here I come to help you get updated about cricket !\nWhat do you want me to do ? Choose one among them :"
                    message += "\n".join(updateMessage)
                    prevMessage = "update"
                    postMessage(message, BOT_TOKEN, channelId)
                    
                elif prevMessage == "update":            
                    if text.isdigit() and int(text) >=1 and int(text) <=6: 
                        if int(text) == 1:
                            postMessage(" Just Checking", BOT_TOKEN, channelId)
            
            
    
    text = "teams those won yestereday"
    response = text.lower() 
    
    userDay = checkStringPresenceInResponse(day,response)
    userGender = checkStringPresenceInResponse(gender, response)
    userStatus = checkStringPresenceInResponse(status,response)
    userCategory = checkStringPresenceInResponse(category,response)
    userMisc = checkStringPresenceInResponse(misc, response)
    userTeam = extractTeams(internationalTeams, response)
    userResult = checkStringPresenceInResponse(result, response)
    userDate = checkDateMatch(response)
    
    if userDay == None and userStatus == None and userCategory == None and userMisc == None and userDate == False:
        print("I think I'm not good enough to understand.")
        
    else:
        
        matchInfoList = []
        
        if userDay != None:
            matchInfoList = getMatchInfoList(userDay, None)
            userPreferences[userId]["matchinfolist"] = matchInfoList
            print(userPreferences)
        
        if userGender != None:
            print("User Gender :::::::" + userGender)
            matchInfoList = getMatchByGenderList(matchInfoList, userGender)
    
        if userTeam != None:
            print ("user Team :::: " + userTeam)
            matchInfoList = getTeamSpecificMatchList(matchInfoList, userTeam)
            
        if userStatus != None:
            print("User status ::::" + userStatus)
            matchInfoList = getUserStatusMatchList(matchInfoList,userStatus, userTeam)
            print(matchInfoList)
            
        if userCategory != None:
            print("User Category ::::" + userCategory)
            matchInfoList = getuserCategoryMatchList(matchInfoList, userCategory)
            
        if userMisc != None:
            print("User Misc ::::" + userMisc)
            getuserMiscMatchList(matchInfoList, userMisc)
            
        if userResult != None:
            print("User Result ::::::: " + userResult)
            print(matchInfoList)
            message = showUserResults(matchInfoList, userResult, userStatus, userDay)
            print(message)
       
                
            '''channel_id = slack_event["channel"]
        
            # We need to send back three pieces of information:
            #     1. The reversed text (text)
            #     2. The channel id of the private, direct chat (channel)
            #     3. The OAuth token required to communicate with 
            #        the API (token)
            # Then, create an associative array and URL-encode it, 
            # since the Slack API doesn't not handle JSON (bummer).
            data = urllib.parse.urlencode(
                (
                    ("token", BOT_TOKEN),
                    ("channel", channel_id),
                    ("text", message)
                )
            )
            data = data.encode("ascii")
            
            
            # Construct the HTTP request that will be sent to the Slack API.
            request = urllib.request.Request(
                SLACK_URL, 
                data=data, 
                method="POST"
            )
            # Add a header mentioning that the text is URL-encoded.
            request.add_header(
                "Content-Type", 
                "application/x-www-form-urlencoded"
            )
            
    # Fire off the request!
    urllib.request.urlopen(request).read()
    
    # Everything went fine.
    return "200 OK"


date = "2017-07-07"
m = MatchInfoPortfolio("day",date)
matchInfoList = m.getMatchInfo()
            
matchOne= matchInfoList[4]
sI = matchOne.secondInningsObject()
sI.addOverObjects()'''
