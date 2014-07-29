# PPMI study - Genetics - Preparation of PLINK files
# Christian Bracher, July 2014
#
# Background:  Genetics info is provided in PPMI in form of PLINK databases.
# Information is bound against a 'gene/allele' file and a 'subject' file.
# The PLINK .fam subject file lists unique PPMI subject ids, but not their
# corresponding condition - also, it still contains data from subjects who
# withdrew from the study.
#
# The collection of methods in this file is designed to update the PLINK
# subject file by entering subjects as 'affected' or 'not affected' by
# a condition.  To be flexible, 'condition' can be chosen to be 'PD'
# (Parkinson's disease), 'SWEDD' (PD with normal SPECT scan), or the
# presence of either of PD or SWEDD.
#
# Condition logic to be used, and the PLINK .fam subject file to be
# accessed as usual are controlled by a short JSON control string 
# (stored as a file).  The implementation can only work on one file
# at a time.

import pandas as pd
import numpy as np
import json as js
import sys


# *********** METHODS:

# Read the study subject database, and return a list of subject IDs,
# as well as a dictionary {subject_ID : condition}
#
# Parameters:  path & name of Patient Status information
# Returns:	 subject:condition dictionary

def subject_list_conditions(fileinfo = '../PPMI Data/Subject_Characteristics/Patient_Status.csv'):
	
	# Read Patient Status file:
	
	try:
		patientdata = pd.io.parsers.read_table(fileinfo, sep =',', header = 0, index_col = False)

	except IOError:
		print "ERROR:  Could not open PPMI Subject Database"
		raise IOError

	# For our purpose, we are really only interested in the IDs of subjects that
	# are enrolled in the study, and their condition (as determined by imaging)
	
	dropcols = patientdata.columns.values.tolist()[1:4]
	patientdata = patientdata.drop(dropcols, axis = 1)
	
	# Purge subject database - enrolled subjects only, please
	
	patientdata = patientdata[['PATNO','ENROLL_CAT']][(patientdata['ENROLL_STATUS'] == 'Enrolled')]
	subject_count = len(patientdata)
	
	# Extract ID : Condition dictionary
	
	subject_condition = {}
	
	for pat in range(0, subject_count):
		subject_condition[patientdata.iloc[pat][0]] = patientdata.iloc[pat][1]
	
	return subject_condition

# Read the instructions for modifying the PLINK file from a json object,
# stored as a file.
#
# Parameter: filepath/name to the control file.
#
# Returns:
# cohorts - a list of the conditions that make a subject 'affected' in the PLINK sense
# datafile - filepath/name to the PLINK .fam subject file
# 
# Format of the json control string:
#
# {"plink" : {"cohort" : ["HC" and/or "PD" and/or "SWEDD"], "filename" : "(path + name)"}}
#

def read_plink_instructions(fileinfo = '../PPMI Genetics/prepare_plink.json'):

	# Open information file.
	# All information is stored in the 'plink' dictionary (top level)

	try:
		overview = open(fileinfo, 'r')
	except IOError:
		print 'ERROR: Could not open information file'
		raise IOError
		
	contents = js.load(overview)['plink']
	overview.close()

	# Read in cohort information stored in 'cohort' key.
	# Subjects in these cohorts will be designated as 'affected.'
	
	cohorts = contents['cohort']
   
	# Check validity:

	if (cohorts == []):
		print "ERROR:  No cohorts specified for analysis"
		raise ValueError

	for group in cohorts:
		if not (group in ['HC', 'PD', 'SWEDD']):
			print 'ERROR:  Unknown cohort ', group
			raise ValueError

	# Read data file name

	datafile = contents['filename']
	
	return cohorts, datafile

# Save a copy of the original PLINK .fam file (original will be overwritten)
#
# Parameter:
# datafile - path/name of PLINK file (...).fam
#
# A copy will be written to disk as '(...).fam.old'

def plink_fam_copy(datafile):
	
	# Read the plink.fam description file
	# Make a copy 'plink.fam.old'
	
	# Try to read file:
	
	try:
		plink_fam_file = open(datafile, 'r')
	except IOError:
		print 'ERROR: Could not open PLINK file', datafile
		raise IOError
 
	contents = plink_fam_file.read()
	plink_fam_file.close()
	
	# Try to write out a copy of the file:
	
	try:
		plink_old_file = open(datafile + '.old', 'w')
	except IOError:
		print 'ERROR: Could not write copy of PLINK file', datafile
		raise IOError
 
	plink_old_file.write(contents)
	plink_old_file.close()

# Read the PLINK .fam file as a dataframe, indicate status (affected/non-affected/missing)
# of each subject, and write modified file back into position.
#
# Parameters:
# cohorts - a list of conditions ('HC', 'PD', and/or 'SWEDD') considered 'affected'
# datafile - path/name of the PLINK .fam file
# subject_condition - dictionary linking subject ID and condition for subjects enrolled
# in the PPMI study
	
def plink_fam_write_status(cohorts, datafile, subject_condition):
	
	# Read plink.fam file as a csv-type spreadsheet:
	
	plink_fam = pd.io.parsers.read_table(datafile, sep = ' ', header = None, index_col = None)

	# Read through rows in table:
	
	for subject in range(0, len(plink_fam)):
		
		# Find subject:
		
		subject_id = plink_fam.loc[subject, 0]
		
		# Is subject part of the study?
		
		if (subject_id in subject_condition.keys()):
			
			# Yes, store with proper code:
			
			condition  = subject_condition[subject_id]

			# Select plink code - 1 for unaffected, 2 for affected (by selected cohorts)

			affected = 1
			if condition in cohorts:
				affected = 2

			# Store this information back into the table

			plink_fam.loc[subject, 5] = affected
		else:
			
			# No, issue warning and ignore (keep -9 'missing' affected status):
			
			print 'Warning: Subject ID', subject_id, 'not found in study documents.  Ignoring entry.'
		
	# Store resulting table back into csv-type plink.fam file:
	
	try:
		plink_fam.to_csv(datafile, sep = ' ', header = False, index = False)
	except IOError:
		print 'ERROR: Could not write PLINK file', datafile
		raise IOError


# **** Main Program
#
# Execute this only if called directly from command line
#

if __name__ == '__main__':

	# Look for control file - if provided as command line argument.
	# First, define default name:

	ctrlfile = '../PPMI Genetics/prepare_plink.json'

	if len(sys.argv) > 1:
		ctrlfile = sys.argv[1]

	# Next, look for subject-condition file - if provided as command line argument.
	# First, define default name:

	subjfile = '../PPMI Data/Subject_Characteristics/Patient_Status.csv'
	
	if len(sys.argv) > 2:
		subjfile = sys.argv[2]

	# Grab subject_ID : condition lookup table

	subject_condition = subject_list_conditions(subjfile)

	# Read instructions - cohorts, data file to use

	cohort, datafile = read_plink_instructions(ctrlfile)

	# Copy the original .fam file for safekeeping

	plink_fam_copy(datafile)

	print 'Copied', datafile, 'to', datafile + '.old'

	# Read the .fam file, adjust subject status to affected/unaffected
	# (depending on instructions - list of cohorts viewed as affected)

	plink_fam_write_status(cohort, datafile, subject_condition)

	# Success!

	print 'SUCCESS:  Adjusted PLINK file', datafile