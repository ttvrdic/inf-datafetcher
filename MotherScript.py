#!/usr/bin/python
# coding: utf-8

# In[22]:

import requests
import argparse
import xmltodict, json
import time
from subprocess import call
import os.path
import sys
import codecs
from ConfigParser import SafeConfigParser

# PARSER BLOCK START

parser = SafeConfigParser()
parser.read('ParserConfiguration.cfg')

start = time.time()

ap = argparse.ArgumentParser()
ap.add_argument('-countries',nargs='+')
ap.add_argument('-st_period',nargs=1)
ap.add_argument('-end_period',nargs=1)
ap.add_argument('-categories',nargs='+')
opts = ap.parse_args()
categories_list=""
#if(opts.categories[0] == "NATURAL" ):
#        categories_list = "FOOD+IGD_NNRG+NRG+SERV"
#	i=4
#elif(opts.categories[0] == "CP" ):
#        categories_list = "CP01+CP02+CP03+CP04+CP05+CP06+CP07+CP08+CP09+CP10+CP11+CP12"
#	i=12
#else:
i=0


# Detail Categories array
# used to call up single categories script, which creates unweighted inflation data for each category
# these files are called in the "inflationsrate" in the GUI
detail_categories=[]

for category in opts.categories:
	if(category == "NATURAL" ):
		detail_categories.extend(["NATURAL"]) # Extend with details, for single cat script
	elif(category == "CP" ):
		detail_categories.extend(["CP"])
	elif(category == "AP" ):
		detail_categories.extend(["FOOD_P","FOOD_NP","IGD_NNRG_D","IGD_NNRG_SD","IGD_NNRG_ND","ELC_GAS","FUEL","SERV_COM","SERV_HOUS","SERV_MSC","SERV_REC","SERV_TRA","AP"])
	elif(category == "ALL" ):
                detail_categories.extend(["NATURAL","CP","AP_ALL"])# ONLY THESE TWO RELEVANT FOR CONTRIBUTIONS
	else:
		detail_categories.append(category)
	categories_list += '"'+category+'"'
	i=i+1
	if(i<len(opts.categories)):
	 	categories_list += ","
i=0
countries_list_de=""
countries_list_en=""

# SINGLE CATEGORIES UNWEIGHTED INFLATION START

percStep = float(100.00/len(opts.countries))
percStep = float(percStep/len(opts.categories))
totalPerc=0
k=1
print "Download Started!"
print "Setting up Basic Inflation Data"
step_calculated=0
step_number=1;
totalSteps=100/percStep
step_elapsed=0
for country in opts.countries:
        for detail_category in opts.categories:
		call(["python","GetSingleCategories.py","-country",country,"-categories",detail_category,"-st_period",opts.st_period[0],"-end_period",opts.end_period[0]])
                totalPerc += percStep
                end = time.time()
                elapsed = end - start
		if step_calculated == 0 :
                	step_elapsed=elapsed
			step_calculated=1
		completed = totalSteps-step_number
                elapsed_min=0
                if (elapsed>60):
                        elapsed_min=elapsed/60
                elapsed=elapsed%60
		elapsed_hrs=0
		if (elapsed_min>60):
			elapsed_hrs=elapsed_min/60
		elapsed_min=elapsed_min%60
		time_left=completed*step_elapsed
		time_left_min=0
		if (time_left>60):
			time_left_min = time_left/60
		time_left = time_left%60
		time_left_hrs=0
                if (time_left_min>60):
                        time_left_hrs = time_left_min/60
                time_left_min = time_left_min%60
                sys.stdout.write("\rTime Elapsed: "+str(int(elapsed_hrs))+" hour(s) "+str(int(elapsed_min))+" min %.2f sec " %elapsed +"Processing data for "+country+", total: %.2f " % totalPerc +"% complete."+" Time left "+str(int(time_left_hrs))+" hour(s) "+str(int(time_left_min))+" min %.2f sec" % time_left)
                sys.stdout.flush()
		step_number=step_number+1
        j=0

# CONTRIBUTIONS START
# TODO remove the sys exit to allow normal execution of the program

