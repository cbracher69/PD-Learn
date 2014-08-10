# PPMI-LEARN
# A collection of machine-learning related methods for project PD-LEARN
# Christian Bracher, July 2014

# New (August 9, 2014):
# - Allow image type selection for CM plot (Gauss vs. scatter)
# - Add PCA view (projection on PCA components of leading importance)

from sklearn.cross_validation import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, roc_curve, auc
from sklearn.decomposition import PCA

import numpy as np
import pandas as pd
import StringIO
import matplotlib.pyplot as plt

import PPMI_Gaussplots as scg

# Center-of-mass view:
#
# Plot a projection of multi-dimensional data onto the plane of maximum separation
# of cohort averages
#
# Idea:  Use normalized data from features to find average feature vectors for each cohort
#        Since there are three cohorts, these vectors span a plane in feature space
#        This 'center-of-mass' plane is special in the sense that it yields the biggest
#        distance between average feature vectors in any two-dimensional projection of
#        feature space, so it *may* show differences between cohorts most clearly.
#
# The graphical rendering is executed by the scatter_gauss and scatter_plain methods.
#
# Parameters:
# norm_table - pandas DataFrame containing a normalized data set
# data_avg - pandas DataFrame containing summary statistics of the same set
# subj_cond - pandas Series: cohort vs. subject ID
# cohorts - list of subject cohorts present in data
# image_type - rendering mechanism.  Should be either 'Gauss' or 'Scatter'
#
# Returns: 
# png_data - string containing the rendered image in PNG format
# 

def center_mass_view(norm_table, data_avg, subj_cond, cohorts, image_type):

    # Check that indeed all three cohorts are present

    if (len(cohorts) < 3):
        print 'WARNING:  Center of mass view requires all three cohorts.'
        return None

    # Create cohort average vectors in normalized coordinates

    norm_avg_HC = (data_avg.ix['HC mean'] - data_avg.ix['global mean']) / data_avg.ix['std dev']
    norm_avg_PD = (data_avg.ix['PD mean'] - data_avg.ix['global mean']) / data_avg.ix['std dev']
    norm_avg_SW = (data_avg.ix['SWEDD mean'] - data_avg.ix['global mean']) / data_avg.ix['std dev']

    # Normalize the 'healthy' cohort direction to the unit vector e1 in feature space:

    square_length = norm_avg_HC.dot(norm_avg_HC)
    unit_1 = norm_avg_HC / np.sqrt(square_length)

    # Find the component of the 'PD' cohort direction perpendicular to e1:
    # (mathematically, a Schmidt-Gram procedure)

    dot_product = norm_avg_PD.dot(unit_1)
    ortho_PD = norm_avg_PD - dot_product * unit_1

    # Normalize this vector, too, into unit vector e2:

    square_length = ortho_PD.dot(ortho_PD)
    unit_2 = ortho_PD / np.sqrt(square_length)

    # Project normalized feature vectors for all subjects onto the center-of-mass plane

    CM_coord_1 = pd.Series(norm_table.dot(unit_1), name = 'Center of Mass')
    CM_coord_2 = pd.Series(norm_table.dot(unit_2), name = 'View')

    # Send out to graphics rendering engine:

    if (image_type == 'Gauss'):
        return scg.scatter_gauss(CM_coord_1, CM_coord_2, subj_cond)
    elif (image_type == 'Scatter'):
        return scg.scatter_plain(CM_coord_1, CM_coord_2, subj_cond)

# PCA view (projection on principal components of leading importance)
#
# Idea:  Use normalized data from features to find the two directions that explain
#        most of the variance of the data, and use the plane they span for
#        projection.  This yields a projection that is the overall "closest fit" to
#        the data in the sense that the sum of the squared distances of all data points
#        to the plane of projection is minimized.
#
# The graphical rendering is executed by the scatter_gauss and scatter_plain methods.
#
# Parameters:
# norm_table - pandas DataFrame containing a normalized data set
# subj_cond - pandas Series: cohort vs. subject ID
# cohorts - list of subject cohorts present in data
# image_type - rendering mechanism.  Should be either 'Gauss' or 'Scatter'
#
# Returns: 
# png_data - string containing the rendered image in PNG format
# 

