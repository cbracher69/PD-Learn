# PPMI Statistics Core Module
# Christian Bracher, July 2014

# ******** METHODS:

# 
# Unpickle the PPMI data object:
# Restore subject list and conditions, event and test lists;
# return data as pandas Panel object:
#
#   First (item) coordinate:  Event
#   Second (major) coordnate:  Subject
#   Third (minor) coordinate:  Test 
# 
# Parameter:  File name & path for pickled data object
# Returns:
# subject_list - a list of all subject IDs
# subject_condition - a dictionary that lists the cohort (condition) by subject ID
# event_list - a list of all events (timeline of study)
# test_list - a list of all study tests stored in the data object (clear text)
# test_dict - a dictionary PPMI test code : clear text descriptor
# data_panel - three-dimensional pandas data object.

import pandas as pd
import numpy as np
import json as js
import pickle

# PPMI machine learning:
import PPMI_learn as plearn

# PPMI graphics:
import PPMI_Gaussplots as pgauss

def unpickle_PPMI_data(filename = 'PPMI_data.pkl'):

	# Recover the pickled data:

	try:
		with open(filename, 'rb') as datafile:
			subject_list, subject_condition, event_list, test_list, test_dict, PPMI_array = pickle.load(datafile)
	
	except IOError:
		print 'ERROR:  Could not open pickled data object'
		raise IOError

	# Create pandas Panel object:

	data_panel = pd.Panel(data = PPMI_array, items = event_list, major_axis = subject_list, minor_axis = test_list)

	return subject_list, subject_condition, event_list, test_list, test_dict, data_panel

# Write out information about all available data into a JSON formatted string
#
# Parameter:  
# event_list - a list of all events (timeline of study)
# test_list - a list of all study tests stored in the data object (clear text)
# data_panel - three-dimensional pandas data object.
#
# Returns:
# available_data - a JSON string that contains a dictionary of all event-test combinations.

def list_available_data(event_list, test_list, data_panel):
    
    # Placeholder dictionary
    
    data_dict = {}
    
    # Step through list of study 'events' (timeline):
    
    for event in event_list:
        
        # Slice out dataframe from panel:
        
        event_frame = data_panel[event]
        
        # Create placeholder list:
        
        tests_in_event = []
        
        # Step through tests:
        
        for test in test_list:
            
            test_data = event_frame[test]
            
            # Check whether there is any data in this test series:
            
            contains_data = test_data.notnull().any()
            
            # Append if data was found:
            
            if (contains_data == True):
                tests_in_event.append(test)
                
        # Add sorted list to data dictionary, if any test was found for event:
        
        if (len(tests_in_event) > 0):
            tests_in_event.sort()
            data_dict.update({event : tests_in_event})
       
    # Dictionary for JSON format
    
    available_data = {'PPMI All Data': data_dict}
    
    # Return as JSON string, event keys sorted alphabetically 
    
    return js.dumps(available_data, sort_keys = True)

# Create lists that indicate membership of study subjects to the three 'cohorts':
# 'HC' (healthy control), 'PD' (Parkinson's Disease), 'SWEDD' (scan w/o evidence of dopaminergic deficiency)
#
# Parameter:  subject ID list, Subject:Condition dictionary
# Returns:  Dictionary containing membership lists for HC, PD, SWEDD cohorts

def create_cohort_filters(subject_list, subject_condition):
	
	# Turn subject:condition dictionary into a pandas Series object:

	cond_series = pd.Series(subject_condition)
	
	# Create membership lists of individual subjects:

	HC_filter = (cond_series == 'HC').tolist()
	PD_filter = (cond_series == 'PD').tolist()
	SW_filter = (cond_series == 'SWEDD').tolist()
	
	# 'Zip' this information into a membership dictionary

	filter_dict = {'HC':HC_filter, 'PD':PD_filter, 'SWEDD':SW_filter}

	return filter_dict

# Read instructions for test/subject/event selection from file (json format)
# (see separate instructions for format)
#
# Parameter:  File path & name
# Returns:
# cohorts - a list of the cohorts requested (some combination of 'HC', 'PD', 'SWEDD')
# selections - a list of the individual combinations of event and test requested,
#			  in the form [[event1, test1], [event2, test2], ...]

def extract_information(fileinfo = '../PPMI Analysis/employdata.json'):
	
	# Open information file
	
	try:
		with open(fileinfo, 'r') as overview:
			contents = js.load(overview)['employdata']

	except IOError:
		print 'ERROR:  Could not read data selection file'
		raise IOError
	
	# Read in cohort information stored in 'cohort' key, then remove
	
	cohorts = contents.pop('cohort', [])
   
	# Check validity:
	if (cohorts == []):
		print "ERROR:  No cohorts specified for analysis"
		raise ValueError

	for group in cohorts:
		if not (group in ['HC', 'PD', 'SWEDD']):
			print 'ERROR:  Unknown cohort ', group
			raise ValueError

	# Build placeholder for selections from dataset
	
	selections = []
		
	# Read in information for each dataset - events and tests desired
	# Extract every combination of event and test
	# (Note:  Combinations formed separately for each entry in the information file)
	
	datasets = contents.keys()

	for entry in datasets:
		events = contents[entry]['events']
		tests =  contents[entry]['tests']
		
		for ev in events:
			for tt in tests:
				selections.append((ev, tt))

	# Render selections unique:
	
	selections = list(set(selections))

	return cohorts, selections