#TODO decide if you want to delete all files or not
# probably it makes sense to leave them all
# if decided otherwise, remove comments below

#if not os.path.exists("test/data"):
#	call(["rm","test/data/*"])

percStep = float(100.00/len(opts.countries))
percStep = float(percStep/len(detail_categories))
totalPerc=0
k=1
print "Download Started!"
print "Setting up Weighted Contribution Inflation Data:"
step_calculated=0
step_number=1;
totalSteps=100/percStep
step_elapsed=0
second_start=time.time()
for country in opts.countries:
        countries_list_de += '"'+country+";"+parser.get('countries', country)+'"'
	countries_list_en += '"'+country+";"+parser.get('countries_en', country)+'"'
	i=i+1
	for category in detail_categories:
		call(["python","GetContributions.py","-country",country,"-categories",category,"-st_period",opts.st_period[0],"-end_period",opts.end_period[0]])
		totalPerc += percStep	
		end = time.time()
		elapsed = end - start
		if step_calculated == 0 :
                        step_elapsed=end-second_start
                        step_calculated=1
		completed = totalSteps-step_number
		elapsed_min=0
		if (elapsed>60):
			elapsed_min=elapsed/60
		elapsed=elapsed%60
		time_left=completed*step_elapsed
                time_left_min=0
                if (time_left>60):
                        time_left_min = time_left/60
                time_left = time_left%60
		sys.stdout.write("\rTime Elapsed: "+str(int(elapsed_min))+" min %.2f sec " %elapsed +"Processing data for "+country+", total: %.2f " % totalPerc +"% complete."+" Time left "+str(int(time_left_min))+" min %.2f sec" % time_left)
		sys.stdout.flush()
		step_number=step_number+1
        if(i<len(opts.countries)):
                countries_list_de += ","
		countries_list_en += ","
	j=0
f = open('data/config/BarchartConfig_de','w+')
g = open('data/config/BarchartConfig_en','w+')
f.write('{"Categories":[')
f.write(categories_list)
f.write('],\n"Countries":[')
f.write(countries_list_de)
f.write(']}')
f.close() 
g.write('{"Categories":[')
g.write(categories_list)
g.write('],\n"Countries":[')
g.write(countries_list_en)
g.write(']}')
g.close()

print "Inflation data has been set up."
print "Done!"

#DIFFERENTIAL DATA SETUP START
#print "TEST PHASE - skipping differentials.."
#import sys
#sys.exit(0)

print "Setting up differential data:"

totalPerc=0.0
percStep = float(100.00/(len(opts.countries)*(len(opts.countries)-1)))
step_calculated=0
step_number=1;
totalSteps=100/percStep
step_elapsed=0
third_start=time.time()
for country in opts.countries:
	for comp_country in opts.countries:
		if(comp_country !=country):
			call(["python","GetDifferentials.py","-countries",country,comp_country,"-categories","NATURAL","-st_period",opts.st_period[0],"-end_period",opts.end_period[0]])
			totalPerc += percStep
			end = time.time()
                	elapsed = end - start	
			if step_calculated == 0 :
                        	step_elapsed=end-third_start
                        	step_calculated=1
			completed = totalSteps-step_number
			elapsed_min=0
                	if (elapsed>60):
                        	elapsed_min=elapsed/60
                	elapsed=elapsed%60
			time_left=completed*step_elapsed
                	time_left_min=0
                	if (time_left>60):
                        	time_left_min = time_left/60
                	time_left = time_left%60
			sys.stdout.write("\rTime Elapsed: "+str(int(elapsed_min))+" m %.2f s " % elapsed + "Processing "+country+" vs "+comp_country+", total: %.2f " % totalPerc +"% complete. Time left"+str(int(time_left_min))+" min %.2f sec" % time_left )
                	sys.stdout.flush()
			step_number=step_number+1

print "DONE, Data downloaded!\n"
end = time.time()
elapsed = end - start
elapsed_min=0
if (elapsed>60):
	elapsed_min=elapsed/60
elapsed=elapsed%60
print "Total Time Elapsed: "+str(int(elapsed_min))+" min %.2f sec " % elapsed 
