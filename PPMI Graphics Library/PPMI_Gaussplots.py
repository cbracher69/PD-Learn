# Fancy Gaussian display styles for 1D and 2D maps.

# Update (August 9, 2014):
# - Add choice of cumulative or probability density distribution
# - Add white background scatterplot method

# Provide a colored scatterplot that uses Gaussian profiles 
# to show distribution besides markers.
# Indicate averages for different cohorts if applicable

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import StringIO
from scipy.stats import norm

# A Gaussian display style for 2D correlations.

# Plot two data series against each other, color them according to subject cohort
# Provide a background image that shows a probability density distribution (of sorts)
# with RGB color values according to relative abundance of cohort.
# Color coding: Blue - HC, green - PD, red - SWEDD
#
# Input parameters:
# Pairs of values of data points in form of pandas series objects - x_series, y_series
# Corresponding series object (subject ccondition/cohort) - subj_cond
#
# Returns:
# String containing bitmap image in .PNG format - png_file

def scatter_gauss(x_series, y_series, subj_cond):
    
    # This section ideally should be controlled by function parameter keys.
    # For now, these were pretty good values for the PPMI study: 

    # Some parameters

    Gauss_width = 0.2  # Width of the Gaussian marker
    Gauss_depth = 0.1  # Maximum color saturation

    # Displayed Canvas

    x_min = -2.5
    x_max = +2.5

    y_min = -2.5
    y_max = +2.5
    
    # Resolution of background image:

    image_resolution_x = 0.025
    image_resolution_y = 0.025
    
    # Number of data points to be displayed
    
    scatter_size = len(x_series)
    
    # Color information - dictionary of rgb values for each color code (saturated)
    # Here only defined for types 0, 1, 2 (HC, PD, SWEDD)
    # (One could extend this for more values & colors, of course.)

    rgb = {'HC':[0.0,0.0,1.0], 'PD':[0.0,1.0,0.0], 'SWEDD':[1.0,0.0,0.0]}
    
    # Create Numerical Grid for Gaussians

    x = np.arange(x_min, x_max, image_resolution_x)
    y = np.arange(y_min, y_max, image_resolution_y)
    X, Y = np.meshgrid(x, y)
    
    # Create grids for color functions.
    # (We'll lave an empty canvas black.)
    
    ImageR = np.zeros((len(x),len(y)))
    ImageG = np.zeros((len(x),len(y)))
    ImageB = np.zeros((len(x),len(y)))
    
    ImageRGB = np.zeros((len(x), len(y), 3))
    
    # Add Gaussian 'penumbra' for each data point
    # (color depends on condition listed)
    
    for subj in subj_cond.index:
        delta_X = X - x_series[subj]
        delta_Y = Y - y_series[subj]
        
        rel_dist = (delta_X * delta_X + delta_Y * delta_Y) / (Gauss_width * Gauss_width)
        
        # An interpolation function would speed up calculation here:

        GaussValues = Gauss_depth * np.exp(-rel_dist)
        
        # Provide color by superposition
        
        ImageR = ImageR + GaussValues * rgb[subj_cond[subj]][0]
        ImageG = ImageG + GaussValues * rgb[subj_cond[subj]][1]
        ImageB = ImageB + GaussValues * rgb[subj_cond[subj]][2]
      
    # Check and correct for saturated colors - RGB values should not exceed unity
        
    ImageR = ImageR / (1.0 + ImageR)
    ImageG = ImageG / (1.0 + ImageG)
    ImageB = ImageB / (1.0 + ImageB)
    
    # Combine into RGB color function
    
    ImageRGB[:,:,0] = ImageR
    ImageRGB[:,:,1] = ImageG
    ImageRGB[:,:,2] = ImageB
    
    # Set up figure parameters:
    fig = plt.figure(num=None, figsize=(8, 8), dpi=150, facecolor='w', edgecolor='k')

    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)

    plt.title(x_series.name + ' - ' + y_series.name)

    # Create figure background - Gaussian distributions
    
    ax = plt.subplot()
    ax.imshow(ImageRGB, interpolation='bilinear', origin='lower', extent=[x_min,x_max,y_min,y_max])
    fig.add_subplot(ax)

    # Create pinpoints for individual measurements by condition:
    # Healthy controls:

    ax = plt.subplot()
    
    cond_filter = (subj_cond == 'HC')
    
    x_select = x_series[cond_filter]
    y_select = y_series[cond_filter]
    
    if (len(x_select) > 0):
        
        x_avg = x_select.mean()
        y_avg = y_select.mean()
        
        # Plot little blue markers for data points, big stars for cohort average

        ax.scatter(x_select, y_select, s = 10, c = 'b', alpha = .33)
        ax.scatter(x_avg, y_avg, s = 150 , c = 'b', marker = '*', label = 'HC')
    
    # Same now for Parkinson's cohort:

    cond_filter = (subj_cond == 'PD')
    
    x_select = x_series[(cond_filter)]
    y_select = y_series[(cond_filter)]
    
    if (len(x_select) > 0):
        
        x_avg = x_select.mean()
        y_avg = y_select.mean()

        # Plot little green markers for data points, big stars for cohort average
       
        ax.scatter(x_select.tolist(), y_select.tolist(), s = 10, c = 'g', alpha = .33)
        ax.scatter(x_avg, y_avg, s = 150 , c = 'g', marker = '*', label = 'PD')
     
    # And finally, the SWEDD cohort:

    cond_filter = (subj_cond == 'SWEDD')
    
    x_select = x_series[(cond_filter)]
    y_select = y_series[(cond_filter)]
    
    if (len(x_select) > 0):
        
        x_avg = x_select.mean()
        y_avg = y_select.mean()

        # Plot little red markers for data points, big stars for cohort average
        
        ax.scatter(x_select, y_select, s = 10, c = 'r', alpha = .33)
        ax.scatter(x_avg, y_avg, s = 150 , c = 'r', marker = '*', label = 'SWEDD')    

    ax.legend(loc = 'upper left', scatterpoints = 1)
    fig.add_subplot(ax)

    # Now, save the graph as a .PNG image.
    # Don't write it to disk - instead, return it as a string:
    
    imgdata = StringIO.StringIO()
    fig.savefig(imgdata, dpi = 150, format='png')
    plt.close()
    
    # Get the contents of the image file as a string:
    
    imgdata.seek(0)
    png_file = imgdata.buf
    
    return png_file

