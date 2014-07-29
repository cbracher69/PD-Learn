### FORMAT FOR THE JSON INFORMATION FILE USED TO SELECT PPMI DATA

The script 'PPMI_Data_Structures.py' is used to selectively read PPMI study data into a three-dimensional numerical data array that is indexed by 'event' (timeline), subject ID, and a list of tests.  The information where to find what data is conveyed to 'PMI Data Structures.py' via an object in JSON format, 'selectdata.json' (default file name).

'selectdata.json' has the following format:

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

Description of the fields:

	database identifier #1, #2, etc. 
	
User-defined labels for the databases - they can take any value, but must be unique;

	path_filename
	
The path & filename to the PPMI data file;

	[descriptor #1, descriptor #2, ...] 
	
Denotes a list of unique descriptors that give a cleartext description of tests;

	{PPMI Test Code #1 : descriptor, PPMI Test Code #2 : descriptor, ...} 
	
This field contains a dictionary that links each official PPMI test code to one of the descriptors.

*Note*:  If several PPMI test codes point to the same descriptor, the test scores will be *aggregated as a sum*.

---

*Example*:  Read four columns of results from the DaTSCAN imaging procedure, plus a single aggregate score of four subscores in UPSIT olfactory testing:


	{"selectdata" :
		{"DaTSCAN" :
			{"filename" : "Desktop/PPMI Data/DaTSCAN/DaTscan_Striatal_Binding_Ratio_Results.csv",
			 "testlist" : ["DaTSCAN Right Caudate", "DaTSCAN Left Caudate", "DaTSCAN Right Putamen", "DaTSCAN Left Putamen"],
			 "testdict" : {"CAUDATE_R":"DaTSCAN Right Caudate", "CAUDATE_L":"DaTSCAN Left Caudate", 
				  "PUTAMEN_R":"DaTSCAN Right Putamen", "PUTAMEN_L":"DaTSCAN Left Putamen"}},
		"Olfactory" :
			{"filename" : "Desktop/PPMI Data/Non-motor_Assessments/Univ._of_Pennsylvania_Smell_ID_Test.csv",
			 "testlist" : ["UPSIT Olfactory Score"],
			 "testdict" : {"UPSITBK1":"UPSIT Olfactory Score", "UPSITBK2":"UPSIT Olfactory Score",
				  "UPSITBK3":"UPSIT Olfactory Score", "UPSITBK4":"UPSIT Olfactory Score"}}
		}
	}
