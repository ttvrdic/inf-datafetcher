#!/bin/bash          
python MotherScript.py -countries AT BE BG CZ DK DE EE IE EL ES FR HR IT CY LV LT LU HU MT NL PL PT RO SI SK FI SE UK IS NO CH EA EU EEA EU28 EU27 EA18 EA17 -categories ALL -st_period 2013-01 -end_period 2015-12
echo "copying inflation,contribution and differential data.."
cp -R data/test/* ../web/data/
#sshpass -p "D.c.SCp-www" scp -r ../../web/* scp2www@datacenter.ihs.ac.at:visuals/inflation
#python MotherScript_comparisons.py -countries AT BE BG CZ DK DE EE IE EL ES FR HR IT CY LV LT LU HU MT NL PL PT RO SI SK FI SE UK IS NO CH EA EU EEA EU28 EU27 EA18 EA17 -categories ALL -st_period 2013-01 -end_period 2015-12
#cp -R data/test/* ../../web/data/
#sshpass -p "D.c.SCp-www" scp -r ../../web/* scp2www@datacenter.ihs.ac.at:visuals/inflation