# Extract desired data from general data storage object
# 
# Parameters:
# data_panel - the 3D storage object for PPMI data
# cohorts - list of subject cohorts to be included
# selections - list of event-test combinations to be included
# subject_list - list of all subject IDs
# subject_condition - dictionary of subject cohort membership
#
# Returns:
# subj_cond - series object containing condition (data) for each subject in table (index)
# data_table - dataframe containing test results in selection
#
# Requires:
# Create_cohort_filters(...) - library of cohort membership filters
#

def build_data_table(data_panel, cohorts, selections, subject_list, subject_condition):
	
	# Template for data table

	data_table = pd.DataFrame()

	# Populate data table with desired test/event combinations

	for group in selections:
		
		# Make sure test/event really exists:

		try:
			event_data = data_panel[group[0]][group[1]]
		except:
			print 'ERROR:  Unknown event or test ', group
			raise ValueError

		# Invent column name for combination:

		event_name = group[1] + ' [' + group[0] + ']'

		# Store data as column in table

		data_table[event_name] = event_data

	# Create a filter for cohorts - select all subjects in any of the cohorts listed
		
	cohort_filter = [False for subject in subject_list]	
	
	# Read in global filter information:

	filter_dict = create_cohort_filters(subject_list, subject_condition)

	# Determine union of membership lists

	for group in cohorts:
		cohort_filter = [i|j for i,j in zip(cohort_filter, filter_dict[group])]

	# Apply subject filter	
		
	data_table = data_table[cohort_filter]	

	# Clean out subjects that have incomplete information for any test:

	subjects_complete = (data_table.notnull().all(axis = 1))
	data_table = data_table[subjects_complete]

	# Warn user if selection is empty:

	if (len(data_table) == 0):
		print 'WARNING:  No subjects available'

	# Retrieve list of subjects in this set, their condition:

	subjects_in_selection = data_table.index
	conditions_in_selection = [subject_condition[subj] for subj in subjects_in_selection]

	# Create a subject-condition dictionary in the form of a pandas Series object:

	subj_cond = pd.Series(conditions_in_selection, index = subjects_in_selection)

	return subj_cond, data_table

# Find the cohort sizes in a subject sample, and update the list of cohorts present:
#
# Parameters:  
# subj_cond - pandas Series object having subject ID as index, subject condition as data
#
# Returns:
# data_counts - pandas Series object listing number of subjects in total, and in each
#			   condition separately.
# cohorts -	 list of patient cohorts ('HC', 'PD', 'SWEDD') present in data

def data_count(subj_cond):
	
	# Find/store cohort sizes, subject total.
	# Recreate cohort list - consider only conditions that appear in selected data.
	
	# Step 1: Count cohorts
	
	num_HC = subj_cond.tolist().count('HC')
	num_PD = subj_cond.tolist().count('PD')
	num_SW = subj_cond.tolist().count('SWEDD')
		
	data_counts = pd.Series([num_HC + num_PD + num_SW, num_HC, num_PD, num_SW], index = ['subjects', 'HC', 'PD', 'SWEDD'])
	
	# Step 2: Repopulate cohort list
		
	cohorts = []
	filter_dict = {}
	
	if (num_HC > 0):  
		cohorts.append('HC')
	   
	if (num_PD > 0):  
		cohorts.append('PD')
		
	if (num_SW > 0):  
		cohorts.append('SWEDD')
	
	if (len(cohorts) == 0):
		print "WARNING:  No subjects selected"
		
	return data_counts, cohorts
 
# Create a table that contains statistical information for each test considered:
# * Global average over all subjects
# * Sample standard deviation over subjects
# * Averages for each cohort (HC, PD, SWEDD)
#
# Requires:
# data_table - pandas dataframe containing test results
# subj_cond  - pandas series object containing condition of subjects
# cohorts	 - list of cohorts present in data
#
# Returns:
# data_avg   - pandas dataframe storing averages and standard deviation

def data_stats(data_table, subj_cond, cohorts):  

	# Find global and cohort averages, global deviation
	
	# List of tests:
	
	column_list = data_table.columns.tolist()
	
	# Prepare pandas DataFrame for storage of averages:
	
	index_list = ['global mean', 'std dev', 'HC mean', 'PD mean', 'SWEDD mean']
	
	data_avg = pd.DataFrame()
	
	# Go through test columns:
		
	for test in column_list:
		
		# Isolate test results:
		
		aux_series = data_table[test].astype(float)
		
		glob_mean = aux_series.mean()
		glob_std  = aux_series.std()
		
		# Select cohorts - find averages only for existing cohorts
		
		if ('HC' in cohorts):
			hc_mean = aux_series[(subj_cond == 'HC')].mean()
		else:
			hc_mean = None
			
		if ('PD' in cohorts):
			pd_mean = aux_series[(subj_cond == 'PD')].mean()
		else:
			pd_mean = None
		
		if ('SWEDD' in cohorts):
			sw_mean = aux_series[(subj_cond == 'SWEDD')].mean()
		else:
			sw_mean = None
				
		# Store information:
	
		data_avg[test] = pd.Series([glob_mean, glob_std, hc_mean, pd_mean, sw_mean], index = index_list)
	
	return data_avg

