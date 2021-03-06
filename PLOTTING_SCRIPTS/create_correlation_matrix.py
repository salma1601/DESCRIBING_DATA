#!/usr/bin/env python

def calc_stats(df, measures):
    '''
    Calc stats takes a data frame (df) and a list of measures of interest
    and calculates and returns four matrices:
        * pairES --> pairwise effect size matrix
        * pairP ---> pairwise p value matrix
        * partES --> partial effect size matrix
        * partP ---> partial p value matrix
        
    If the y measure is *dichotomous* the effect size is that of an odds ratio,
    calculated as the exponent of the parameter estimate of the logistic
    regression. A pairwise logistic regression is run for the pairES, and a 
    full model is run for the partES.
    
    If the y measure is *continuous* the effect size is that of a pearson
    correlation. A pairwise correlation is performed for the pairwiseES and
    the partial correlation is calculated as a correlation of the residuals
    from two models with x and y missing as appropriate (using the
    partial_correlation function defined below).

    Written by Kirstie Whitaker (kw401@cam.ac.uk) on 11th May 2014
    '''
    
    # Import the modules you need
    import numpy as np
    from scipy.stats import pearsonr

    # Set up the empty arrays that you're interested in
    (pairP_mat, pairES_mat, 
                partP_mat, partES_mat) = setup_arrays(measures)
        
  # Loop through all the measures
    for i, y in enumerate(measures):

        # Your covars are all the measures that aren't y
        covars = [x for x in measures if not x == y]
        
        # Your multiple regression formula is just a
        # linear regression of all the covars on y
        RHS = ' + '.join(covars)
        formula_all = '{} ~ {}'.format(y, RHS)
        
        # Fit the appropriate model
        lm_all = fit_model(y, formula_all, df)
        
        # Now to fill in the six different matrices
        # for all the "j" columns of this "i"th row
        for j, x in enumerate(measures):
            
            # Set all the matrix element values equal to 1 
            # if you're filling in the diagonal of the matrix
            if not i == j:
                
                # Calculate the ols regression or logistic
                # regression for just this pair of variables
                formula_pair = '{} ~ {}'.format(y, x)
                
                lm_pair = fit_model(y, formula_pair, df)
            
                # Fill in the correct p values
                pairP_mat[i ,j] = lm_pair.pvalues[x]
                partP_mat[i, j] = lm_all.pvalues[x]
                
                # Now fill in the effect size values
                if df[y].nunique() == 2:
                    pairES_mat[i, j] = np.exp(lm_pair.params)[x]
                    partES_mat[i, j] = np.exp(lm_all.params)[x]
                else:
                    pairES_mat[i, j] = pearsonr(df[x], df[y])[0]
                    partES_mat[i, j] = partial_correlation(df, x, y, measures)[0]
                    
    return (pairP_mat, pairES_mat, 
                partP_mat, partES_mat)

    
def setup_arrays(measures):
    '''
    This very little function just creates the following arrays
    as arrays of 1s. The arrays are square and have length and 
    with equal to the number of meaures.
    '''
    # Import what you need
    import numpy as np
    
    # Create an array of ones that's the appropriate size
    ones_array = np.ones([len(measures), len(measures)])

    # There are a few arrays we want to make
    # specifically pairwise comparisons and partial comparisons
    # and we'll save the effect seize (R if OLS, odds ratio if logistic)
    # and P values (for both)
    pairES_mat = np.copy(ones_array)
    pairP_mat = np.copy(ones_array)
    
    partES_mat = np.copy(ones_array)
    partP_mat = np.copy(ones_array)

    return (pairP_mat, pairES_mat, 
                partP_mat, partES_mat)



def fit_model(y, formula, df):
    from statsmodels.formula.api import ols, logit

    # If you have a dichotomous variable then
    # we're going to run a logistic regression
    if df[y].nunique() == 2:
        lm = logit(formula, df).fit()
    # otherwise we'll run an ordinary least
    # squares regression
    else:
        lm = ols(formula, df).fit()

    return lm


    
