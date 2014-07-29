PPMI Graphics Library
=====================

For the graphical presentation of PPMI data, I have developed two new designs that (I hope) aid in the interpretation of the data.  Conceptually, they are based on the idea that one can associate each of the three cohorts in the study with one of the primary colors:

	Healthy control (HC) --- blue
	Parkinson's Disease (PD) --- green
	SWEDD (atypical PD) --- red

The designs also try to emphasize the fact that the data often come with a significant experimental uncertainty.  Technically, the images are created using elements of the Python pyplot engine.  I have added some simple images, based on actual PPMI data, for illustration.

#### Brief description of the methods in the library

The two designs are made available in the library *PPMI_Gaussplots.py*:

	profile_gauss(x_series, subj_cond, cohorts, data_counts)

This method draws a combination of a scatterplot of the data with cohort averages (stars, bottom) and a smoothened cumulative probability distribution (top) for a normalized data set, i.e., for a data set that is centered around zero and has unit sample standard deviation.  (The statistics core has a method *normalize_data* that automatically transforms a data set this way.)  The list *cohorts* contains the subjects cohorts to be displayed (any combination of 'HC', 'PD', 'SWEDD').  The series *data_counts* contains the total counts of HC, PD, and SWEDD subjects, and is available using the *count_data* method in the statistics core.

*x_series* is a pandas Series object that contains the data to be displayed, with the subject IDs as series index. *subj_cond* is also a pandas Series, with the same subject ID index, but contains the subject cohort ('HC', 'PD', 'SWEDD') as data instead.

*profile_gauss* returns a string object that contains the image in .png format.

	scatter_gauss(x_series, y_series, subj_cond)

This method illustrates the correlation between two normalized data sets.  It draws a scatterplot together with the cohort averages (star symbols) on top of a smooth background intended to depict that all data points have a random statistical error; the resulting coloring should also serve as a visual aid to identify clusters of similar data points.

*x_series* and *y_series* are again pandas Series objects that contains the data to be displayed in correlation, and *subj_cond* is a pandas Series that indicates the cohort assigned to each data point.  All three series share the same subject ID index.

*scatter_gauss* likewise returns a string object that contains the image in .png format.

#### Mathematical background

Both methods use the normal distribution (Gaussian) to achieve data smoothing.  In *profile_gauss*, each data point is assigned a cumulative normal distribution (or error function) of constant width; the displayed cumulative distribution function is the sum of these error functions.  The curves represent the likelihood that a data point of a given cohort has a value smaller than the argument, while allowing for a normally distributed statistical error.

In *scatter_gauss*, each data point is assigned a background 'halo' of Gaussian profile indicating the statistical uncertainty of a measurement.  It would be expected that the background image closely resembles the joint probability distribution function if the number of measurements is large.

#### Future improvements

Currently, many parameters in the methods (e.g., window displayed, width of Gaussian distribution, etc.) are hard-coded at values that yield pleasing displays when applied to PPMI data.  Ideally, these parameters should be able to be set by the calling program.