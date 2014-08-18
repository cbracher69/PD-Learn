PPMI Machine Learning Library
=============================

This is a collection of methods that involve machine learning on PPMI data, and display results in form of PNG graphics files.  They partially build on the graphics methods developed for this project - see *PPMI_Gaussplots.py* in the *Graphics* folder.  (Please note that simple correlation and profile plots of PPMI data can be generated straight from the methods in there.)

## Brief description of the methods in the library

#### Unsupervised Learning:

Currently, there are three methods available:

	center_mass_view(norm_table, data_avg, subj_cond, cohorts, image_type)

This is a *projection method* that reduces multidimensional normalized data to a correlation plot (which is subsequently rendered by the *scatter_gauss* and *scatter_plain* engines in the graphics library *PPMI_Gaussplots.py*).  The idea is based on the fact that PPMI data typically involves three cohorts (healthy (HC), Parkinson's (PD), and atypical Parkinson's (SWEDD) subjects).  The average feature vectors for these three cohorts form a triangle in feature space that defines a plane (which I call the 'center-of-mass' plane), which is used for the projection.  This choice of coordinate axes guarantees the maximum possible *average* separation between cohorts, and may assist in discovering patterns that are specific to the different cohorts.  (In the machine learning literature, this projection is known as 'canonical discriminant analysis' (CDA).)  As usual, the color coding in the map is:

	Healthy control (HC) --- blue
	Parkinson's Disease (PD) --- green
	SWEDD (atypical PD) --- red

*norm_table* is a dataframe containing multi-feature normalized data, *data_avg* is a dataframe containing basic statisics of the data (both are available using methods in the statistics core), *subj_cond* is a pandas Series object that contains cohort information (all data objects are indexed by the subject IDs), and *cohorts* is a list of the cohorts ('HC', 'PD', 'SWEDD') present in the data.  (The method is only available if all three cohorts are represented.)

The variable *image_type* is used to select the graphics method used to draw the plot.  Allowed values are 'Gauss' (draw a correlation plot on a colored canvas using *scatter_gauss*) and 'Scatter' (draw a scatterplot on a white canvas using *scatter_plain*).

The method returns a string containing graphics data in PNG format.  The title of the plot contains the 'capture ratio,' the percentage of the variance in the data contained in the projection (see also the *pca_view* method below).

	pca_view(norm_table, subj_cond, cohorts, image_type)

This is another *projection method* that reduces multidimensional normalized data to a correlation plot (see above).  Unlike the *center-mass_view* method, PCA can be performed even when only a single cohort is present, although there are clearer benefits in the multi-cohort case. The PCA method picks the two dominant orthogonal directions in space according to singular value decomposition (SVD), and projects the data points onto it.  Thereby, it generates a view onto the plane in feature space that minimizes the average square distance of data points to the plane of projection ("explains most of the variance," in statistics lingo).  The fraction of variance in the data "explained" by the two dominant directions is displayed in the title of the plot returned by the method.  The parameters used in calling the method are the same as above.  The image is returned in PNG format as a string.

The third method is a non-linear approach to display clusters of data in a two-dimensional "embedded" space that is then rendered as a scatterplot, with or without a Gaussian color canvas:

	t_sne_view(norm_table, subj_cond, cohorts, image_type)

The method utilizes the scikit-learn *TSNE* (sklearn.manifold.TSNE) implementation of the *stochastic neighbor embedding* algorithm to generate the data for the image, which is then rendered by *scatter_gauss* or *scatter_plain*.  t-SNE uses the (euclidean) distance between two data points in the normalized data set to create clusters of points, an approach that works best for well-separated clusters.  (If the feature space has large dimension (d > 12), PCA is used to project the data onto the 12 "most significant" coordinate axes first.)  In this implementation, the resulting data in the embedded space is first shifted and normalized before display.

Because t-SNE uses random initialization, and the algorithm often converges to a local minimum in its target function, repeated execution of *t_sne_view* on the same data usually results in different outcomes.

The call parameters have the same meaning as in *center_mass_view* and *pca_view*, and the method again returns a PNG image file as a string.

#### Supervised Learning

This section contains one method that currently supports three supervised learning approaches:

	plot_roc_curve(norm_table, subj_cond, cohorts, classifier)

This will show the *receiver operating characteristic* (ROC curve) for every pair of cohorts present in the data, either a single curve (for a pair of cohorts), or a set of three curves (if all three cohorts are present).  The parameters are the same as above, except that the string variable *classifier* selects one of three classifying methods:

	'Random Forest' - Random Forest classifier with 200 trees, considering all features
	'kNN' - k-nearest neighbor clustering algorithm, using 5 neighbors
	'Logistic Regression' - logistic regression algorithm

The method will also return information about the *area under the curve* (AUC) as a measure for classification success, in the form of a legend built into the plot.  This method again returns a string containing an image in PNG format.

#### Future improvements

*	Currently, some parameters in the methods (e.g., classifier parameters, etc.) are hard-coded.  Ideally, these parameters should be able to be set by the calling program.

*	The library should be extended by additional supervised and unsupervised learning algorithms.