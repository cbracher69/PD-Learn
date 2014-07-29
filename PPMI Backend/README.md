PPMI Backend
============

This folder contains all methods and scripts to generate an integrated data object from the raw PPMI databases.

## Usage of the Python scripts

To prepare the data, two scripts should be run in sequence - first prepare the biomarkers database, then readout the databases and create the data object.

#### Biomarkers script

The PPMI biomarkers database deviates in its structure from the remaining data files, consists of several parts, and is also marred by multiple entries for the same procedures (some samples had to be re-tested).  To prepare the biomarkers database for consumption by the data structures utility, run a script that removes these issues and creates a conforming database:

	PPMI_Prepare_Biomarkers [control-script]

The *control-script* is an optional argument that points to a JSON file containing the biomarker data files, and the desired output file for the cleaned database, in the form:

	{"biomarkers" :	
		{"raw" 		  : [list of biomarker input files],
		 "outputfile" : path & filename for created database}}

If no argument is given, the script uses the default values:

	raw file #1 : '../PPMI Data/Biospecimen_Analysis/Biospecimen_Analysis_Results.csv'
	raw file #2 : '../PPMI Data/Biospecimen_Analysis/Pilot_Biospecimen_Analysis_Results_Projects_101_and_103.csv'
	outputfile  : '../PPMI Data/Biospecimen_Analysis/biomarkers_clean.csv'

#### Data structures script

The data structures utility reads out PPMI databases according to a control script in JSON format, creates a three-dimensional data object (a numpy array that is indexed with respect to 'events' - the timeline of the study, the study subject ID, and the type of test performed) that forms the substrate for the statistics engine, and writes it in pickled form to disk.  The calling format is:

	PPMI_Data_Structures [-c=control_file] [-l=log_file] [-o=output_file] [-s=subject_master_record]

All four command line entries are optional; if missing, they will be replaced by their default values:

	control_file = '../PPMI Analysis/selectdata.json'
    subject_master_record = '../PPMI Data/Subject_Characteristics/Patient_Status.csv'
    output_file = '../PPMI Analysis/PPMI_data.pkl'
    log_file = '../PPMI Analysis/PPMI_data_structures.log'

*subject-master-record* is a PPMI database that contains subject IDs, their cohort (healthy, or 'HC'; Parkinson's, or 'PD'; Parkinson's with normal SPECT scan, or 'SWEDD'), and their enrollment status in the study.  The *log-file* yields details about the conversion process.  *output-file* provides the filename under which the pickled data object is written to disk.  Finally, *control-file*, a JSON object, provides the names of the PPMI databases, and fine-grained information about which tests to include.  Its general format is:

	{"selectdata" :
		{database identifier #1:
			{"filename" : path_filename,
			 "testlist" : [descriptor #1, descriptor #2, ...],
			 "testdict" : {PPMI Test Code #1 : descriptor, PPMI Test Code #2 : descriptor, ...}},
		database identifier #2:
			{"filename" : path_filename,
			 "testlist" : [descriptor #1, descriptor #2, ...],
			 "testdict" : {PPMI Test Code #1 : descriptor, PPMI Test Code #2 : descriptor, ...}},
		...}
		}
	}

*selectdata* is a fixed identifier for the control file, *database identifier* are user-selected descriptions of the entry, *path_filename* provides the location of a PPMI database file, *testlist* is a set of user-defined descriptors for the tests included, and *testdict* is a dictionary that links the 'official' PPMI test codes to the corresponding user-defined descriptors.  A separate documentation file ('Description of input selection file') contains detailed instructions about its format and proper use.

#### Future improvements

At this stage, the backend can only import tests with numerical output into the data object.  Although this captures a large number of PPMI scores, it would be desirable to add non-numerical data to the set, in particular genetics and raw imaging data.