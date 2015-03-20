#!/usr/bin/python
# coding: utf-8

# In[22]:

# This script generates data for single categories
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
elif(opts.categories[0] == "ALL" ):
	categories_list = "CP00+CP01+CP02+CP03+CP04+CP05+CP06+CP07+CP08+CP09+CP10+CP11+CP12+FOOD+IGD_NNRG+NRG+SERV+FOOD_P+FOOD_NP+IGD_NNRG_SD+IGD_NNRG_ND+IGD_NNRG_D+ELC_GAS+FUEL+SERV_COM+SERV_HOUS+SERV_MSC+SERV_REC+SERV_TRA+AP"
	i=29
else:
	for category in opts.categories:
		categories_list += category
		i=i+1
		if(i<len(opts.categories)):
		 	categories_list += "+"

# form the request string as url, which we will pass to Eurostat´s Web service
# use boilerplate, and add arguments which have been passed to the script
request_string = "http://ec.europa.eu/eurostat/SDMX/diss-web/rest/data/prc_hicp_midx/.."+categories_list+"."+opts.country[0]+"./?startperiod="+opts.st_period[0]+"&endPeriod="+opts.end_period[0]
r = requests.get(request_string)
first = r.text
json_parsed = xmltodict.parse(first)
# parse the text, convert to python structures
parser = SafeConfigParser()
parser.read('ParserConfiguration.cfg')
z = 1
if (i>1):
	for cat in json_parsed['message:GenericData']['message:DataSet']['generic:Series']: 
		# key is the name of the category we are consuming
		key = cat['generic:SeriesKey']['generic:Value'][1]['@value']
		# no fancy operations neccessary here, so write the JSON boilerplate immediately
		f = open('data/test/inputData_'+opts.country[0]+'_'+key+'.json','w')
		f.write('[{\n "key" : '+'"'+ parser.get('categories', key)+'",\n')
		f.write('"key_en" : '+'"'+ parser.get('categories_en', key)+'",\n')
    		f.write('"values" : ')
    		a = 0
		data_list=[]
    		for res in cat['generic:Obs']:
        		date_time = res['generic:ObsDimension']['@value']
			year,month = date_time.split("-")
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
						# notice there are no weights, so we can set the value to diffvalue immediately
						diff_value= ((float(value)/float(value_last_year))*100)-100
                				value=diff_value
					if(a!=0 or value !=0):
						val = [epoch*1000, value]
						data_list.append(val)
        		a=a+1
			counter =1
		# Load the previously stored data
                # transform it in a dictionary, and create a union of sets between previously loaded data
                # and newly downloaded data. This way we dont have to redownload everything everytime
		file_name='data/inputData_'+opts.country[0]+'_'+key+'.json'
		ordered_data = list(reversed(data_list))
		starting_index= 0
		if (os.path.isfile(file_name) and ordered_data):
			json_data=open(file_name)
        		loaded_data = json.load(json_data)
        		json_data.close()
        		values = loaded_data[0]["values"]
			starting_index = index_containing_substring(values,int(ordered_data[0][0]))	
        		resulting_data=values[:starting_index]
        	else:
			resulting_data = []
		resulting_data.extend(ordered_data)
        	f.write(str(resulting_data))
		f.write('\n}\n]')
		f.close()
else:
	f = open('data/test/inputData_'+opts.country[0]+'_'+opts.categories[0]+'.json','w')
	f.write('[')
	key = json_parsed['message:GenericData']['message:DataSet']['generic:Series']['generic:SeriesKey']['generic:Value'][0]['@value']
    	f.write('[{\n "key" : '+'"'+ parser.get('categories', key)+'",\n')
        f.write('"key_en" : '+'"'+ parser.get('categories_en', key)+'",\n')
	f.write('"values" :')
	a=1
	data_list=[]
    	for res in json_parsed['message:GenericData']['message:DataSet']['generic:Series']['generic:Obs']:
        	date_time = res['generic:ObsDimension']['@value']
        	year,month = date_time.split("-")
		pattern = '%Y-%m'
        	epoch = int(time.mktime(time.strptime(date_time, pattern)))
        	value = res['generic:ObsValue']['@value']
		data_length=len(json_parsed['message:GenericData']['message:DataSet']['generic:Series']['generic:Obs'])
        	if (value == 'NaN' or value == 'nan'):
            		value =0
		border_value=data_length-11
        	if (a<border_value):
			ret_index=a+11
			value_last_year= json_parsed['message:GenericData']['message:DataSet']['generic:Series']['generic:Obs'][ret_index]['generic:ObsValue']['@value']
			if (value_last_year == 'NaN' or value_last_year == 'nan'):
                        	value_last_year =0
			if(value_last_year!=0):
				if (value!=0):
                                        diff_value= ((float(value)/float(value_last_year))*100)-100
					value = diff_value
				val = [epoch*1000, value]
                                data_list.append(val)
		a=a+1
		counter =1
                #reverse the array - since they are downloaded in newest-oldest from eurostat
	
	file_name='data/inputData_'+opts.country[0]+'_'+opts.categories[0]+'.json'
        if (os.path.isfile(file_name)):	
		json_data=open(file_name)
		loaded_data = json.load(json_data)
        	json_data.close()
        	values = loaded_data[0]["values"]
	else:
                values= []
	ordered_data = list(reversed(data_list))
	starting_index = index_containing_substring(values,int(ordered_data[0][0]))
	resulting_data=values[:starting_index]	
	resulting_data.extend(ordered_data)
	f.write(str(resulting_data))
	f.write('\n}\n]')
	f.close() 
