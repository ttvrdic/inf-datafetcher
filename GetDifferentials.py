#!/usr/bin/python
# coding: utf-8

# In[22]:

# This script calculates data for differential visualisation

import requests
import argparse
import xmltodict, json
import time
from collections import OrderedDict
from ConfigParser import SafeConfigParser
import os.path

# return index of the position where timestamp was found
def index_containing_substring(the_list, timestamp):
        for i, s in enumerate(the_list):
                if timestamp == s[0]:
                        return i
        return 0

parser = SafeConfigParser()
parser.read('ParserConfiguration.cfg')


# parse all the arguments
ap = argparse.ArgumentParser()
ap.add_argument('-countries',nargs=2)
ap.add_argument('-st_period',nargs=1)
ap.add_argument('-end_period',nargs=1)
ap.add_argument('-categories',nargs='+')
opts = ap.parse_args()
categories_list=""
countries_list=""
categories=[]
i=0
for country in opts.countries:
                countries_list += country
                i=i+1
                if(i<len(opts.countries)):
                        countries_list += "+"
i=0

# Translate aggregated categories to individual categories
# only NATURAL NEEDED - we are differntiating only on 4 categories. others are there just in case. 
if(opts.categories[0] == "NATURAL" ):
        categories_list = "FOOD+IGD_NNRG+NRG+SERV"
        categories.append("NRG")
	categories.append("FOOD")
	categories.append("IGD_NNRG")
	categories.append("SERV")
	i=4
else:
	# we are not performin analysis on aggregated categories - this script cannot be used
        print "Differentiation data will be skipped"
        import sys
        sys.exit(0)
        # Single category download - not in the scope of this script


# form the request string as url, which we will pass to Eurostat´s Web service
# use boilerplate, and add arguments which have been passed to the script
request_string = "http://ec.europa.eu/eurostat/SDMX/diss-web/rest/data/prc_hicp_midx/.."+categories_list+"."+countries_list+"./?startperiod="+opts.st_period[0]+"&endPeriod="+opts.end_period[0]
r = requests.get(request_string)
first = r.text


#HERE BE WEIGHTS
# we need to invoke a different service by Eurostat, passing arguments similarly like for inflation data
weights_request_string = "http://ec.europa.eu/eurostat/SDMX/diss-web/rest/data/prc_hicp_inw/."+categories_list+"."+countries_list+"../?startperiod="+opts.st_period[0]+"&endPeriod="+opts.end_period[0]
req = requests.get(weights_request_string)
digest = req.text
# parse the text, convert to python structures
transform = xmltodict.parse(digest)
weights = {}
for wei in transform['message:GenericData']['message:DataSet']['generic:Series']:
    for single in wei['generic:Obs']:
	    # index is composed of current year-month-category_code
            index = single['generic:ObsDimension']['@value']+"-"+wei['generic:SeriesKey']['generic:Value'][0]['@value']+"-"+wei['generic:SeriesKey']['generic:Value'][1]['@value']
            # the value - what is the weight for this month
	    value = single['generic:ObsValue']['@value']
            if(value == 'NaN' or value == 'nan'):
		# remedy all missing values, otherwise false format exception
                value=0
            weights[index] = value
# as a result, a dictionary of weights for each category for each month is created
#WE HAVE THE WEIGHTS


parsed_json = xmltodict.parse(first)
f = open('data/test/diff/inputData_'+opts.countries[0]+'vs'+opts.countries[1]+'_'+opts.categories[0]+'.json','w')
f.write('[')
if (i>1):
	all_data={}
	for cat in parsed_json['message:GenericData']['message:DataSet']['generic:Series']:
		# key is the name of the category we are consuming 
    		key = cat['generic:SeriesKey']['generic:Value'][1]['@value']
		country = cat['generic:SeriesKey']['generic:Value'][2]['@value']
    		a = 0
		data_list=OrderedDict()
    		for res in cat['generic:Obs']:
        		date_time = res['generic:ObsDimension']['@value']
			year,month = date_time.split("-")
			# we have to reference the weight dictionary, add also country because we have 2 countries here
        		weight_index=year+"-"+key+"-"+country
			pattern = '%Y-%m'
        		epoch = int(time.mktime(time.strptime(date_time, pattern))) # Convert to epoch for visualizations
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
						# Calculation, as described in developers manual, for GetEurostatData.py
						diff_value= ((float(value)/float(value_last_year))*100)-100
                				value=(float(weights[weight_index])*diff_value)/1000
					data_list[str(epoch*1000)] = str(value)
        		a=a+1
			counter =1
		# as a result we will get a dictionary of timestamp-value pairs for both countries.
		all_data[country+"_"+key] =data_list
        z=1
	cat_counter=0
        for cat in categories:
		f.write('{\n "key" : '+'"'+ parser.get('categories', cat) +'",\n')
		f.write('"key_en" : '+'"'+ parser.get('categories_en', cat) +'",\n')
                f.write('"values" : ')
                 # Load the previously stored data
                # transform it in a dictionary, and create a union of sets between previously loaded data
                # and newly downloaded data. This way we dont have to redownload everything everytime
		file_name='data/diff/inputData_'+opts.countries[0]+'vs'+opts.countries[1]+'_'+opts.categories[0]+'.json'
		if (os.path.isfile(file_name)):
                        json_data=open(file_name)
                        loaded_data = json.load(json_data)
                        json_data.close()
                        values = loaded_data[cat_counter]["values"]
		else:
			values=[]
		dat = all_data[opts.countries[0]+"_"+cat]
		diff_data=[]		
		for timestamp,value in dat.items():
		    if(timestamp in all_data[opts.countries[1]+"_"+cat]):
			# This is the whole point right in this line underneath
			# take the value of country number one and subtrract from other one
			# this gives us the differential which we will then display
		    	resulting_value= float(value) - float(all_data[opts.countries[1]+"_"+cat][timestamp])
                    	val = [int(timestamp),float(resulting_value) ]
			diff_data.append(val)
			#diff_data.append('[ '+timestamp+' , '+str(resulting_value)+']')
                counter =1           
		ordered_data = list(reversed(diff_data)) 
                starting_index = 0
                if(ordered_data):
                        starting_index = index_containing_substring(values,int(ordered_data[0][0]))
		resulting_data=values[:starting_index]
                resulting_data.extend(ordered_data)
		# write to file and we´re done
		f.write(str(resulting_data))
                f.write(' }\n')
                if(z!=len(categories)):
                        f.write(",")
                z=z+1
		cat_counter=cat_counter+1	
f.write(']')
f.close() 
