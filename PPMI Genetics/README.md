PPMI Genetics
=============

The PPMI study provides a large array of genetic allele data on about 1,000 subjects in two sets of data files.  The data is encoded in [PLINK format](http://pngu.mgh.harvard.edu/~purcell/plink/), a standard used in the field.  PLINK supports various conventions, but the PPMI data is distributed over a set of three files:

*   *plink.bed*      
	( binary file, holding the data = genotype information )
*   *plink.fam*      
	( subject information, subject status ) 
*   *plink.bim*
	( list of mutations tested for)

The .fam files refer to the subject IDs used throughout the study, but have not been crosslinked with the patient status (this information is recorded as 'missing' in the files).  They also contain information from subjects that have subsequently withdrawn from the study.

The methods contained in this directory rewrite the .fam files, linking the subject IDs with their disease status, and label patients no longer in the study as missing.  After this modification, they are suitable for simple genome statistics using the PLINK utility.

### How to use the Python utility

To link the PPMI genetics data to subject ID data, run 

	PPMI_Genetics_Label_Condition.py [script-file [subject-info-file]]

from the command line.  [script-file] is an optional parameter that points to the script controlling execution of the utility.  If [script-file] is not provided, the utility assumes that the script is stored in a file 'prepare_plink.json' in the directory '../PPMI Genetics'.

[subject-info-file] is a second optional command line parameter that indicates the location of the PPMI master subject file.  By default, the path and filename are set to: '../PPMI Data/Subject_Characteristics/Patient_Status.csv'

#### Format of the script file

The script file must be in JSON format, of the form:

	{"plink" :
		{"cohort"   : ["HC" and/or "PD" and/or "SWEDD"],
	 	 "filename" : "(PLINK file).fam"}}

"plink" identifies the control file as a genetics file modifier.  "filename" should indicate the path/name of the PLINK file to be analyzed, including the '.fam' suffix.  The "cohort" entry is a list containing any combination of the three PPMI cohorts 'HC' (healthy control), 'PD' (Parkinson's Disease), and 'SWEDD' (Parkinson's patient with normal DaTSCAN image).  The groups indicated in "cohorts" are assigned to be 'affected' by disease for the PLINK analysis.

#### Brief description of methods in the utility

	subject_list_conditions(subject-info-file)

*subject-info-file* is an optional parameter (the default is '../PPMI Data/Subject_Characteristics/Patient_Status.csv') indicating the location of the PPMI master datafile linking subject ID with subject PD status.  The method tries to read the master file, and returns a subject:condition dictionary.

	read_plink_instructions(script-file)

Reads out the processing instructions, by default stored in '../PPMI Genetics/prepare_plink.json'.  It returns a tupel made from a list *cohorts* (the cohorts to be marked as affected), and a string 'filename', the path and name of the .fam PLINK file to be modified.

	plink_fam_copy(datafile)

This tries to create a copy 'datafile.fam.old' of the original '.fam' file in the same directory.  No return value.

	plink_fam_write_status(cohorts, datafile, subject_condition)

This rewrites the PLINK .fam file in *datafile* with the actual subject information, according to their affected status controlled by *cohorts*.  The subject status is extracted from the subject-condition dictionary *subject_condition*.