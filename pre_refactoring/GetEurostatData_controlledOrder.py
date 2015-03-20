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
elif(opts.categories[0] == "AP_ALL" ):
        categories_list = "FOOD_P+FOOD_NP+IGD_NNRG_D+IGD_NNRG_SD+IGD_NNRG_ND+ELC_GAS+FUEL+SERV_COM+SERV_HOUS+SERV_MSC+SERV_REC+SERV_TRA"
        i=12
else:
	print "Contribution data will be skipped"
	import sys
	sys.exit(0)
	# Single category download - not in the scope of this script


	#for category in opts.categories:
	#	categories_list += category
#		i=i+1
#		if(i<len(opts.categories)):
#		 	categories_list += "+"

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

parsed_json = xmltodict.parse(first)

parser = SafeConfigParser()
parser.read('ParserConfiguration.cfg')
f = open('data/test/inputData_'+opts.country[0]+'_'+opts.categories[0]+'.json','w')
f.write('[')
z = 0
allData={}
if (i>1):
	for cat in parsed_json['message:GenericData']['message:DataSet']['generic:Series']: 
    		key = cat['generic:SeriesKey']['generic:Value'][0]['@value']
		#f.write('{\n "key" : '+'"'+ parser.get('categories', key)+'",\n')
		#f.write('"key_en" : '+'"'+ parser.get('categories_en', key)+'",\n')
    		#f.write('"values" : ')
    		a = 0
		data_list=[]
    		for res in cat['generic:Obs']:
        		date_time = res['generic:ObsDimension']['@value']
			year,month = date_time.split("-")
			weight_index=year+"-"+key
        		pattern = '%Y-%m'
        		epoch = int(time.mktime(time.strptime(date_time, pattern)))
			if(opts.categories[0] == 'AP_ALL'):	
				if(opts.country[0] == 'EE' or opts.country[0] == 'NO' or opts.country[0] == 'EA17' or opts.country[0] == 'EA18'):
					if epoch < 1009843200:
      						break
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
                				value=(float(weights[weight_index])*diff_value)/1000
                			#f.write("[ "+str(epoch*1000)+" , "+str(value)+"]")
					#f.write(str(epoch)+" , ")
					if(a!=0 or value !=10000000): #TODO what to do in this case?
						val = [epoch*1000, value]
                                                data_list.append(val)
						#data_list.append('[ '+str(epoch*1000)+' , '+str(value)+']')
        		a=a+1
			counter =1
		allData[key] = data_list
			#reverse the array - since they are downloaded in newest-oldest from eurostat
	
    	categories=[]	
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
        	ordered_data = list(reversed(allData[singleCategory]))
		starting_index = index_containing_substring(values,int(ordered_data[0][0]))
        	resulting_data=values[:starting_index]
        	resulting_data.extend(ordered_data)
        	f.write(str(resulting_data))
        	f.write('\n}')
		if(z<(len(parsed_json['message:GenericData']['message:DataSet']['generic:Series'])-1)):
			f.write('\n,')
		z=z+1

# non-contribution aggregates (most likely never executed)
else:
	key = parsed_json['message:GenericData']['message:DataSet']['generic:Series']['generic:SeriesKey']['generic:Value'][0]['@value']
	f.write('{\n "key" : '+'"'+parser.get('categories', key) +'",\n')
	f.write('"key_en" : '+'"'+parser.get('categories_en', key) +'",\n')
    	f.write('"values" : [ ')
	a=1
	data_list=[]
    	for res in parsed_json['message:GenericData']['message:DataSet']['generic:Series']['generic:Obs']:
        	date_time = res['generic:ObsDimension']['@value']
        	year,month = date_time.split("-")
		weight_index=year+"-"+key
		pattern = '%Y-%m'
        	epoch = int(time.mktime(time.strptime(date_time, pattern)))
        	value = res['generic:ObsValue']['@value']
		data_length=len(parsed_json['message:GenericData']['message:DataSet']['generic:Series']['generic:Obs'])
        	if (value == 'NaN' or value == 'nan'):
            		value =0
		border_value=data_length-11
        	if (a<border_value):
			ret_index=a+11
			value_last_year= parsed_json['message:GenericData']['message:DataSet']['generic:Series']['generic:Obs'][ret_index]['generic:ObsValue']['@value']
			if (value_last_year == 'NaN' or value_last_year == 'nan'):
                        	value_last_year =0
			if(value_last_year!=0):
				if (value!=0):
                                        diff_value= ((float(value)/float(value_last_year))*100)-100
					value=(float(weights[weight_index])*diff_value)/1000
                                #f.write("[ "+str(epoch*1000)+" , "+str(value)+"]")
                                #f.write(str(epoch)+" , ")
                                data_list.append('[ '+str(epoch*1000)+' , '+str(value)+']')	
		a=a+1
		counter =1
                #reverse the array - since they are downloaded in newest-oldest from eurostat
	for data in reversed(data_list):
                f.write(data)
                if (counter<len(data_list)):
                        f.write(" , ")
                counter=counter+1
        f.write(']\n }\n')
f.write(']')
f.close() 
#print "DONE, Data downloaded!\n"
