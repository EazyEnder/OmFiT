"""
Python script: Correct result.json files using older versions
"""

import os, sys, json

file_path = "/media/irina/5C00325A00323B7A/Zack/nov20/wt2/"+"result.json"
f = open(file_path)
data = json.load(f)
f.close()
new_file_path = "/media/irina/5C00325A00323B7A/Zack/data/export/wt2Tc1/"+"wt2Tc1.json"
f = open(new_file_path)
new_data = json.load(f)
f.close()

def argsort(seq):
	return sorted(range(len(seq)), key=seq.__getitem__)

def getOldIndexesFlatten(data):
	old_indexes = []
	for channel in data.keys():
		for index in data[channel].keys():
			old_indexes.extend(data[channel][index]["old_index"])
		break
	return old_indexes

recent_indexes = getOldIndexesFlatten(new_data)

for channel in data.keys():
	global_idx_offset = 0
	sorted_keys_indexes = argsort([int(nbr) for nbr in (data[channel].keys())])
	for index in [data[channel].keys()[ski] for ski in sorted_keys_indexes]:
		gii = data[channel][index]["old_index"]	
		index_to_keep = []
		for i in range(len(gii)):
			if not(gii[i] in recent_indexes):
				continue
			index_to_keep.append(i)
		for k in data[channel][index].keys():
			if "old_index" in k:
				continue
			if not("global_index" in k):
				data[channel][index][k] = [data[channel][index][k][i] for i in index_to_keep]
			else:
				if "old_index" in data[channel][index].keys():
					data[channel][index]["old_index"] = [data[channel][index]["old_index"][i] for i in index_to_keep]
					continue
				data[channel][index]["old_index"] = [data[channel][index][k][i] for i in index_to_keep]
		data[channel][index]["global_index"] = [i+global_idx_offset for i in range(len(index_to_keep))]
		global_idx_offset += len(index_to_keep)
				
	
with open(new_file_path, "w") as outfile:
	json.dump(data, outfile, indent=2)
print("JSON " + new_file_path + " modified")