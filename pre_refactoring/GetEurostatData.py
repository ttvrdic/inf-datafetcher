#!/usr/bin/python
# coding: utf-8

# In[22]:

# Import all the neccessary libraries

import requests
import argparse
import xmltodict, json
import time
from ConfigParser import SafeConfigParser
import os.path

# return index of the position where timestamp was found
def index_containing_substring(the_list, timestamp):
        for i, s in enumerate(the_list):
                if timestamp == s[0]:
                        return i
        return 0

# parse all the arguments
ap = argparse.ArgumentParser()
ap.add_argument('-country',nargs=1)
ap.add_argument('-st_period',nargs=1)
ap.add_argument('-end_period',nargs=1)
ap.add_argument('-categories',nargs='+')
opts = ap.parse_args()
categories_list=""
i=0

# Translate aggregated categories to individual categories
if(opts.categories[0] == "NATURAL" ):
        categories_list = "FOOD+IGD_NNRG+NRG+SERV"
	i=4
elif(opts.categories[0] == "CP" ):
        categories_list = "CP01+CP02+CP03+CP04+CP05+CP06+CP07+CP08+CP09+CP10+CP11+CP12"
	i=12
elif(opts.categories[0] == "AP_ALL" ):
        categories_list = "FOOD_P+FOOD_NP+IGD_NNRG_D+IGD_NNRG_SD+IGD_NNRG_ND+ELC_GAS+FUEL+SERV_COM+SERV_HOUS+SERV_MSC+SERV_REC+SERV_TRA"
        i=12
else:
	# we are not performin analysis on aggregated categories - this script cannot be used
	print "Contribution data will be skipped"
	import sys
	sys.exit(0)
	# Single category download - not in the scope of this script


# form the request string as url, which we will pass to Eurostat´s Web service
# use boilerplate, and add arguments which have been passed to the script
request_string = "http://ec.europa.eu/eurostat/SDMX/diss-web/rest/data/prc_hicp_midx/.."+categories_list+"."+opts.country[0]+"./?startperiod="+opts.st_period[0]+"&endPeriod="+opts.end_period[0]
r = requests.get(request_string)
first = r.text

#HERE BE WEIGHTS
# we need to invoke a different service by Eurostat, passing arguments similarly like for inflation data
weights_request_string = "http://ec.europa.eu/eurostat/SDMX/diss-web/rest/data/prc_hicp_inw/."+categories_list+"."+opts.country[0]+"../?startperiod="+opts.st_period[0]+"&endPeriod="+opts.end_period[0]
req = requests.get(weights_request_string)
digest = req.text
# parse the text, convert to python structures
transform = xmltodict.parse(digest)
weights = {}
if (i>1): # we are dealing with more than one category - will alwayss be true really
	for wei in transform['message:GenericData']['message:DataSet']['generic:Series']:
    		for single in wei['generic:Obs']:
			# index is composed of current year-month-category_code
        		index = single['generic:ObsDimension']['@value']+"-"+wei['generic:SeriesKey']['generic:Value'][0]['@value'] 
        		# the value - what is the weight for this month
			value = single['generic:ObsValue']['@value']
        		if(value == 'NaN' or value == 'nan'):
				# remedy all missing values, otherwise false format exception
                		value=0
        		weights[index] = value
# as a result, a dictionary of weights for each category for each month is created
#WE HAVE THE WEIGHTS

parsed_json = xmltodict.parse(first)

