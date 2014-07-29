PPMI Machine Learning Library
=============================

This is a collection of methods that involve machine learning on PPMI data, and display results in form of PNG graphics files.  They partially build on the graphics methods developed for this project - see *PPMI_Gaussplots.py* in the *Graphics* folder.  (Please note that simple correlation and profile plots of PPMI data can be generated straight from the methods in there.)

#### Brief description of the methods in the library

Currently, there are two methods available:

	center_mass_view(norm_table, data_avg, subj_cond, cohorts)

This is a *projection method* that reduces multidimensional normalized data to a correlation plot (which is subsequently rendered by the *scatter_gauss* engine in the graphics library *PPMI_Gaussplots.py*).  The idea is based on the fact that PPMI data typically involves three cohorts (healthy (HC), Parkinson's (PD), and atypical Parkinson's (SWEDD) subjects).  The average feature vectors for these three cohorts form a triangle in feature space that defines a plane (which I call the 'center-of-mass' plane), which is used for the projection.  This choice of coordinate axes guarantees the maximum possible *average* separation between cohorts, and may assist in discovering patterns that are specific to the different cohorts.  As usual, the color coding in the map is:

	Healthy control (HC) --- blue
	Parkinson's Disease (PD) --- green
	SWEDD (atypical PD) --- red

*norm_table* is a dataframe containing multi-feature normalized data, *data_avg* is a dataframe containing basic statisics of the data (both are available using methods in the statistics core), *subj_cond* is a pandas Series object that contains cohort information (all data objects are indexed by the subject IDs), and *cohorts* is a list of the cohorts ('HC', 'PD', 'SWEDD') present in the data.  (The method is only available if all three cohorts are represented.)

The method returns a string containing graphics data in PNG format.

The second method supports supervised learning:

	plot_roc_curve(norm_table, subj_cond, cohorts, classifier)

This will show the *receiver operating characteristic* (ROC curve) for every pair of cohorts present in the data, either a single curve (for a pair of cohorts), or a set of three curves (if all three cohorts are present).  The parameters are the same as above, except that the string variable *classifier* selects one of three classifying methods:

	'Random Forest' - Random Forest classifier with 200 trees, considering all features
	'kNN' - k-nearest neighbor clustering algorithm, using 5 neighbors
	'Logistic Regression' - logistic regression algorithm

The method will also return information about the *area under the curve* as a measure for classification success, in the form of a legend built into the plot.  This method again returns a string containing an image in PNG format.

#### Future improvements

*	Currently, some parameters in the methods (e.g., classifier parameters, etc.) are hard-coded.  Ideally, these parameters should be able to be set by the calling program.

*	The library should be extended by unsupervised learning algorithms (clustering, t-SNE, principal component analysis).