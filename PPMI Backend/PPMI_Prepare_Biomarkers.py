# PPMI Study Analysis
# Patch the PPMI Biomarker Analysis Data Files 
# Christian Bracher - July 17, 2014

# Update - August 18, 2014:
# Fix an obscure bug in the event directory
# Sort output database by subject ID, event ID
# Utilize genetic data - fix ApoE allele entries
# Generate numeric columns for ApoE genotype (# of e2, e3, e4 alleles)
# Transform single nucleotid polymorphism (SNP) data into numeric form
# Numerify 'SNCA_multiplication' data

import pandas as pd
import numpy as np

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

	event_dict = {'Screening Visit':'SC', 'Baseline Collection':'BL', 'Visit 01':'V01', 'Visit 02':'V02', 
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
	test_list = sorted(list(test_set))

	# Extract results for first test in list only - extract subject IDs and test values, rename the column after the test:

	cleanbase = database[['PATNO', 'EVENT_ID', 'TESTVALUE']][(database['TESTNAME'] == test_list[0])]
	cleanbase = cleanbase.rename(columns = {'TESTVALUE' : test_list[0]})
	
	# Do the same thing for all other named tests, but merge the result with the initial result:

	for i in range(1, len(test_list)):
		auxbase = database[['PATNO', 'EVENT_ID', 'TESTVALUE']][(database['TESTNAME'] == test_list[i])]
	 	auxbase = auxbase.rename(columns = {'TESTVALUE' : test_list[i]})
	 	
	 	cleanbase = pd.merge(cleanbase, auxbase, on = ['PATNO','EVENT_ID'], how = 'outer')

	# Return the standardized database for biomarkers, sorted by subject ID and event:

	return cleanbase.sort(['PATNO', 'EVENT_ID'])

# This takes care of entries of 'below detection limit' and similar in a numerical column.

def clean_entries(database):

	# Translation Dictionary:

	def clean_string_entries(data_value):

		if (data_value == 'below detection limit'):
			return 0
		
		# This entry occurs in the 'CSF Hemoglobin' column:

		if ((data_value == '>12500 ng/ml') or (data_value == '>12500ng/ml')):
			return 12500.0

		return data_value

	# Clean non-numerical entries:

	database = database.applymap(clean_string_entries)

	return database

# Clean ApoE genotype data, and turn into numerical form:
# - Merge the columns 'ApoE_Genotype' and 'APOE GENOTYPE'
# - Create numerical columns that contain the number of e2, e3, and e4 alleles for each subject

def numerify_apo_e(database):

	# Combine the two columns with partial results into one
	database['ApoE'] = database['ApoE_Genotype'].fillna(value = database['APOE GENOTYPE'])

	# Retain only combined column, toss out originals:
	database = database.drop(['APOE GENOTYPE', 'ApoE_Genotype'], axis = 1)

	# Numerify data - create three numerical columns that list the number of 
	# ApoE e2, e3, e4 alleles in the genotype

	def count_alleles(genotype, allele):

		# Hacky workaround - 'nan' is type(float), all valid entries are strings.
		# Entries are of the form 'e2/e4' etc., so we'll just count occurrences of
		# allele names in the string
	
		if (type(genotype) == str):
			return float(genotype.count(allele))
		else:
			return np.nan

	database['ApoE e2 Count'] = database['ApoE'].apply(lambda x: count_alleles(x, 'e2'))
	database['ApoE e3 Count'] = database['ApoE'].apply(lambda x: count_alleles(x, 'e3'))
	database['ApoE e4 Count'] = database['ApoE'].apply(lambda x: count_alleles(x, 'e4'))

	# Remove the original column:
	return database.drop('ApoE', axis = 1)

# Genetic biomarkers - single nucleotid polymorphisms (SNPs)
# The database contains numerous tests for SNPs that generally list the genetic status
# as (DNA base #1)/(DNA base #2), e.g., 'A/A', 'C/T', etc.
# For each SNP, there is variation in a single base, with only two variants per allele
# (e.g. A/A, A/C, C/C)
# To 'numerify' these, use lexicographical order (A < C < G < T), and assign a value of
# -1/2 to the 'smaller' nucleotid, and +1/2 to the 'bigger' nucleotid. The sum of the
# two values then indicates the genotype.
#
# Ex.:  If the SNP involves a variability of the base C <-> T, there are three genotypes:
#
# 	C/C - numerical value -1
#	C/T - numerical value  0
#   T/T - numerical value +1
#
# (This method guarantees a value of 0 for mixed genotype.)
# The column names are amended to indicate the type of polymorphism, and assigned values.

def numerify_snps(database):

	# First, find all SNP data in the biomarkers file.  Names for columns always start
	# with 'rs':

	biomarker_list = list(database.columns)

	SNP_list = []
	for column in biomarker_list:
		if column[0:2] == 'rs':
			SNP_list.append(column)

	# Helper function:  Lexicographical model for numerical encoding of SNPs
	# Idea:  All SNPs are of the form --, -+, ++, where - and + stand for two nucleotides
	# We'll give a value of +1/2 to '+' and -1/2 to '-'
	# By definition, - and + are assigned in the sequence A < C < G < T
	# Let's include a 'hint' about which letter - and + stand for in the column header

	def find_nucleotid_values(data_table, snp):
	
		# Step #1: Find the nucleotids involved in a SNP:
		
		nucleotid_dict = {'A' : 0, 'C' : 0, 'G' : 0, 'T' : 0}
		nucleotids = nucleotid_dict.keys()
		
		# Count nucleotids for SNP in database:
		
		for entry in data_table[snp]:
	 
			# Hacky workaround - 'nan' is type(float), all valid entries are strings:
			
			if (type(entry) == str):
				# Tally up nucleotids - look for letters in '(base 1)/(base 2)':
				
				for nuc in nucleotids:
					nucleotid_dict[nuc] += entry.count(nuc)
		
		# Now, assign values of +1/2 or -1/2 to nucleotids:
		# Also, generate symbolic code '-(base 1)+(base 2)' that indicates the pair of
		# bases involved in the SNP, and the assignment of negative/positive values:
		
		current_value = -0.5
		code = ' '
		
		for nuc in 'ACGT':
			if nucleotid_dict[nuc] > 0:
				
				# Add symbolic code: (+) or (-) nucleotid
				
				if current_value < 0:
					code = code + '-' + nuc
				else:
					code = code + '+' + nuc

				# Assign value of -0.5 for first nucleotid, +0.5 for second nucleotid
					
				nucleotid_dict[nuc] = current_value
				current_value += 1.0
				
		return nucleotid_dict, code

	# Helper function - find numerical code for genotype in SNP

	def snp_to_value(genotype, nuc_values):

		# Add the values of the pair of nucleotids together, but leave 'NaN' for absent values intact.
		# Hacky workaround - 'nan' is type(float), all valid entries are strings:
		
		if (type(genotype) == str):
			return float(nuc_values[genotype[0]] + nuc_values[genotype[2]])
		else:
			return np.nan

	# Helper function - rewrite SNP biomarker column in numerical form: 

	def assign_snp_value(data_table, snp):
		nuc_vals, code = find_nucleotid_values(data_table, snp)
		
		# Assign numerical values for SNPs, drop original columns
		
		data_table['SNP ' + snp + code] = data_table[snp].apply(lambda x: snp_to_value(x, nuc_vals))
		
		return data_table.drop(snp, axis = 1)

	# Numerify each SNP data column:
	
	for snp in SNP_list:
		database = assign_snp_value(database, snp)

	return database

# Numerify SNCA multiplication codes
# 'SNCA multiplication' is a data column containing text descriptors.
# We numerify data by the replacement list:
#
# - 'NormalCopyNumber' (dominant entry)  --> 0
# - 'CopyNumberChange' (rare)  --> 1
# - 'NotAssessed'  --> np.nan

def numerify_snca_multiplication(database):

	# Dictionary:

	snca_dict = {'NormalCopyNumber' : 0.0, 'CopyNumberChange' : 1.0, 'NotAssessed' : np.nan}

	# Helper function - replace SNCA code

	def snca_to_value(snca_type, snca_dict):

		# Translate into numerical values, but leave 'NaN' for absent values intact.
		# Hacky workaround - 'nan' is type(float), all valid entries are strings:
		
		if (type(snca_type) == str):
			return snca_dict[snca_type]
		else:
			return np.nan

	# Assign numerical values
		
	database['SNCA_multiplication'] = database['SNCA_multiplication'].apply(lambda x: snca_to_value(x, snca_dict))
		
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
	clean_bio = numerify_snca_multiplication(clean_bio)

	# Clean Apolipoprotein E genetic data:

	clean_bio = numerify_apo_e(clean_bio)

	# Turn single nucleotid polymorphism (SNP) data into numerical form:

	clean_bio = numerify_snps(clean_bio)

	# Store for use with the conforming data files:
	
	try:
		clean_bio.to_csv(outputfile, index = False)

	except IOError:
		print 'ERROR:  Could not write cleaned biomarker database to file', outputfile
		raise IOError

	# Success!

	print 'Wrote', len(clean_bio), 'entries to', outputfile