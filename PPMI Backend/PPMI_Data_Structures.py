# PPMI Data Importer
# Christian Bracher, July 2014
#
# Idea:  Import numerical data from PPMI datafiles into a three-dimensional database
#        using a 3D numpy array, and ultimately the pd.PANEL data structure 
# 
# The data will be indexed along three 'axes':
#
#   * by date ('event' in PPMI speak)
#   * by subject ID
#   * by test performed
#
# In addition, we'll establish lists of subjects, events, and tests,
# and create a subject : condition dictionary.


# *********** METHODS:

# Read the study subject database, and return a list of subject IDs,
# as well as a dictionary {subject_ID : condition}
#
# Parameters:  path & name of Patient Status information
# Returns:     list of subject IDs, subject:condition dictionary

def subject_list_conditions(fileinfo = '../PPMI Data/Subject_Characteristics/Patient_Status.csv'):
    
    # Read Patient Status file:
    
    try:
        patientdata = pd.io.parsers.read_table(fileinfo, sep =',', header = 0, index_col = False)

    except IOError:
        print 'ERROR:  Could not open subject master file'
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
    
    # Extract list of actual study subjects, count them
    
    subject_list = subject_condition.keys()
    subject_list.sort()
    
    return subject_list, subject_condition


# Create the list of event codes (timeline of study)
# This seems to be very much fixed, so we'll keep it hard-coded.
#
# Parameters:  none
# Returns:     list of event codes
#
# 'SC' = screening visit, 'BL' = baseline visit, 'Vxx' = visit #xx

def event_list_create():
    
    event_list = ['SC', 'BL', 'V01', 'V02', 'V03', 'V04', 'V05', 'V06', 'V07', 'V08', 'V09', 'V10', 'V11', 'V12']
    
    return event_list


# Next, we need a list of tests to be included in the database, and the files where they are found.  
# We assume that all results to be included are in NUMERICAL form, otherwise they will have to be translated first.
# Data records must follow PPMI 'standard convention,' containing subject ID ('PATNO') and event ID ('EVENT_ID')
# as columns, and test results as columns, with headers labeling the tests.
#
# Notably, the Biomarkers database does NOT heed this convention, and must be cleaned and transformed first.
# Run the script 'PPMI_Prepare_Biomarkers' to create a conforming database.
#
# Necessary information (dataset, file, list of tests, test dictionary) is conveyed in JSON format.  
# See separate documentation for the format used.
#
# Parameters:  Test information as JSON file
# Returns:     list of files, list of tests, directory (PPMI study codes : descriptors)
#
# The list of tests contains cleartext column descriptors. The directory translates the shortcuts used by PPMI
# into the cleartext descriptors.
#
# If more than one shortcut points to the same descriptor, the values will be added up. 
# (This is very helpful for summarizing detailed questionnaire response data.)

def extract_test_information(fileinfo = '../PPMI Analysis/selectdata.json'):
    
    # Set up lists/dicts:

    file_list = []
    test_list = []
    test_dict = {}
    
    # Open information file
    
    try:
        with open(fileinfo, 'r') as overview:
            selection = js.load(overview)['selectdata']

    except IOError:
        print 'ERROR:  Could not open PPMI test information file', fileinfo
        raise IOError
    
    # Read in information for each dataset - file locations, tests in descriptor/PPMI code
    
    datasets = selection.keys()

    for entry in datasets:
        file_list.append(selection[entry]['filename'])
        test_list += selection[entry]['testlist']
        test_dict.update(selection[entry]['testdict']) 
    
    return file_list, test_list, test_dict


# Unfortunately, not all PPMI data files follow the same format convention.
# We'll implement a readout method for the most common format:
#
# Subject ID - Event ID - Test#1 - Test#2 - etc. 
#
# For databases in different format (Biomarkers), use a conversion algorithm first.

def read_PPMI_data(fileinfo, infolog, data_array, subject_list, event_list, test_list, test_dict):
    
    # Add data contained in PPMI file to array of data
    # 
    # fileinfo - path & filename to PPMI data file
    # infolog - file handle (file object open with write access) for logfile output
    # data_array - three-dimensional array to store data
    # subject_list - list of all study subjects
    # event_list - list of study 'events' (timeline)
    # test_list - list of desired data columns (readable descriptors)
    # test_dict - translation dictionary PPMI abbreviation : descriptor

    # Open database:

    try:
        ppmi_data = pd.io.parsers.read_table(fileinfo, sep =',', header = 0, index_col = False)

    except IOError:
        print 'ERROR:  Could not open PPMI database file', fileinfo
        raise IOError

    # Find dimensions of data file:

    rowcount = len(ppmi_data)
    
    columns  = ppmi_data.columns.tolist()
    colcount = len(columns)

    colset   = set(test_dict.keys())
    
    # Read PPMI data, row by row:
    
    for row in range(0, rowcount):
        
        # Find subject and event IDs first:
        
        subject_ID = ppmi_data.ix[row,'PATNO']
        event_ID = ppmi_data.ix[row,'EVENT_ID']
    
        # Is the data entry recognizable?
        
        if ((subject_ID in subject_list) and (event_ID in event_list)):
            subject_index = subject_list.index(subject_ID)
            event_index = event_list.index(event_ID)
           
            # Yes, check for columns of interest:
            
            for col in columns:
                if (col in colset):
                    
                    # Translate Description:
                    
                    test_index = test_list.index(test_dict[col])
                    
                    # Read & store value in array:
                    
                    entry = ppmi_data.ix[row, col]
                    
                    # Initialize entry if encountered for the first time:
                    
                    if (np.isnan(data_array[event_index, subject_index, test_index]) == True):
                        data_array[event_index, subject_index, test_index] = 0
                    
                    # Columns that are translated to the same descriptions are added together.
                    # This requires purely numerical input ... try to catch scattered mal-formed text entries here:
                    
                    try:
                        if entry == 'below detection limit':
                            entry = 0

                        entry = float(entry)
                        data_array[event_index, subject_index, test_index] += entry
                    
                    except ValueError:
                        
                        # Give detailed error information
                        
                        infolog.write('\t\t TROUBLE:  Encountered non-numerical data while trying to import\n')
                        infolog.write('\t\t\t Offending entry: ' + entry + '\n')
                        infolog.write('\t\t\t File: ' + fileinfo + '\n')
                        infolog.write('\t\t\t Subject: ' + str(subject_ID) + ' - Test: ' + test_dict[col] + ' - Event: ' + event_ID + '\n')
                        
                        # To recover, just mark the value as not present
                        
                        data_array[event_index, subject_index, test_index] = np.nan
                            
                    except:
                        
                        # Something else happened, so fail gracefully...
                        
                        print "Unexpected error:", sys.exc_info()[0]
                        raise
             
    # Deliver success message:
    
    infolog.write('\t Read ' + str(rowcount) + ' entries in database ' + fileinfo + '\n')
    
    return data_array