# Get configuration data
parser = SafeConfigParser()
parser.read('ParserConfiguration.cfg')
f = open('data/test/inputData_'+opts.country[0]+'_'+opts.categories[0]+'.json','w')
f.write('[')
z = 0
allData={}
if (i>1):
	for cat in parsed_json['message:GenericData']['message:DataSet']['generic:Series']: 
    		# key is the name of the category we are consuming
		key = cat['generic:SeriesKey']['generic:Value'][1]['@value']
    		a = 0
		data_list=[]
    		for res in cat['generic:Obs']:
        		date_time = res['generic:ObsDimension']['@value']
			year,month = date_time.split("-")
			weight_index=year+"-"+key # we have to reference the weight dictionary
        		pattern = '%Y-%m'
        		epoch = int(time.mktime(time.strptime(date_time, pattern))) # convert to epoch, for visualizations
			if(opts.categories[0] == 'AP_ALL'):	
				if(opts.country[0] == 'EE' or opts.country[0] == 'NO' or opts.country[0] == 'EA17' or opts.country[0] == 'EA18'):
					if epoch < 1009843200:
      						break
			value = res['generic:ObsValue']['@value']
			if (value == 'NaN' or value == 'nan'):
            			value =0
        		border_value=len(cat['generic:Obs'])-12
        		if (a<border_value):
				# When values are fetched from Eurostat they are in an inverted order
				# this is why, in order to get value from last year, we have to go 12 months "ahead"
            			ret_index = a+12 
            			value_last_year = cat['generic:Obs'][ret_index]['generic:ObsValue']['@value']
            			if (value_last_year == 'NaN' or value_last_year == 'nan'):
                			value_last_year =0
            			if(value_last_year!=0):
					if (value!=0):
						# Calculation, as described in developers manual
						diff_value= ((float(value)/float(value_last_year))*100)-100
                				value=(float(weights[weight_index])*diff_value)/1000
                			#f.write("[ "+str(epoch*1000)+" , "+str(value)+"]")
					#f.write(str(epoch)+" , ")
					if(a!=0 or value !=0): #TODO revise if problems with some countries
						val = [epoch*1000, value] # timestamp - value pair
                                                data_list.append(val)
						#data_list.append('[ '+str(epoch*1000)+' , '+str(value)+']')
        		a=a+1
			counter =1
		allData[key] = data_list
	# IMPOSE ORDER FOR CATEGORIES PER ANALYSIS
	if(opts.categories[0] == 'AP_ALL'):
		categories=["ELC_GAS","FUEL","FOOD_P","FOOD_NP","IGD_NNRG_D","IGD_NNRG_SD","IGD_NNRG_ND","SERV_COM","SERV_HOUS","SERV_TRA","SERV_REC","SERV_MSC"]
	if(opts.categories[0] == 'CP'):
                categories=["CP01","CP02","CP03","CP04","CP05","CP06","CP07","CP08","CP09","CP10","CP11","CP12"]
	if (opts.categories[0] == 'NATURAL'):
		categories=["NRG","FOOD","IGD_NNRG","SERV"]

	for singleCategory in categories:
		f.write('{\n "key" : '+'"'+ parser.get('categories', singleCategory)+'",\n')
                f.write('"key_en" : '+'"'+ parser.get('categories_en', singleCategory)+'",\n')
                f.write('"values" : ')
		file_name='data/inputData_'+opts.country[0]+'_'+opts.categories[0]+'.json'
 		if (os.path.isfile(file_name)):
			json_data=open(file_name)
               		loaded_data = json.load(json_data)
               		json_data.close()
			retrievedCategory = parser.get('categories', singleCategory)
			for readSeries in loaded_data:
				if(readSeries["key_en"]==parser.get('categories_en', singleCategory)):
               				values = readSeries["values"]
		else:
                	values= []
		# data has to be reversed, because it is downloaded in a youngest-oldest order from Eurostat
        	ordered_data = list(reversed(allData[singleCategory]))
		# find the index from which we cut the values loaded from files
		starting_index = index_containing_substring(values,int(ordered_data[0][0]))
        	resulting_data=values[:starting_index]
        	resulting_data.extend(ordered_data)
		# write union of two sets to a file, and we are done
        	f.write(str(resulting_data))
        	f.write('\n}')
		if(z<(len(parsed_json['message:GenericData']['message:DataSet']['generic:Series'])-1)):
			f.write('\n,')
		z=z+1