def pca_view(norm_table, subj_cond, cohorts, image_type):

    # SVG-PCA analysis: Plot projections onto plane spanned by the two most 
    # significant principal axes (PCA components)

    # Keep only two principal components
    pca = PCA(n_components=2)

    # Use normalized data:    
    norm_data = norm_table.as_matrix()

    # Find principal axes:
    pca.fit(norm_data)

    # Project on principal components:
    pca_data = pca.transform(norm_data)

    # 'Captured' variance in percent:
    pca_var  = 100.0 * pca.explained_variance_ratio_.sum()
    pca_note = '(Capture ratio: %.1f%%)' % pca_var

    # Prepare for view:
    cols = ['PCA View', pca_note]
    pca_table = pd.DataFrame(pca_data, index = norm_table.index, columns = cols)
    
    # Send out to graphics rendering engine:

    if (image_type == 'Gauss'):
        return scg.scatter_gauss(pca_table[cols[0]], pca_table[cols[1]], subj_cond)
    elif (image_type == 'Scatter'):
        return scg.scatter_plain(pca_table[cols[0]], pca_table[cols[1]], subj_cond)


# Receiver-Operating Characteristic
# Find the ROC curve for a given selection of data,
# for possible combination of cohorts present
#
# Parameters:
# norm_table - pandas Dataframe object containing normalized data sets
# subj_cond - pandas Series representing cohort (data) vs. subject ID (index)
# cohorts - list of PPMI cohorts present in data set
# classifier - string selecting a supervised learning algorithm
#
# For now, allow three different classifier settings:
# 
#   'Random Forest' - Random Forest classifier with 200 trees, considering all features
#   'kNN' - k-nearest neighbor clustering algorithm with 5 neighbors
#   'Logistic Regression' - logistic regression algorithm

def plot_roc_curve(norm_table, subj_cond, cohorts, classifier):
    
    # We have up to three cohorts in a given data set.
    # ROC analysis requires to compare only pairs of cohorts, so let's find these
    # The list of cohorts is in 'cohorts', so create a set of unique pair sets:

    cohort_pairs = set()

    for c1 in cohorts:
        for c2 in cohorts:
            if (c1 != c2):
                cohort_pairs.update([frozenset([c1,c2])])

    # Check that at least one pair is present:

    if (len(cohort_pairs) < 1):
        print 'WARNING:  ROC analysis requires at least two cohorts.'
        #(return here)

    # Initialize figure

    fig = plt.figure()
    plt.xlim([-0.005, 1.005])
    plt.ylim([-0.005, 1.005])

    # Run the supervised learning test for all pairs...

    for pair in cohort_pairs:

        # Filter out data set - create filter accepting either member of pair

        pl = list(pair)
        pair_filter = ((subj_cond == pl[0]) | (subj_cond == pl[1]))

        # Apply filter to features

        feature_filtered = norm_table[pair_filter].as_matrix()

        # Apply filter to labels
        # Turn condition codes to numerical values of zero 
        # (leading member of pair) and one (trailing member):

        cond_filtered   = subj_cond[pair_filter]
        code_filtered   = cond_filtered.apply(lambda condition : pl.index(condition))
        labels_filtered = code_filtered.tolist()

        # Split list into training and test parts

        X_train, X_test, y_train, y_test = train_test_split(feature_filtered, labels_filtered)

        # Now, select classifier algorithm:
        
        if (classifier == 'Random Forest'):
            clf = RandomForestClassifier(n_estimators = 200, max_features = None)
            
        elif (classifier == 'kNN'):
            clf = KNeighborsClassifier(n_neighbors = 5)
            
        elif (classifier == 'Logistic Regression'):
            clf = LogisticRegression()
            
        else:
            print 'WARNING:  Unsupported classifier', classifier
            return None
        
        # Fit to training data
        
        clf.fit(X_train, y_train)
        
        # Predict PPMI cohort probabilities for test set of subjects
        
        prob = clf.predict_proba(X_test)

        # Create ROC curve, determine area under curve (AUC)
        
        fpr, tpr, thresholds = roc_curve(y_test, prob[:,1])
        roc_auc = auc(fpr, tpr)

        # Plot curve
        
        legend_text = 'AUC ' + pl[0] + ' vs. ' + pl[1] + ': %0.2f' % roc_auc
        plt.plot(fpr, tpr, lw = 2, label=legend_text, alpha = 0.5)

    # Plot diagonal (random guesses)
    
    plt.plot([0, 1], [0, 1], 'k--', lw = 1.5)

    # Figure labels
    
    plt.xlabel('False Positive Rate', fontsize = 14)
    plt.ylabel('True Positive Rate', fontsize = 14)
    plt.title('ROC Curve (' + classifier + ')', fontsize = 18)
    plt.legend(loc="lower right")

    # Now, save the graph as a .PNG image.
    # Don't write it to disk - instead, return it as a string:
    
    imgdata = StringIO.StringIO()
    fig.savefig(imgdata, format='png')
    plt.close()
    
    # Get the contents of the image file as a string:
    
    imgdata.seek(0)
    png_file = imgdata.buf
    
    return png_file