# Normalize data set - express test results as deviation from the respective test average, 
# in units of the sample standard deviation of that test
# 
# Requires:
# data_table - pandas dataframe containing original test results
# data_avg   - pandas dataframe containing average test results
#
# Returns:
# norm_table - pandas dataframe containing normalized test results

def normalize_table(data_table, data_avg):
	
	# Take a table of test results and express it in units of std deviations from the mean
	
	column_list = data_table.columns.tolist()
	norm_table = data_table.copy()
	
	# Normalize table - express deviation from column average in units of column standard deviation
	
	for column in column_list:
		avg = data_avg[column]['global mean']
		std = data_avg[column]['std dev']
		
		norm_table[column] = norm_table[column].apply(lambda x : (float(x) - avg) / std)
	
	return norm_table


# Given the data selection, find all available plots and list information in a JSON string object.
#
# By definition, the core suggests a profile plot only if a single data series is chosen.
# If two data series are chosen, it suggests a correlation plot.
# If two or more data series are chosen, and the data contains at least two cohorts, ROC plots are available.
# If more than two series are chosen, and the data contains all three cohorts, it suggests a center-of-mass plot, too.
#
# Parameters:
# norm_table - Dataframe containing normalized data
# cohorts - list of cohorts present in data
#
# Returns:
# available_plots - JSON string object that contains a dictionary of test types:
#
#   ('Correlation', 'Profile', 'Projection', 'ROC Curve')
#
# pointing to a list of available options (e.g. 'Center-of-Mass' or 'Logistic Regression')

def list_available_plots(norm_table, cohorts):

    # Set up dictionaries, lists:
    
    test_dict = {'Profile':[], 'Correlation':[], 'Projection':[], 'ROC Curve':[]}
       
    # Find number of tests selected:
    
    test_count = len(norm_table.columns)

    if (test_count == 1):
        
        # Add profile plot
        
        test_dict['Profile'].append('Profile')
        
    else:
        if (test_count == 2):
            
            # Add correlation plot
            
            test_dict['Correlation'].append('Correlation')
            
        if (len(cohorts) > 1):
            
            # Add ROC plots
            
            test_dict['ROC Curve'].extend(['Logistic Regression', 'kNN', 'Random Forest'])
            
        if ((test_count > 2) and (len(cohorts) > 2)):
            
            # Add center-of-mass view:
            
            test_dict['Projection'].append('Center-of-Mass')
    
    # Dictionary for JSON format
    
    available_tests = {'PPMI Tests' : test_dict}
    
    return js.dumps(available_tests, sort_keys = True)

    # Respond to image request - run graphics, return PNG image file as string
#
# Image requests have the form of a short JSON string:
#
#    {"PPMI Image" : {"Type" : type, "Option" : option}}
#
# where 'type' is one of {'Correlation', 'Profile', 'Projection', 'ROC Curve'}, and 'option' indicates the subtype.
#
# Parameters:
# image_request - JSON command string (see above)
# norm_table - dataframe containing normalized test data
# data_avg - dataframe containing basic data statistics
# subj_cond - pandas series containing the subject ID : cohort lookup table
# cohorts - list of cohorts present in data
# data_counts - pandas series containing number of subjects in each cohort
#
# Returns:
# image_data - string containing the graphics data in PNG format

def create_plot(image_request, norm_table, data_avg, subj_cond, cohorts, data_counts):
    
    # Turn request into dictionary, then extract option chosen:
    
    image_dict   = js.loads(image_request)['PPMI Image']
    image_type   = image_dict['Type']
    image_option = image_dict['Option']
    
    # Select type, and render image:
    
    if (image_type == 'Profile'):
        
        # No options here ... find the single test selected
        
        test_name = norm_table.columns[0]
        test_data = norm_table[test_name]
        image_data = pgauss.profile_gauss(test_data, subj_cond, cohorts, data_counts)
        
    elif (image_type == 'Correlation'):
        
        # Again, no options:
        
        test1_name = norm_table.columns[0]
        test1_data = norm_table[test1_name]
        test2_name = norm_table.columns[1]
        test2_data = norm_table[test2_name]
        
        image_data = pgauss.scatter_gauss(test1_data, test2_data, subj_cond)
        
    elif (image_type == 'Projection'):
        
        # No options here yet ...
        
        image_data = plearn.center_mass_view(norm_table, data_avg, subj_cond, cohorts)
        
    elif (image_type == 'ROC Curve'):
        
        # Calculate ROC crve with classifier chosen via the image option:
        
        image_data = plearn.plot_roc_curve(norm_table, subj_cond, cohorts, image_option)
        
    return image_data