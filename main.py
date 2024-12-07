#
# Client-side python app for recipe app, which is calling
# a set of lambda functions in AWS through API Gateway.
#
# Authors:
#   Grace Yang
#   Dong Joo Kwon

import requests
import jsons
import random
import awsutil
import boto3

import uuid
import pathlib
import logging
import sys
import os
import base64
import time

from configparser import ConfigParser


############################################################
#
# classes
#
class User:

  def __init__(self, row):
    self.userid = row[0]
    self.firstname = row[1]
    self.lastname = row[2]
    self.allergies = row[3]


class Recipe:

  def __init__(self, row):
    self.mealdbid = row[0]
    self.recipename = row[1]
    self.assetname = row[2]
    self.recipeid = row[3]


class Allergy:

  def __init__(self, row):
    self.allergyid = row[0]
    self.allergyname = row[1]
    self.userid = row[2]


###################################################################
#
# web_service_get
#
# When calling servers on a network, calls can randomly fail. 
# The better approach is to repeat at least N times (typically 
# N=3), and then give up after N tries.
#
def web_service_get(url):
  """
  Submits a GET request to a web service at most 3 times, since 
  web services can fail to respond e.g. to heavy user or internet 
  traffic. If the web service responds with status code 200, 400 
  or 500, we consider this a valid response and return the response.
  Otherwise we try again, at most 3 times. After 3 attempts the 
  function returns with the last response.
  
  Parameters
  ----------
  url: url for calling the web service
  
  Returns
  -------
  response received from web service
  """

  try:
    retries = 0
    
    while True:
      response = requests.get(url)
        
      if response.status_code in [200, 400, 480, 481, 482, 500]:
        #
        # we consider this a successful call and response
        #
        break;

      #
      # failed, try again?
      #
      retries = retries + 1
      if retries < 3:
        # try at most 3 times
        time.sleep(retries)
        continue
          
      #
      # if get here, we tried 3 times, we give up:
      #
      break

    return response

  except Exception as e:
    print("**ERROR**")
    logging.error("web_service_get() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return None
    

############################################################
#
# prompt
#
def prompt():
  """
  Prompts the user and returns the command number

  Parameters
  ----------
  None

  Returns
  -------
  Command number entered by user (0, 1, 2, ...)
  """
  try:
    print()
    print(">> Enter a command:")
    print("   0 => end")
    print("   1 => add user")
    print("   2 => get all users")
    print("   3 => add new allergy")
    print("   4 => get recipe")
    print("   5 => get all recipes")
    print("   6 => download recipe txt")
    print("   7 => get recipe cost")

    cmd = input()

    if cmd == "":
      cmd = -1
    elif not cmd.isnumeric():
      cmd = -1
    else:
      cmd = int(cmd)

    return cmd

  except Exception as e:
    print("**ERROR")
    print("**ERROR: invalid input")
    print("**ERROR")
    return -1
  

############################################################
#
# adduser
#
def addUser(baseurl):
  """
  Prompts the user for the first and last name of new user, 
  and adds user to database. 

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """
  
  try:
    print("Enter user's first name>")
    firstname = input()

    print("Enter user's last name>")
    lastname = input()
    
    #
    # call the web service:
    #
    res = None
    url = f"{baseurl}/adduser/{firstname}/{lastname}"
    res = requests.post(url)


    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      print("User has been added successfully.")
    else:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

  except Exception as e:
    logging.error("**ERROR: addUser() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


############################################################
#
# users
#
def users(baseurl):
  """
  Prints out all the users in the database

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  try:
    #
    # call the web service:
    #
    api = '/getallusers'
    url = baseurl + api

    # res = requests.get(url)
    res = web_service_get(url)

    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    else:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    #
    # deserialize and extract users:
    #
    body = res.json()

    index = 0
    for user in body: 
      print(body[index].get("userid"))
      print(" First name: ", body[index].get("firstname"))
      print(" Last name: ", body[index].get("lastname"))
      all_allergies = body[index].get("allergies")

      if len(all_allergies) == 0: 
        print(" Allergies: None")
      
      else: 
        print_allergies = " Allergies: "
        for a in all_allergies: 
          print_allergies = print_allergies + a + ", "

        actual_print_allergies = print_allergies[:-2]
        print(actual_print_allergies)

      index = index + 1
    return

  except Exception as e:
    logging.error("**ERROR: users() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


############################################################
#
# addAllergy
#
def addAllergy(baseurl):
  """
  Prompts the user for the userid of a user and adds allergies to database

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """
  
  try:
    #
    # ask for userid
    #
    print("Enter user id>")
    userid = input()

    #
    # ask for allergies one at a time
    #
    print("Enter allergy (enter 0 if finished) >")
    allergy = input()
    while (allergy != "0"):
    
      #
      # call the web service:
      #
      res = None
      url = f"{baseurl}/addallergy/{userid}/{allergy}"
      res = requests.post(url)

      #
      # let's look at what we got back:
      #
      if res.status_code == 200: #success
        if res.json() == 0:
          print("Userid does not exist.")
          return
        print("Allergy has been added. Enter new allergy (enter 0 if finished) >")
        allergy = input()
      else:
        # failed
        print("Failed with status code:", res.status_code)
        print("url: " + url)
        if res.status_code == 500:
          # we'll have an error message
          body = res.json()
          print("Error message:", body)
        return

  except Exception as e:
    logging.error("**ERROR: addAllergy() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return

############################################################
#
# getRecipe
#
def getRecipe(baseurl):
  """
  queries theMealDB for a recipe from a certain category that does not contain the allergies of the user

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """
  try:
    #
    # ask for userid
    #
    print("Enter a user id> ")
    userid = input()

    #
    # print categories
    #
    categories = ["Beef", "Chicken", "Goat", "Lamb", "Pork", "Seafood", "Pasta", "Dessert", "Side", "Starter", "Vegan", "Vegetarian", "Breakfast", "Miscelleneous"]
    print("Below are the available recipe categories: ")
    print("     > Beef")
    print("     > Chicken")
    print("     > Goat")
    print("     > Lamb")
    print("     > Pork")
    print("     > Seafood")
    print("     > Pasta")
    print("     > Dessert")
    print("     > Side")
    print("     > Starter")
    print("     > Vegan")
    print("     > Vegetarian")
    print("     > Breakfast")
    print("     > Miscellaneous")
    print("")
    print("Enter a category> ")
    category = input()

    if category not in categories:
      print("Input does not match any of the categories. Note that first letter must be capitalized.")
      return

    #
    # call the web service:
    #
    res = None
    url = f"{baseurl}/getrecipe/{userid}/{category}"

    print("Finding a recipe...")
    res = requests.post(url)

    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    else:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      return
    
    #
    # deserialize and extract recipe info
    #
    body = res.json()
    print(body)

    return

  except Exception as e:
    logging.error("**ERROR: getRecipe() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return
  

############################################################
#
# getAllRecipes
#

def getAllRecipes(baseurl):
  """
  Prints out all the recipes in the database

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  try:
    #
    # call the web service:
    #
    api = '/getallrecipes'
    url = baseurl + api

    # res = requests.get(url)
    res = web_service_get(url)

    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    else:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    #
    # deserialize and extract users:
    #
    body = res.json()

    #
    #format recipes
    #
    recipes = []
    for row in body:
      recipe = Recipe(row)
      recipes.append(recipe)

    #
    # recipes table empty
    #
    if len(recipes) == 0:
      print("no recipes...")
      return
    
    #
    # print recipes
    #
    for recipe in recipes:
      print(recipe.recipeid)
      print(" TheMealDB id: ", recipe.mealdbid)
      print(" Name: ", recipe.recipename)
      if len(recipe.assetname) == 0: 
        print(" Asset name: None")
      else:
        print(" Asset name: ", recipe.assetname)
      print(" Id: ", recipe.recipeid)
    return

  except Exception as e:
    logging.error("**ERROR: getAllRecipes() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return
  

  ############################################################
#
# getRecipeCost
#

def getRecipeCost(baseurl):
  """
  Returns cost information about the ingredients of a recipe

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  try:
    #
    # ask for recipeid
    #
    print("Enter a recipe's TheMealDB id>")
    recipeid = input()
    print("Getting estimated cost details...\n")

    #
    # call the web service:
    #
    res = None
    url = f"{baseurl}/getrecipecost/{recipeid}"
    res = requests.get(url)

    # res = requests.get(url)
    res = web_service_get(url)

    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    else:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # error message
        body = res.json()
        print("Error message:", body)
      #
      return
    
    #
    # deserialize and extract recipe cost info
    #
    body = res.json()
    print(body)
    return
  
  except Exception as e:
    logging.error("**ERROR: getAllRecipes() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return
  

  ############################################################
#
# getRecipeCost
#

def downloadTXT(baseurl, bucketname):
  """
  Downloads recipe information to local computer in a .txt file 

  Parameters
  ----------
  baseurl: baseurl for web service
  bucketname: client's s3 bucket

  Returns
  -------
  nothing
  """

  try:
    print("Enter a recipe's TheMealDB id>")
    recipeid = input()
    
    #
    # call the web service:
    #
    res = None
    url = f"{baseurl}/downloadrecipe/{recipeid}"
    res = requests.post(url)

    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    else:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # error message
        body = res.json()
        print("Error message:", body)
      #
      return
    
    #
    # deserialize and extract recipe cost info
    #
    body = res.json()
    if body == 0:
      print("Recipeid doesn't exist.")
      return
    
    #extract the local_filename and bucketkey_results_file variables
    filename = body.get("local_filename")
    bucketkey_results_file = body.get("bucketkey_results_file")

    print(f"Downloading file '{filename}'")

    s3 = boto3.client('s3')

    # download the file from S3
    s3.download_file(bucketname, bucketkey_results_file, filename)

    print(f"File downloaded and saved as '{filename}'")

    return
  except Exception as e:
    logging.error("**ERROR: downloadPDF() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


############################################################
# main
#
try:
  print('** Welcome to RecipeApp **')
  print()

  # eliminate traceback so we just get error message:
  sys.tracebacklimit = 0

  config_file = 'recipeapp-client-config.ini'
  other_config_file = 'recipeapp-config.ini'

  print("Config file to use for this session?")
  print("Press ENTER to use default, or")
  print("enter config file name>")
  s = input()

  if s == "":  # use default
    pass  # already set
  else:
    config_file = s

  #
  # does config file exist?
  #
  if not pathlib.Path(config_file).is_file():
    print("**ERROR: config file '", config_file, "' does not exist, exiting")
    sys.exit(0)

  #
  # setup base URL to web service:
  #
  configur = ConfigParser()
  configur.read(config_file)
  baseurl = configur.get('client', 'webservice')
  
  other_configur = ConfigParser()
  other_configur.read(other_config_file)
  bucketname = other_configur.get('s3', 'bucket_name')

  #
  # make sure baseurl does not end with /, if so remove
  #
  if len(baseurl) < 16:
    print("**ERROR: baseurl '", baseurl, "' is not nearly long enough...")
    sys.exit(0)

  if baseurl == "https://YOUR_GATEWAY_API.amazonaws.com":
    print("**ERROR: update config file with your gateway endpoint")
    sys.exit(0)

  if baseurl.startswith("http:"):
    print("**ERROR: your URL starts with 'http', it should start with 'https'")
    sys.exit(0)

  lastchar = baseurl[len(baseurl) - 1]
  if lastchar == "/":
    baseurl = baseurl[:-1]

  #
  # main processing loop:
  #
  cmd = prompt()

  while cmd != 0:
    #
    if cmd == 1:
      addUser(baseurl) # add new user
    elif cmd == 2:
      users(baseurl) # return all users
    elif cmd == 3:
      addAllergy(baseurl) # add new allergy 
    elif cmd == 4:
      getRecipe(baseurl) # return a random recipe without allergies
    elif cmd == 5:
      getAllRecipes(baseurl) # return all recipes
    elif cmd == 6:
      downloadTXT(baseurl, bucketname)  # downloads a pdf of a recipe
    elif cmd == 7:
      getRecipeCost(baseurl) # gets cost information about a recipe
    else:
      print("** Unknown command, try again...")
    #
    cmd = prompt()

  #
  # done
  #
  print()
  print('** done **')
  sys.exit(0)

except Exception as e:
  logging.error("**ERROR: main() failed:")
  logging.error(e)
  sys.exit(0)