# The same as the Gaussian scatter plot, just without the fancy background:

def scatter_plain(x_series, y_series, subj_cond):
    
    # This section ideally should be controlled by function parameter keys.
    # For now, these were pretty good values for the PPMI study: 

    # Displayed Canvas

    x_min = -2.5
    x_max = +2.5

    y_min = -2.5
    y_max = +2.5
    
    # Number of data points to be displayed
    
    scatter_size = len(x_series)
    
    # Color information - dictionary of rgb values for each color code (saturated)
    # Here only defined for types 0, 1, 2 (HC, PD, SWEDD)
    # (One could extend this for more values & colors, of course.)

    rgb = {'HC':[0.0,0.0,1.0], 'PD':[0.0,1.0,0.0], 'SWEDD':[1.0,0.0,0.0]}
       
    # Set up figure parameters:
    fig = plt.figure(num=None, figsize=(8, 8), dpi=150, facecolor='w', edgecolor='k')

    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)

    plt.title(x_series.name + ' - ' + y_series.name)

    # Create pinpoints for individual measurements by condition:
    # Healthy controls:

    ax = plt.subplot()
    
    cond_filter = (subj_cond == 'HC')
    
    x_select = x_series[cond_filter]
    y_select = y_series[cond_filter]
    
    if (len(x_select) > 0):
        
        x_avg = x_select.mean()
        y_avg = y_select.mean()
        
        # Plot little blue markers for data points, big stars for cohort average

        ax.scatter(x_select, y_select, s = 20, c = 'b', alpha = .33)
        ax.scatter(x_avg, y_avg, s = 175 , c = 'b', marker = '*', label = 'HC')
    
    # Same now for Parkinson's cohort:

    cond_filter = (subj_cond == 'PD')
    
    x_select = x_series[(cond_filter)]
    y_select = y_series[(cond_filter)]
    
    if (len(x_select) > 0):
        
        x_avg = x_select.mean()
        y_avg = y_select.mean()

        # Plot little green markers for data points, big stars for cohort average
       
        ax.scatter(x_select.tolist(), y_select.tolist(), s = 20, c = 'g', alpha = .33)
        ax.scatter(x_avg, y_avg, s = 175, c = 'g', marker = '*', label = 'PD')
     
    # And finally, the SWEDD cohort:

    cond_filter = (subj_cond == 'SWEDD')
    
    x_select = x_series[(cond_filter)]
    y_select = y_series[(cond_filter)]
    
    if (len(x_select) > 0):
        
        x_avg = x_select.mean()
        y_avg = y_select.mean()

        # Plot little red markers for data points, big stars for cohort average
        
        ax.scatter(x_select, y_select, s = 20, c = 'r', alpha = .33)
        ax.scatter(x_avg, y_avg, s = 175, c = 'r', marker = '*', label = 'SWEDD')    

    ax.legend(loc = 'upper left', scatterpoints = 1)
    fig.add_subplot(ax)

    # Now, save the graph as a .PNG image.
    # Don't write it to disk - instead, return it as a string:
    
    imgdata = StringIO.StringIO()
    fig.savefig(imgdata, dpi = 150, format='png')
    plt.close()
    
    # Get the contents of the image file as a string:
    
    imgdata.seek(0)
    png_file = imgdata.buf
    
    return png_file