# Read numerical PPMI data from databases, store it in three-dimensional numpy array
# indexed by subject ID, event ID, test
#
# Parameters: subject_list - list of test subject IDs
#             event_list - list of recognized 'events' in study timeline
#             file_list - list of PPMI data files
#             test_list - list of recognized tests (cleartext descriptors)
#             test_dict - dictionary PPMI test code : cleartext descriptors
#             infolog - file handle (file object open with write access) for logfile output

def get_PPMI_data(subject_list, event_list, file_list, test_list, test_dict, infolog):
    
    # Create storage for the data panel.  By default, we assume that all entries are numerical.
    # Also, mark every entry initially as invalid - we'll divide zero by zero:

    data_array = np.zeros((len(event_list), len(subject_list), len(test_list))) / 0

    # (Note:  This is a workaround for storing data in the pandas Panel structure directly - that is just *way* slow.)
    
    # Loop thru data files, parse for test results:
    
    for datafile in file_list:
        read_PPMI_data(datafile, infolog, data_array, subject_list, event_list, test_list, test_dict)
        
    return data_array

# ********** MAIN SCRIPT

# Run only if called directly:

if __name__ == '__main__':
    
    import pandas as pd
    import numpy as np
    import json as js
    import pickle
    import sys

    # Default settings for JSON control script, subject master record,
    # pickled data object, log file:
 
    ctrlfile = '../PPMI Analysis/selectdata.json'
    subjfile = '../PPMI Data/Subject_Characteristics/Patient_Status.csv'
    objfile  = '../PPMI Analysis/PPMI_data.pkl'
    logfile  = '../PPMI Analysis/PPMI_data_structures.log'    

    # Settings may be overridden by options:
    #
    #   -c = controlfile
    #   -s = subjectfile
    #   -o = objectfile
    #   -l = logfile
    #
    # First, check whether file names are supplied:

    if len(sys.argv) > 1:
        options = sys.argv[1:]

        # Read out options:

        for entry in options:

            if (entry.count('=') == 0):

                # Options must contain '=' for assignments

                print 'ERROR:  Unrecognized argument', entry
                raise SystemExit(0)

            code, value = entry.split('=', 1)
            
            if (len(code) < 2):

                # Unrecognizable option

                print 'ERROR:  Unrecognized argument', entry
                raise SystemExit(0)

            if (code[0] != '-'):

                # Unrecognizable option - must start with hyphen

                print 'ERROR:  Unrecognized argument', entry
                raise SystemExit(0)

            # Keep only first letter of option string, clean out value string:

            code = code[1]
            value = value.strip()

            # Set values for recognized options:

            if (code == 'c'):
                ctrlfile = value

            elif (code == 'l'):
                logfile = value

            elif (code == 'o'):
                objfile = value

            elif (code == 's'):
                subjfile = value

            else:
                # Unrecognized option

                print 'ERROR:  Unrecognized argument', entry
                raise SystemExit(0)             

    # We need to create some master documents:
    #
    # A list of all subject IDs (PATNO)
    # A dictionary of subject ID and condition
    # A list of events along the timeline
    # A list of available tests

    # Start log file ...

    try:
        infolog = open(logfile, 'w')

    except IOError:
        print 'ERROR:  Could not create log file', logfile
        raise IOError

    # First, read out the subject database:

    subject_list, subject_condition = subject_list_conditions(subjfile)
    infolog.write('SUCCESS:  Read out subject and condition master record\n')

    # Create valid event markers:

    event_list = event_list_create()
    infolog.write('SUCCESS:  Created list of events in PPMI timeline\n')

    # Read script for databases to be included:

    file_list, test_list, test_dict = extract_test_information(ctrlfile)
    infolog.write('SUCCESS:  Read PPMI database dictionary\n')

    # Ingest PPMI data:

    PPMI_array = get_PPMI_data(subject_list, event_list, file_list, test_list, test_dict, infolog)
    infolog.write('SUCCESS:  Loaded PPMI databases\n')

    # The work is really now all done ... store away results for later use:
    
    try:
        with open(objfile, 'wb') as output:
            results = (subject_list, subject_condition, event_list, test_list, test_dict, PPMI_array)
            pickle.dump(results, output)

    except IOError:
        print 'ERROR:  Could not create PPMI data object', objfile
        raise IOError

    infolog.write('SUCCESS:  Wrote PPMI data object to file ' + objfile + '\n\n')
    infolog.close()