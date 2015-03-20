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

parser = SafeConfigParser()
parser.read('ParserConfiguration.cfg')

start = time.time()

ap = argparse.ArgumentParser()
ap.add_argument('-countries',nargs='+')
ap.add_argument('-st_period',nargs=1)
ap.add_argument('-end_period',nargs=1)
ap.add_argument('-categories',nargs=1)
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
#for category in opts.categories:
#	categories_list += category
#	i=i+1
#	if(i<len(opts.categories)):
#	 	categories_list += ","
#i=0

for category in opts.categories:
    	categories_list += category
	i=i+1
	if(i<len(opts.categories)):
		categories_list += ","

#TODO decide if you want to delete all files or not
# probably it makes sense to leave them all
# if decided otherwise, remove comments below

#if not os.path.exists("test/data"):
#	call(["rm","test/data/*"])

percStep = float(100.00/len(opts.countries))
percStep = float(percStep/len(opts.categories))
totalPerc=0
k=1
print "Download Started!"
print "Setting up differential data:"
totalPerc=0.0
percStep = float(100.00/(len(opts.countries)*(len(opts.countries)-1)))
step_calculated=0
step_number=1;
totalSteps=100/percStep
step_elapsed=0
for country in opts.countries:
	for comp_country in opts.countries:
		if(comp_country !=country):
			call(["python","GetEurostatDataDiffInflation.py","-countries",country,comp_country,"-categories",categories_list,"-st_period",opts.st_period[0],"-end_period",opts.end_period[0]]) #TODO Multiple categories
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
			sys.stdout.write("\rTime Elapsed: "+str(int(elapsed_hrs))+" h "+str(int(elapsed_min))+" m %.2f s " % elapsed + "Processing "+country+" vs "+comp_country+", total: %.2f " % totalPerc +"% complete."+" Time left "+str(int(time_left_hrs))+" h "+str(int(time_left_min))+" m %.2f s" % time_left)
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
