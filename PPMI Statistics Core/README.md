PPMI Statistics Core
====================

This folder contains the library *PPMI_Stats_Core* which is responsible for data administration, communication with the frontend/user interface, simple statistics, and deploying machine learning algorithms.

## Overview

As the core module, the statistics core interfaces both the 'backend' which conditions the PPMI study data, and the 'frontend' that interacts with the user.  At start-up, the core module reads the data object provided by the backend, and creates a three-dimensional internal representation (implemented as a pandas Panel object):

	(Startup)  Read pickled PPMI data object -> Data organized by time (event ID), subject ID, medical procedure ('test')

Whenever the 'frontend' is initialized or reset, it requests a list of available data organized by event ID and medical procedure:

	(Frontend)  Request for available data
	(Core)  Transmit array of (event, test) combinations

After the user chooses certain datasets, the core is responsible for collecting a list of all study subjects for which the desired data is available.  (In the PPMI study, not all tests are performed on all subjects.)  It creates some simple statistics (counting subjects by cohort, finding averages and standard deviations, normalizing the data), and assembles a list of statistics/display/machine learning procedures that are available for the data.  This list is sent back to the frontend:

	(Frontend)  Selection of (event, test) pairs
	(Core)  Data collection & examination, transmit list of suitable procedures

In the current version, these procedures include one-dimensional probability distributions (profiles) if a single (event, test) set is chosen, correlations between pairs of (event, test) data, and projection and machine learning algorithms for extended feature selections.

Finally, the user selects one of these procedures.  Upon request, the statistics core performs the calculation, renders the result in graphical form (in the course, differentiating the study cohorts - healthy (HC), Parkinson's (PD), and atypical Parkinson's (SWEDD)), and transmits an image file (in .png format) back to the frontend:

	(Frontend)  Selection of statistics/machine learning procedure
	(Core)  Perform analysis, render result as plot, transmit image file for display

From there, the user can return to select different (event, test) pairs, and perform further analysis.

####  Transfer formats

The core module generally relies on JSON control strings to communicate with the frontend.  They consist of nested dictionaries and lists, with the outermost key indicating the purpose of the communication:

	{"PPMI All Data" : 
		{ event : [list of tests], 
		  event : [list of tests], 
		  ... }
	}

Transmit list of (event, test) pairs to frontend.

	{"employdata" : 
		{"cohort" : [list of cohorts], 
		 group of tests : 
		 	{"events" : [list of events], "tests" : [list of tests]},
		 group of tests : 
		 	{"events" : [list of events], "tests" : [list of tests]},
		 ... }
	}

List of (test, event) pairs selected by user, received from frontend.

	{"PPMI Tests" : 
		{"Profile" : [list of options],
		 "Correlation" : [list of options],
		 "Projection" : [list of options],
		 "ROC Curve" : [list of options]
		}
	}

Methods for data analysis, forwarded to frontend.

	{"PPMI Image" : {"Type" : type, "Option" : option}}

Analysis selected by user, received from frontend.  This must match one of the methods/options suggested by the statistics core.

#### List of methods available

This is a summary of the methods collected in the core library.

	subject_list, subject_condition, event_list, test_list, test_dict, data_panel = unpickle_PPMI_data(filename)

Load data object provided by backend, create list of subject IDs, event IDs, tests, assign cohorts to subject IDs.

	available_data = list_available_data(event_list, test_list, data_panel)

Create JSON control string containing (event, test) pairs, for frontend.

	filter_dict = create_cohort_filters(subject_list, subject_condition)

Define cohort 'masks'.  Used internally.

	cohorts, selections = extract_information(fileinfo)

Read list of requested study data from JSON control string.

	subj_cond, data_table = build_data_table(data_panel, cohorts, selections, subject_list, subject_condition)

Create table of data according to user requests.

	data_counts, cohorts = data_count(subj_cond)

Count subjects by cohorts in data table, adjust list of cohorts.

	data_avg = data_stats(data_table, subj_cond, cohorts)

Perform simple statistics (average, standard deviation) on data table.

	norm_table = normalize_table(data_table, data_avg)

Create normalized data table, with zero mean and unit standard deviation.

	available_tests = list_available_plots(norm_table, cohorts)

Construct JSON control string with available statistics/ML algorithms.

	png_image = create_plot(image_request, norm_table, data_avg, subj_cond, cohorts, data_counts)

Read requested plot from JSON control string, render it as an image, and return it as a string in .png image format.

#### Future improvements

Add additional algorithms for machine learning analysis, such as clustering.  Implement the frontend application as a webpage or GUI.  Extend range of PPMI study data to include categorical/numerical results.