def partial_correlation(df, x, y, measures):
    '''
    A little (but hopefully quite useful) piece of code that calculates
    the partial correlation between x and y while covarying for the
    remaining measures in a list of measures.
    
    It requires a data frame, the names of x and y, and a list of measures
    (that don't need to, but can, contain x or y)
    
    This function returns r and p values
    '''
    # Import the modules you need
    from scipy.stats import pearsonr
    from statsmodels.formula.api import ols

    # Your covars are all the measures you've selected
    # that aren't x and y
    covars = [ z for z in measures if not z == x and not z == y ]
                                
    # Your formulae just set x and y to be a function
    # of all the other covariates
    formula_x = x + ' ~ ' + ' + '.join(covars)
    formula_y = y + ' ~ ' + ' + '.join(covars)

    # Fit both of these formulae
    lm_x = ols(formula_x, df).fit()
    lm_y = ols(formula_y, df).fit()
        
    # Save the residuals from the model
    res_x = lm_x.resid
    res_y = lm_y.resid
            
    r, p = pearsonr(res_x, res_y)
    
    return r, p


def plot_matrix(df, measures, names, height, title, star=False, tri=True):
    '''
    This code makes separate figures of the pairwise and partial correlation
    matrices as created by the calc_stats function.
    
    The pairwise correlation is on top and the partial correlation is below.
    
    The code returns the two figures along with the four stats matrices as
    calculated by calc_stats.
    
    
    '''    
    
    # Import the various modules that you need
    import numpy as np
    import matplotlib.pylab as plt
    import matplotlib.colors as colors
    
    # First calculate the pairwise and partial statistic matrices
    (pairP_mat, pairES_mat, 
            partP_mat, partES_mat)  = calc_stats(df, measures)
    
    # Make two figures
    pairFig = plt.figure("pairFig", figsize=(height, height))
    partFig = plt.figure("partFig", figsize=(height, height))
    
    # Set a sensible sized font
    font = { 'size'   : 22 * height/10}
    plt.rc('font', **font)

    # We're going to make two separate figures:
    for ES_mat, P_mat, fig_name, title_suffix in zip([pairES_mat, partES_mat],
                                  [pairP_mat, partP_mat],
                                  ["pairFig", "partFig"],
                                  ['Pairwise', 'Partial']):

        # Set the appropriate figure as your current figure
        fig = plt.figure(fig_name)                                    
        # Add an axis for the figure
        ax = fig.add_subplot(111)

        # Masks for the odds ratios and the pearson effect sizes
        maskR, maskO = calc_masks(df, measures, tri)
        
        # Mask the effect size matrices
        mR_mat = np.ma.masked_array(ES_mat, mask=maskR)
        mO_mat = np.ma.masked_array(ES_mat, mask=maskO)

        # Make the background grey
        pbg = plt.imshow(np.ones_like(ES_mat)*0.5, 
                             cmap='Greys', 
                             vmin=0, vmax=1, 
                             interpolation='none')
        
        # Plot the two effect size maps
        r = plt.imshow(mR_mat, 
                           cmap = 'RdBu_r', 
                           vmin=-1, vmax=1, 
                           interpolation='none')
        o = plt.imshow(mO_mat, 
                           cmap = 'PRGn', 
                           vmin=0.2, vmax=5, 
                           interpolation='none', 
                           norm=colors.LogNorm(vmin=0.02, vmax=5))

        # Make the diagonal line black
        eye_mat = np.eye(mR_mat.shape[0])
        meye = np.ma.masked_array(eye_mat, 1-eye_mat)
        eye = plt.imshow(meye, 
                             cmap='Greys', 
                             vmin=0, vmax=1, 
                             interpolation='none')
        
        # Make your tick_labels line up sensibly
        locs = np.arange(0, float(len(measures)))
        ax.set_xticks(locs)
        ax.set_xticklabels(names, rotation=45, ha='right')
        ax.set_yticks(locs)
        ax.set_yticklabels(names)

        plt.tight_layout()
        
        # Set up TWO lovely color bars
        ax = setup_colorbars(fig, ax, r, o, only_useful=False, maskR=0, maskO=0)

        # Give your plot a lovely title
        ax.set_title(title + '\n' + title_suffix)
    
        # If stars is true then add the stars to the appropriate cells
        if star:
            ax = add_stars(ax, P_mat, tri)
        

    return pairFig, pairES_mat, pairP_mat, partFig, partES_mat, partP_mat




