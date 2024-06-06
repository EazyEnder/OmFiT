"""
Convert a json file to a text file, only for the json exported using personnals scripts
"""

import os, sys
import json

POSITION = "wt5"
DIR_PATH = "/media/irina/LIPhy-INFO/test/nice_ss30_nov13-20_2023/"+POSITION+"/"
JSON_PATH = DIR_PATH+"result.json"

def argsort(seq):
    return sorted(range(len(seq)), key=seq.__getitem__)
    
def line_builder(array):
	string = ""
	for a in array:
		string += str(a) + " "
	return string+"\n"

def main():
	f = open(JSON_PATH)
	data = json.load(f)
	
	for channel in data.keys():
		#first line of the txt file
		prefix = []
		#each row is a frame / line in the txt file
		rslt_matrix = []
		line_index= 0
		for index in data[channel]:
			index_values = []
			for key in data[channel][index]:
				if not(key in prefix):
					prefix.append(key)
				index_values.append(data[channel][index][key])
			index_values = list(zip(*index_values))
			for line in index_values:
				rslt_matrix.append(line)
				line_index += 1
		#Serialization
		txt = open(DIR_PATH+channel+".txt", "w")
		txt.write(line_builder(prefix))
		for line in rslt_matrix:
			txt.write(line_builder(line))
		txt.close()
	print("Conversion finished")
	
main()

