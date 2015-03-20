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
ap.add_argument('-countries',nargs='+')
ap.add_argument('-st_period',nargs=1)
ap.add_argument('-end_period',nargs=1)
ap.add_argument('-categories',nargs='+')
opts = ap.parse_args()
categories_list=""
countries_list=""
categories=[]
countries=[]
i=0
for country in opts.countries:
                countries_list += country
                countries.append(country)
		i=i+1
                if(i<len(opts.countries)):
                        countries_list += "+"
i=0

if(opts.categories[0] == "NATURAL" ):
        categories_list = "FOOD+IGD_NNRG+NRG+SERV"
        categories.append("FOOD")
	categories.append("IGD_NNRG")
	categories.append("NRG")
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
elif(opts.categories[0] == "ALL" ):
	categories.append("CP00")
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
	categories.append("FOOD")
        categories.append("IGD_NNRG")
        categories.append("NRG")
        categories.append("SERV")
	categories.append("FOOD_P")
	categories.append("FOOD_NP")
	categories.append("IGD_NNRG_SD")
	categories.append("IGD_NNRG_ND")
	categories.append("IGD_NNRG_D")
	categories.append("ELC_GAS")
	categories.append("FUEL")
	categories.append("SERV_COM")
	categories.append("SERV_HOUS")
	categories.append("SERV_TRA")
	categories.append("SERV_REC")
	categories.append("SERV_MSC")
	categories.append("AP")
	categories_list = "CP00+CP01+CP02+CP03+CP04+CP05+CP06+CP07+CP08+CP09+CP10+CP11+CP12+FOOD+IGD_NNRG+NRG+SERV+FOOD_P+FOOD_NP+IGD_NNRG_SD+IGD_NNRG_ND+IGD_NNRG_D+ELC_GAS+FUEL+SERV_COM+SERV_HOUS+SERV_MSC+SERV_REC+SERV_TRA+AP"
        i=29

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

parsed_json = xmltodict.parse(first)
if (1): #TODO used to be i>1
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
                				#value=(float(weights[weight_index])*diff_value)/1000
						value=diff_value
                			#f.write("[ "+str(epoch*1000)+" , "+str(value)+"]")
					#f.write(str(epoch)+" , ")
					#data_list.append('[ '+str(epoch*1000)+' , '+str(value)+']')
					if(a!=0 or value !=0):
						data_list[str(epoch*1000)] = str(value)
        		a=a+1
		all_data[country+"_"+key] =data_list
	for cat in categories:
		f = open('data/test/diffreal/inputData_comparisons_'+cat+'.json','w')
		f.write('[')
		file_name='data/diffreal/inputData_comparisons_'+cat+'.json'
		counter =0
		previousOK=False
		for country in countries:
			if (os.path.isfile(file_name)):
                        	json_data=open(file_name)
                        	loaded_data = json.load(json_data)
                        	json_data.close()
				found = False
				for loadedItem in loaded_data:
					spl = loadedItem["key"].split('#')
					if(country==spl[0]):
						values=loadedItem["values"]
						found = True
				if (not found):
                        		values= []
				#values = loaded_data[counter]["values"]
                	else:
                        	values= []
			if(all_data[country+"_"+cat] or values):
				if (counter>0 and prevOK):
                                        f.write(" , ")
				prevOK=True
				f.write('{\n "key" : '+'"'+country+'#'+parser.get('countries', country) +'",\n')
				f.write('"key_en" : '+'"'+country+'#'+parser.get('countries_en', country) +'",\n')
                		f.write('"values" : ')
                		dat = all_data[country+"_"+cat]
				base_data = []
				for timestamp,value in dat.items():
		    			#resulting_value= float(value) - float(all_data[opts.countries[1]+"_"+cat][timestamp])
                    			val = [int(timestamp),float(value) ]
		    			base_data.append(val)                           
				#for data in reversed(base_data):
				ordered_data = list(reversed(base_data))
                		starting_index = 0
                		if(ordered_data):
                        		starting_index = index_containing_substring(values,int(ordered_data[0][0]))
                		resulting_data=values[:starting_index]
                		resulting_data.extend(ordered_data)
                		f.write(str(resulting_data))
                    		#f.write(data)
				f.write('}\n')
                    	counter=counter+1
		f.write(']')
		f.close() 
#print "DONE, Data downloaded!\n"
