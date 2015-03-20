#!/usr/bin/python
# coding: utf-8

# In[22]:

import requests
import argparse
import xmltodict, json
import time
from ConfigParser import SafeConfigParser
import os.path

def index_containing_substring(the_list, timestamp):
	for i, s in enumerate(the_list):
        	if timestamp == s[0]:
                	return i
        return 0

ap = argparse.ArgumentParser()
ap.add_argument('-country',nargs=1)
ap.add_argument('-st_period',nargs=1)
ap.add_argument('-end_period',nargs=1)
ap.add_argument('-categories',nargs='+')
opts = ap.parse_args()
categories_list=""
i=0
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

request_string = "http://ec.europa.eu/eurostat/SDMX/diss-web/rest/data/prc_hicp_midx/.."+categories_list+"."+opts.country[0]+"./?startperiod="+opts.st_period[0]+"&endPeriod="+opts.end_period[0]
#request_string = "http://ec.europa.eu/eurostat/SDMX/diss-web/rest/data/prc_hicp_midx/..CP00+IGD_NNRG+FOOD+SERV+NRG.BG./?startperiod=1990-02&endPeriod=2014-08"
r = requests.get(request_string)
first = r.text
#HERE BE WEIGHTS
weights_request_string = "http://ec.europa.eu/eurostat/SDMX/diss-web/rest/data/prc_hicp_inw/."+categories_list+"."+opts.country[0]+"../?startperiod="+opts.st_period[0]+"&endPeriod="+opts.end_period[0]
req = requests.get(weights_request_string)
digest = req.text
transform = xmltodict.parse(digest)
weights = {}
if (i>1):
	for wei in transform['message:GenericData']['message:DataSet']['generic:Series']:
    		for single in wei['generic:Obs']:
        		index = single['generic:ObsDimension']['@value']+"-"+wei['generic:SeriesKey']['generic:Value'][0]['@value']
        		value = single['generic:ObsValue']['@value']
        		if(value == 'NaN' or value == 'nan'):
                		value=0
        		weights[index] = value
else:
	 for single in transform['message:GenericData']['message:DataSet']['generic:Series']['generic:Obs']:
                        index = single['generic:ObsDimension']['@value']+"-"+ transform['message:GenericData']['message:DataSet']['generic:Series']['generic:SeriesKey']['generic:Value'][0]['@value']
                        value = single['generic:ObsValue']['@value']
                        if(value == 'NaN' or value == 'nan'):
                                value=0
                        weights[index] = value
#WE HAVE THE WEIGHTS
json_parsed = xmltodict.parse(first)

parser = SafeConfigParser()
parser.read('ParserConfiguration.cfg')
#f = open('data/test/inputData_'+opts.country[0]+'_'+opts.categories[0]+'.json','w')
#f.write('[')
z = 1
if (i>1):
	for cat in json_parsed['message:GenericData']['message:DataSet']['generic:Series']: 
		key = cat['generic:SeriesKey']['generic:Value'][1]['@value']
		f = open('data/test/inputData_'+opts.country[0]+'_'+key+'.json','w')
		f.write('[{\n "key" : '+'"'+ parser.get('categories', key)+'",\n')
		f.write('"key_en" : '+'"'+ parser.get('categories_en', key)+'",\n')
    		f.write('"values" : ')
    		a = 0
		data_list=[]
    		for res in cat['generic:Obs']:
        		date_time = res['generic:ObsDimension']['@value']
			year,month = date_time.split("-")
			weight_index=year+"-"+key
        		pattern = '%Y-%m'
        		epoch = int(time.mktime(time.strptime(date_time, pattern)))
			value = res['generic:ObsValue']['@value']
        		if (value == 'NaN' or value == 'nan'):
            			value =0
        		border_value=len(cat['generic:Obs'])-12
        		if (a<border_value):
            			ret_index = a+12
            			value_last_year = cat['generic:Obs'][ret_index]['generic:ObsValue']['@value']
            			if (value_last_year == 'NaN' or value_last_year == 'nan'):
                			value_last_year =0
            			if(value_last_year!=0):
                			if (value!=0):
						diff_value= ((float(value)/float(value_last_year))*100)-100
                				value=diff_value
						#value=(float(weights[weight_index])*diff_value)/1000
                			#f.write("[ "+str(epoch*1000)+" , "+str(value)+"]")
					#f.write(str(epoch)+" , ")
					if(a!=0 or value !=0):
						val = [epoch*1000, value]
						data_list.append(val)
						#data_list.append('[ '+str(epoch*1000)+' , '+str(value)+']')
        		a=a+1
			counter =1
		file_name='data/inputData_'+opts.country[0]+'_'+key+'.json'
		ordered_data = list(reversed(data_list))
		starting_index= 0
		# CHECK IF DATA EXISTS LOCALLY
		# AND ON EUROSTAT; SOME CATEGORIES MISSING FOR SOME COUNTRIES
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
		weight_index=year+"-"+key
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
					#value=(float(weights[weight_index])*diff_value)/1000
                                #f.write("[ "+str(epoch*1000)+" , "+str(value)+"]")
                                #f.write(str(epoch)+" , ")
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
#print "DONE, Data downloaded!\n"