def calc_masks(df, measures, tri=True):
    '''
    This little piece of code figures out the appropriate indices of the
    ES_mat to plot as pearson correlations or as odds ratios.
    
    If tri=True then the code additionally masks the upper triangle so that
    there are no redundant values plotted in the figure. (Note that actually
    combinations of continuous and dichotomous measures will be calculated
    differently and therefore if tri is True the differences between these
    measures will be hidden. Importantly though, this is very unlikely to
    make a difference in the real world)
    '''
    # Import the modules you need
    import numpy as np
    
    # Create the empty masks for the odds ratios and the pearson effect sizes
    ones_array = np.ones([len(measures), len(measures)])
    maskO = np.copy(ones_array)
    maskR = np.copy(ones_array)

    # Loop through the measures and mark (with a 0) all rows that represent
    # dichotomous variables in maskO and all others in maskR
    for y in measures:
        if df[y].nunique() == 2:
            maskO[measures.index(y),:] = 0
        else:
            maskR[measures.index(y),:] = 0

    # If tri=True create a mask of only the lower triangle
    if tri:
        maskTri = np.triu(ones_array)
                
        # Add this mask to the R and O masks. The reason you add these
        # is because in the next step we're going to only plot
        # values that have a mask value of 0. If you multiply them
        # (which is what I played around with for ages) then you include
        # too many cells.
        maskR = maskR + maskTri
        maskO = maskO + maskTri

    # Return the masks
    return maskR, maskO


def setup_colorbars(fig, ax, r, o, only_useful=False, maskR=0, maskO=0):
    '''    
    Set up two lovely colorbars, one for the pearson correlations 
    and one for the odds ratios.
    
    If only_useful is true then maskR and maskO are used to figure out
    which of the colorbars to add to the axis.
    
    If only_useful is false then both colorbars are added to the axis
    '''
    
    # Import what you need
    import numpy as np
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    # Make the axis locatable
    divider = make_axes_locatable(ax)

    # If only_useful is True then we're going to figure out which of these
    # two colorbars we actually need
    if only_useful:
        # Include the odds ratio colorbar if maskO has some non-zero values
        includeO = not np.all(maskO)
        includeR = not np.all(maskR)
    else:
        includeO = True
        includeR = True

    if includeR:
        # Set up the pearson colorbar
        tick_labels = [ '{: 1.1f}'.format(tick) for tick in list(np.linspace(-1,1,5)) ]
        cax_r = divider.append_axes("right", "5%", pad="12%")
        cbar_r = fig.colorbar(r, cax=cax_r, ticks = list(np.linspace(-1,1,5)))
        cax_r.set_yticklabels(tick_labels) 
        cax_r.set_ylabel('Pearson r', size='small')
        cax_r.yaxis.set_label_position("left")
        
    if includeO:
        
        # Figure out how much you need to pad this color bar axis by.
        # It will depend on whether you've already plotted the pearson colorbar
        if includeR:
            pad = "25%"
        else:
            pad = "12%"
            
        # Set up the odds ratio colorbar
        tick_labels = [ '{: 1.1f}'.format(tick) for tick in list(np.logspace(np.log(0.2), np.log(5), 5, base=np.e)) ]
        cax_o = divider.append_axes("right", "5%", pad=pad)
        cbar_o = fig.colorbar(o, cax=cax_o, ticks = list(np.logspace(np.log(0.2), np.log(5), 5, base=np.e)))
        cax_o.set_yticklabels(tick_labels)
        cax_o.set_ylabel('Odds ratio', size='small')
        cax_o.yaxis.set_label_position("left")
    
    return ax


def add_stars(ax, P_mat, tri=True):
    '''
    Use the p matrix to add stars to the significant cells.

    If triangle is True then only put stars in the lower triangle, otherwise
    put them in all the cells
    '''
    # Import what you need
    import numpy as np
    # Get the indices you need
    if tri:
        i_inds, j_inds = np.triu_indices_from(P_mat, k=0)
    else:
        i_inds, j_inds = np.triu_indices_from(P_mat, k=P_mat.shape[0]*-1)
    
    # Loop through all the measures and fill the arrays
    for i, j in zip(i_inds, j_inds):

        # Figure out the text you're going to put on the plot
        star = ''
        if 0.01 < P_mat[i,j] < 0.05:
            star = '*'
        elif 0.001 <= P_mat[i,j] < 0.01:
            star = '**'
        elif P_mat[i,j] < 0.001:
            star = '***'

        text = ax.text(i, j, star,
            horizontalalignment='center',
            verticalalignment='center',
            color = 'k')

    return ax