# A Gaussian display style for 1D profiles of PPMI data.

# Show a smoothened cumulative distribution for each cohort present,
# assuming that statistical error is normally distributed.
# In addition, display individual data points, centroids of the distribution
# in a subplot.
# Image has standard PPMI color coding (blue: HC, green: PD, red: SWEDD)

# Input parameters:
# Data points for a test in form of a pandas series object - x_series
# Corresponding series object (subject condition/cohort) - subj_cond
# A list of all subject cohorts present - cohorts
# A pandas Series object containing the number of subjects in each cohort - data_counts
# A switch between CDF and PDF (by default, CDF is shown)
#
# Returns:
# String containing bitmap image in .PNG format - png_file
#
# Note: This depends on the normal distribution provided by scipy.stats.norm

def profile_gauss(x_series, subj_cond, cohorts, data_counts, cumulative = True):
    
    # This section ideally should be controlled by function parameter keys.
    # For now, these were pretty good values for the PPMI study: 

    # Smoothening parameter (ideally, determined in experiment)

    Gauss_width = 0.2  # Width of the Gaussian distribution
    
    # Displayed Canvas

    x_min = -2.5
    x_max = +2.5

    y_min = 0.0
    y_max = 1.0
    
    # Stepsize

    image_resolution = 0.02
    gridpoints = int((x_max - x_min) / image_resolution)
    
    # Create Numerical Grid for Cumulative Distributions

    x = np.linspace(x_min, x_max, gridpoints)
       
    # Color information - dictionary of rgb values for each color code (saturated)
    # Here only defined for types 0, 1, 2 (HC, PD, SWEDD)
    # (One could extend this for more values & colors, of course.)

    rgb = {'HC':[0.0,0.0,1.0], 'PD':[0.0,1.0,0.0], 'SWEDD':[1.0,0.0,0.0]}
    
    # Create a discrete function value table for each cohort present in the test set
    
    df_dict = {}
    
    for c in cohorts:
        df_dict[c] = np.zeros(gridpoints)
        
    # Sum up weighted normal cdf centered around each datapoint:
        
    for subj in subj_cond.index:
                
        # Choosen cumulative distribution function (CDF) or probability density (PDF):
        
        if (cumulative == True):
            normal_df = norm.cdf(x, loc = x_series[subj], scale = Gauss_width)
        else:
            normal_df = norm.pdf(x, loc = x_series[subj], scale = Gauss_width)
        
        # Add it to proper cohort function (and normalize it):
        
        df_dict[subj_cond[subj]] += normal_df / data_counts[subj_cond[subj]]
           
    # Subplot for resulting cdf's for cohorts present:
    
    fig = plt.figure(num=None, figsize=(8, 8), dpi=150, facecolor='w', edgecolor='k')
    
    ax = plt.subplot2grid((4,1), (0,0), rowspan=3)
    plt.title(x_series.name)
    
    # Function value limits depend on method chosen:

    if (cumulative == True):
        y_max = 1.0
    else:
        # Find maximum function value in set of cohorts

        y_max = 0
        for c in cohorts:
            y_max = max(y_max, df_dict[c].max())

    plt.axis([x_min, x_max, 0, 1.01 * y_max])
    
    for member in cohorts:
        ax.plot(x, df_dict[member], lw = 2, c = rgb[member], label = member)
        
    ax.legend(loc = 'upper left', scatterpoints = 1)
    fig.add_subplot(ax)
    
    # Create subplot with pinpoints for individual measurements by condition:
    
    ax = plt.subplot2grid((4,1), (3,0))
    ax.set_xticks([])
    ax.set_yticks([])
        
    plt.xlim(x_min, x_max)
    plt.ylim(0, 1)
    
    # Healthy controls:

    cond_filter = (subj_cond == 'HC')
    
    x_select = x_series[cond_filter]
    y_select = .75 * np.ones(data_counts['HC'])
     
    if (len(x_select) > 0):
        
        x_avg = x_select.mean()
           
        # Plot little blue markers for data points, big stars for cohort average
        
        ax.scatter(x_select, y_select, s = 25, c = rgb['HC'], alpha = .25)
        ax.scatter(x_avg, .75, s = 150, c = rgb['HC'], marker = '*')
            
    # Same now for Parkinson's cohort:

    cond_filter = (subj_cond == 'PD')
    
    x_select = x_series[(cond_filter)]
    y_select = .5 * np.ones(data_counts['PD'])
    
    if (len(x_select) > 0):
        
        x_avg = x_select.mean()
        
        # Plot little green markers for data points, big stars for cohort average
       
        ax.scatter(x_select, y_select, s = 25, c = rgb['PD'], alpha = .25)
        ax.scatter(x_avg, .5, s = 150 , c = rgb['PD'], marker = '*')
     
    # And finally, the SWEDD cohort:

    cond_filter = (subj_cond == 'SWEDD')
    
    x_select = x_series[(cond_filter)]
    y_select = .25 * np.ones(data_counts['SWEDD'])
    
    if (len(x_select) > 0):
        
        x_avg = x_select.mean()
        
        # Plot little red markers for data points, big stars for cohort average
        
        ax.scatter(x_select, y_select, s = 25, c = rgb['SWEDD'], alpha = .25)
        ax.scatter(x_avg, 0.25, s = 150 , c = rgb['SWEDD'], marker = '*')
        
        fig.add_subplot(ax)

    # Now, save the graph as a .PNG image.
    # Don't write it to disk - instead, return it as a string:
    
    imgdata = StringIO.StringIO()
    fig.savefig(imgdata, dpi = 150, format='png')
    plt.close()
    
    # Get the contents of the image file as a string:
    
    imgdata.seek(0)
    png_file = imgdata.buf
    
    return png_file