# PPMI Study Analysis
# Patch the PPMI Biomarker Analysis Data Files 
# Christian Bracher - July 17, 2014

import pandas as pd
import numpy as np
import matplotlib.pyplot as pl

# Read in a raw data set from the study (.CSV format)
# Argument: Path & filename
# Returns:  Dataframe object, containing the file contents

def read_raw_data(fileinfo):
	
	try:
		data_raw = pd.io.parsers.read_table(fileinfo, sep =',', header = 0, index_col = False)

	except IOError:
		print 'ERROR:  Could not open biomarker database', fileinfo
		raise IOError
	
	return data_raw

# Some files contain multiple results for the same measurement or test because the analysis needed to
# be re-run.  This method eliminates obsolete entries for such tests, and only keeps the most recent
# results.  The data is supplied as a dataframe, and returned as a cleaned dataframe, sorted by patient ID. 

def discard_obsolete_data(database):
    
	# This is currently set up for the biomarkers database only - extend as needed.

	# Idea:  Sort database by entries expected to be identical for repeated tests, expect for the data of analysis

	testlist = database.sort(['PATNO', 'CLINICAL_EVENT', 'TYPE', 'TESTNAME', 'RUNDATE'], ascending = False) 
	test_size = len(testlist)

	# Extract a subset of columns that will be matching for tests that are redone:

	comparelist = testlist[['PATNO', 'CLINICAL_EVENT', 'TYPE', 'TESTNAME']]

	# Now, step thru the sorted list line by line.  If the columns match up, only keep the newest result.
	# (The list last_entry stores the rows in the sorted database to be kept.)

	row_keep = []
	last_entry = []

	for row in range(0, test_size):
		entry = comparelist.iloc[row].tolist()
		        
		if (entry != last_entry):
			row_keep.append(row)

		last_entry = entry

	# Eliminate the duplicate/obsolete rows

	testlist = testlist.take(row_keep, axis = 0)

	# Sort the database again, in a more user-friendly ascending format, and return:

	return testlist.sort(['PATNO', 'CLINICAL_EVENT', 'TYPE', 'TESTNAME', 'RUNDATE'], ascending = True)

# Bring the Event column into PPMI standard form:

def clean_event_column(database):

	# Translation Dictionary:

	event_dict = {'Screening Visit':'SC', 'Baseline Collection':'BL', 'Visit 01':'V02', 'Visit 02':'V02', 
				  'Visit 03':'V03', 'Visit 04':'V04', 'Visit 05':'V05', 'Visit 06':'V06',
				  'Visit 07':'V07', 'Visit 08':'V08', 'Visit 09':'V09', 'Visit 10':'V10',
				  'Visit 11':'V11', 'Visit 12':'V12'}

	# Prepare list of recognized keys:
	
	event_list = event_dict.keys()

	# Discard all rows with non-recognized keys by Boolean selection:

	database = database[(database['CLINICAL_EVENT'].isin(event_list))]

	# Rename the column:

	database = database.rename(columns = {'CLINICAL_EVENT' : 'EVENT_ID'})

	# Translate the entries into standard format (if they have a translation):

	database['EVENT_ID'] = database['EVENT_ID'].apply(lambda x : event_dict[x])

	return database

# Rewrite the file contents into standard PPMI format:
# Read out a list of all tests performed
# Create dataframes containing rows with each test individually
# Append the data as columns to a new dataframe

def rewrite_biomarker_data(database):

	# Read test types performed:
	test_list = database['TESTNAME'].tolist()

	# Eliminate Duplicates:
	test_set = set(test_list)

	# Write back into list form:
	test_list = list(test_set)

	# Extract results for first test in list only - extract subject IDs and test values, rename the column after the test:

	cleanbase = database[['PATNO', 'EVENT_ID', 'TESTVALUE']][(database['TESTNAME'] == test_list[0])]
	cleanbase = cleanbase.rename(columns = {'TESTVALUE' : test_list[0]})
	
	# Do the same thing for all other named tests, but merge the result with the initial result:

	for i in range(1, len(test_list)):
		auxbase = database[['PATNO', 'EVENT_ID', 'TESTVALUE']][(database['TESTNAME'] == test_list[i])]
	 	auxbase = auxbase.rename(columns = {'TESTVALUE' : test_list[i]})
	 	
	 	cleanbase = pd.merge(cleanbase, auxbase, on = ['PATNO','EVENT_ID'], how = 'outer')

	# Return the standardized database for biomarkers:

	return cleanbase

# This takes care of entries of 'below detection limit' and similar in a numerical column.

def clean_entries(database):

	# Translation Dictionary:

	def clean_hemoglobin_entries(HB_value):

		if (HB_value == 'below detection limit'):
			HB_value = 0
		elif ((HB_value == '>12500 ng/ml') or (HB_value == '>12500ng/ml')):
			HB_value = 12500

		return HB_value

	# Clean non-numerical entries:

	database['CSF Hemoglobin'] = database['CSF Hemoglobin'].apply(clean_hemoglobin_entries)

	return database



#### RUN THIS SCRIPT ONLY IF NOT CALLED AS A METHOD:

if __name__ == '__main__':

	import pandas as pd
	import numpy as np
	import json as js
	import sys

	# Default file names:

	raw_bio_file = ['../PPMI Data/Biospecimen_Analysis/Biospecimen_Analysis_Results.csv',
					'../PPMI Data/Biospecimen_Analysis/Pilot_Biospecimen_Analysis_Results_Projects_101_and_103.csv']

	outputfile = '../PPMI Data/Biospecimen_Analysis/biomarkers_clean.csv'

	# Replace by user-supplied names if command line argument is given:

	if (len(sys.argv) > 1):

		# Extract file name for JSON control structure:
		fileinfo = sys.argv[1]

		# Try to open this file:

		try:
			with open(fileinfo, 'r') as overview:
				
				# All data are transmitted as values of the principal key 'biomarkers':

				contents = js.load(overview)['biomarkers']

		except IOError:
			print 'ERROR:  Could not read control file', fileinfo
			raise IOError

		# Extract information:
		#
		# The key 'raw' must have a list of input file names (raw data) as values,
		# the key 'output' should contain the path&name for the output database, conforming to PPMI format
		#
		# (other keys simply go unrecognized)

		raw_bio_file = contents['raw']
		outputfile   = contents['outputfile']

	# Load the biomarker files, and join them together, if necessary:

	raw_bio = read_raw_data(raw_bio_file[0])

	if (len(raw_bio_file) > 1):
		for filename in raw_bio_file[1:]:
			raw_bio_new = read_raw_data(filename)
			raw_bio = pd.concat([raw_bio, raw_bio_new])

	# Eliminate obsolete data from tests that had to be re-run:

	clean_bio = discard_obsolete_data(raw_bio)

	# Bring event description into PPMI standard format:

	clean_bio = clean_event_column(clean_bio)

	# Rewrite data into standard form:

	clean_bio = rewrite_biomarker_data(clean_bio)

	# Clean out disruptive non-numerical entries:

	clean_bio = clean_entries(clean_bio)

	# Store for use with the conforming data files:
	
	try:
		clean_bio.to_csv(outputfile, index = False)

	except IOError:
		print 'ERROR:  Could not write cleaned biomarker database to file', outputfile
		raise IOError

	# Success!

	print 'Wrote', len(clean_bio), 'entries to', outputfile









