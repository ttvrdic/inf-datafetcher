#!/usr/bin/python
# coding: utf-8

# In[22]:

import requests
import argparse
import xmltodict, json
import time
from collections import OrderedDict
from ConfigParser import SafeConfigParser
import os.path

def index_containing_substring(the_list, timestamp):
        for i, s in enumerate(the_list):
                if timestamp == s[0]:
                        return i
        return 0

parser = SafeConfigParser()
parser.read('ParserConfiguration.cfg')

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

if(opts.categories[0] == "NATURAL" ):
        categories_list = "FOOD+IGD_NNRG+NRG+SERV"
        categories.append("NRG")
	categories.append("FOOD")
	categories.append("IGD_NNRG")
	categories.append("SERV")
	i=4
elif(opts.categories[0] == "CP" ):
        categories_list = "CP01+CP02+CP03+CP04+CP05+CP06+CP07+CP08+CP09+CP10+CP11+CP12"
        categories.append("CP01")
	categories.append("CP02")
	categories.append("CP03")
	categories.append("CP04")
	categories.append("CP05")
	categories.append("CP06")
	categories.append("CP07")
	categories.append("CP08")	
	categories.append("CP09")
	categories.append("CP10")
	categories.append("CP11")
	categories.append("CP12")
	i=12
else:
        for category in opts.categories:
                categories_list += category
                categories.append(category)
		i=i+1
                if(i<len(opts.categories)):
                        categories_list += "+"


request_string = "http://ec.europa.eu/eurostat/SDMX/diss-web/rest/data/prc_hicp_midx/.."+categories_list+"."+countries_list+"./?startperiod="+opts.st_period[0]+"&endPeriod="+opts.end_period[0]
#request_string = "http://ec.europa.eu/eurostat/SDMX/diss-web/rest/data/prc_hicp_midx/..CP00+IGD_NNRG+FOOD+SERV+NRG.BG./?startperiod=1990-02&endPeriod=2014-08"
r = requests.get(request_string)
first = r.text


#HERE BE WEIGHTS
weights_request_string = "http://ec.europa.eu/eurostat/SDMX/diss-web/rest/data/prc_hicp_inw/."+categories_list+"."+countries_list+"../?startperiod="+opts.st_period[0]+"&endPeriod="+opts.end_period[0]
req = requests.get(weights_request_string)
digest = req.text
transform = xmltodict.parse(digest)
weights = {}
for wei in transform['message:GenericData']['message:DataSet']['generic:Series']:
    for single in wei['generic:Obs']:
            index = single['generic:ObsDimension']['@value']+"-"+wei['generic:SeriesKey']['generic:Value'][0]['@value']+"-"+wei['generic:SeriesKey']['generic:Value'][1]['@value']
            value = single['generic:ObsValue']['@value']
            if(value == 'NaN' or value == 'nan'):
                value=0
            weights[index] = value
#WE HAVE THE WEIGHTS


parsed_json = xmltodict.parse(first)
f = open('data/test/diff/inputData_'+opts.countries[0]+'vs'+opts.countries[1]+'_'+opts.categories[0]+'.json','w')
f.write('[')
if (i>1):
	all_data={}
	for cat in parsed_json['message:GenericData']['message:DataSet']['generic:Series']: 
    		key = cat['generic:SeriesKey']['generic:Value'][1]['@value']
		country = cat['generic:SeriesKey']['generic:Value'][2]['@value']
    		a = 0
		data_list=OrderedDict()
    		for res in cat['generic:Obs']:
        		date_time = res['generic:ObsDimension']['@value']
			year,month = date_time.split("-")
        		weight_index=year+"-"+key+"-"+country
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
                				value=(float(weights[weight_index])*diff_value)/1000
                			#f.write("[ "+str(epoch*1000)+" , "+str(value)+"]")
					#f.write(str(epoch)+" , ")
					#data_list.append('[ '+str(epoch*1000)+' , '+str(value)+']')
					data_list[str(epoch*1000)] = str(value)
        		a=a+1
			counter =1
		all_data[country+"_"+key] =data_list
        z=1
	cat_counter=0
        for cat in categories:
		f.write('{\n "key" : '+'"'+ parser.get('categories', cat) +'",\n')
		f.write('"key_en" : '+'"'+ parser.get('categories_en', cat) +'",\n')
                f.write('"values" : ')
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
		f.write(str(resulting_data))
                f.write(' }\n')
                if(z!=len(categories)):
                        f.write(",")
                z=z+1
		cat_counter=cat_counter+1	
f.write(']')
f.close() 
#print "DONE, Data downloaded!\n"
