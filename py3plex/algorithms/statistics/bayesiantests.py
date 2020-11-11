# bayesian distance tests

import numpy as np
import numpy.matlib

LEFT, ROPE, RIGHT = range(3)


def correlated_ttest_MC(x, rope, runs=1, nsamples=50000):
    """
    See correlated_ttest module for explanations
    """
    if x.ndim == 2:
        x = x[:, 1] - x[:, 0]
    diff = x
    n = len(diff)
    nfolds = n / runs
    x = np.mean(diff)
    # Nadeau's and Bengio's corrected variance
    var = np.var(diff, ddof=1) * (1 / n + 1 / (nfolds - 1))
    if var == 0:
        return int(x < rope), int(-rope <= x <= rope), int(rope < x)

    return x + np.sqrt(var) * np.random.standard_t(n - 1, nsamples)


# Correlated t-test
def correlated_ttest(x, rope, runs=1, verbose=False, names=('C1', 'C2')):
    import scipy.stats as stats
    """
    Compute correlated t-test
 
    The function uses the Bayesian interpretation of the p-value and returns
    the probabilities the difference are below `-rope`, within `[-rope, rope]`
    and above the `rope`. For details, see `A Bayesian approach for comparing
    cross-validated algorithms on multiple data sets
    <http://link.springer.com/article/10.1007%2Fs10994-015-5486-z>`_,
    G. Corani and A. Benavoli, Mach Learning 2015.
 
    |
    The test assumes that the classifiers were evaluated using cross
    validation. The number of folds is determined from the length of the vector
    of differences, as `len(diff) / runs`. The variance includes a correction
    for underestimation of variance due to overlapping training sets, as
    described in `Inference for the Generalization Error
    <http://link.springer.com/article/10.1023%2FA%3A1024068626366>`_,
    C. Nadeau and Y. Bengio, Mach Learning 2003.)
 
    |
    Args:
    x (array): a vector of differences or a 2d array with pairs of scores.
    rope (float): the width of the rope  
    runs (int): number of repetitions of cross validation (default: 1)
    return: probablities (tuple) that differences are below -rope, within rope or
        above rope
    """
    if x.ndim == 2:
        x = x[:, 1] - x[:, 0]
    diff = x
    n = len(diff)
    nfolds = n / runs
    x = np.mean(diff)
    # Nadeau's and Bengio's corrected variance
    var = np.var(diff, ddof=1) * (1 / n + 1 / (nfolds - 1))
    if var == 0:
        return int(x < rope), int(-rope <= x <= rope), int(rope < x)
    pr = 1 - stats.t.cdf(rope, n - 1, x, np.sqrt(var))
    pl = stats.t.cdf(-rope, n - 1, x, np.sqrt(var))
    pe = 1 - pl - pr
    if verbose:
        print('P({c1} > {c2}) = {pl}, P(rope) = {pe}, P({c2} > {c1}) = {pr}'.
              format(c1=names[0], c2=names[1], pl=pl, pe=pe, pr=pr))
    return pl, pe, pr


# SIGN TEST
def signtest_MC(x, rope, prior_strength=1, prior_place=ROPE, nsamples=50000):
    """
    Args:
        x (array): a vector of differences or a 2d array with pairs of scores.
        rope (float): the width of the rope  
        prior_strength (float): prior strength (default: 1)
        prior_place (LEFT, ROPE or RIGHT): the region to which the prior is
            assigned (default: ROPE)
        nsamples (int): the number of Monte Carlo samples

    Returns:
        2-d array with rows corresponding to samples and columns to
        probabilities `[p_left, p_rope, p_right]`
    """
    if prior_strength < 0:
        raise ValueError('Prior strength must be nonegative')
    if nsamples < 0:
        raise ValueError('Number of samples must be a positive integer')
    if rope < 0:
        raise ValueError('Rope must be a positive number')

    if x.ndim == 2:
        x = x[:, 1] - x[:, 0]
    nleft = sum(x < -rope)
    nright = sum(x > rope)
    nrope = len(x) - nleft - nright
    alpha = np.array([nleft, nrope, nright], dtype=float)
    alpha += 0.0001  # for numerical stability
    alpha[prior_place] += prior_strength
    return np.random.dirichlet(alpha, nsamples)


def signtest(x,
             rope,
             prior_strength=1,
             prior_place=ROPE,
             nsamples=50000,
             verbose=False,
             names=('C1', 'C2')):
    """
    Args:
        x (array): a vector of differences or a 2d array with pairs of scores.
        rope (float): the width of the rope  
        prior_strength (float): prior strength (default: 1)
        prior_place (LEFT, ROPE or RIGHT): the region to which the prior is
            assigned (default: ROPE)
        nsamples (int): the number of Monte Carlo samples
        verbose (bool): report the computed probabilities
        names (pair of str): the names of the two classifiers

    Returns:
        p_left, p_rope, p_right 
    """
    samples = signtest_MC(x, rope, prior_strength, prior_place, nsamples)

    winners = np.argmax(samples, axis=1)
    pl, pe, pr = np.bincount(winners, minlength=3) / len(winners)
    if verbose:
        print('P({c1} > {c2}) = {pl}, P(rope) = {pe}, P({c2} > {c1}) = {pr}'.
              format(c1=names[0], c2=names[1], pl=pl, pe=pe, pr=pr))
    return pl, pe, pr


# SIGNEDRANK
def heaviside(X):
    Y = np.zeros(X.shape)
    Y[np.where(X > 0)] = 1
    Y[np.where(X == 0)] = 0.5
    return Y  # 1 * (x > 0)


def signrank_MC(x, rope, prior_strength=0.6, prior_place=ROPE, nsamples=50000):
    """
    Args:
        x (array): a vector of differences or a 2d array with pairs of scores.
        rope (float): the width of the rope  
        prior_strength (float): prior strength (default: 0.6)
        prior_place (LEFT, ROPE or RIGHT): the region to which the prior is
            assigned (default: ROPE)
        nsamples (int): the number of Monte Carlo samples

    Returns:
        2-d array with rows corresponding to samples and columns to
        probabilities `[p_left, p_rope, p_right]`
    """
    if x.ndim == 2:
        zm = x[:, 1] - x[:, 0]
    nm = len(zm)
    if prior_place == ROPE:
        z0 = [0]
    if prior_place == LEFT:
        z0 = [-float('inf')]
    if prior_place == RIGHT:
        z0 = [float('inf')]
    z = np.concatenate((zm, z0))
    n = len(z)
    z = np.transpose(np.asmatrix(z))
    X = np.matlib.repmat(z, 1, n)
    Y = np.matlib.repmat(-np.transpose(z) + 2 * rope, n, 1)
    Aright = heaviside(X - Y)
    X = np.matlib.repmat(-z, 1, n)
    Y = np.matlib.repmat(np.transpose(z) + 2 * rope, n, 1)
    Aleft = heaviside(X - Y)
    alpha = np.concatenate((np.ones(nm), [prior_strength]), axis=0)
    samples = np.zeros((nsamples, 3), dtype=float)
    for i in range(0, nsamples):
        data = np.random.dirichlet(alpha, 1)
        samples[i, 2] = numpy.inner(np.dot(data, Aright), data)
        samples[i, 0] = numpy.inner(np.dot(data, Aleft), data)
        samples[i, 1] = 1 - samples[i, 0] - samples[i, 2]

    return samples


def signrank(x,
             rope,
             prior_strength=0.6,
             prior_place=ROPE,
             nsamples=50000,
             verbose=False,
             names=('C1', 'C2')):
    """
    Args:
        x (array): a vector of differences or a 2d array with pairs of scores.
        rope (float): the width of the rope 
        prior_strength (float): prior strength (default: 0.6)
        prior_place (LEFT, ROPE or RIGHT): the region to which the prior is
            assigned (default: ROPE)
        nsamples (int): the number of Monte Carlo samples
        verbose (bool): report the computed probabilities
        names (pair of str): the names of the two classifiers

    Returns:
        p_left, p_rope, p_right
    """
    samples = signrank_MC(x, rope, prior_strength, prior_place, nsamples)

    winners = np.argmax(samples, axis=1)
    pl, pe, pr = np.bincount(winners, minlength=3) / len(winners)
    if verbose:
        print('P({c1} > {c2}) = {pl}, P(rope) = {pe}, P({c2} > {c1}) = {pr}'.
              format(c1=names[0], c2=names[1], pl=pl, pe=pe, pr=pr))
    return pl, pe, pr


def hierarchical(diff,
                 rope,
                 rho,
                 upperAlpha=2,
                 lowerAlpha=1,
                 lowerBeta=0.01,
                 upperBeta=0.1,
                 std_upper_bound=1000,
                 verbose=False,
                 names=('C1', 'C2')):
    # upperAlpha, lowerAlpha, upperBeta, lowerBeta, are the upper and lower bound for alpha and beta, which are the parameters of
    # the  Gamma distribution used as a prior for the degress of freedom.
    # std_upper_bound is a constant which multiplies the sample standard deviation, to set the upper limit of the prior on the
    # standard deviation.  Posterior inferences are insensitive to this value as this is large enough, such as 100 or 1000.

    samples = hierarchical_MC(diff, rope, rho, upperAlpha, lowerAlpha,
                              lowerBeta, upperBeta, std_upper_bound, names)
    winners = np.argmax(samples, axis=1)
    pl, pe, pr = np.bincount(winners, minlength=3) / len(winners)
    if verbose:
        print('P({c1} > {c2}) = {pl}, P(rope) = {pe}, P({c2} > {c1}) = {pr}'.
              format(c1=names[0], c2=names[1], pl=pl, pe=pe, pr=pr))
    return pl, pe, pr


def hierarchical_MC(diff,
                    rope,
                    rho,
                    upperAlpha=2,
                    lowerAlpha=1,
                    lowerBeta=0.01,
                    upperBeta=0.1,
                    std_upper_bound=1000,
                    names=('C1', 'C2')):
    # upperAlpha, lowerAlpha, upperBeta, lowerBeta, are the upper and lower bound for alpha and beta, which are the parameters of
    # the  Gamma distribution used as a prior for the degress of freedom.
    # std_upper_bound is a constant which multiplies the sample standard deviation, to set the upper limit of the prior on the
    # standard deviation.  Posterior inferences are insensitive to this value as this is large enough, such as 100 or 1000.

    import scipy.stats as stats
    import pystan
    # data rescaling, to have homogenous scale among all dsets
    stdX = np.mean(
        np.std(diff, 1)
    )  # we scale all the data by the mean of the standard deviation of data sets
    x = diff / stdX
    rope = rope / stdX

    # to avoid numerical problems with zero variance
    for i in range(0, len(x)):
        if np.std(x[i, :]) == 0:
            x[i, :] = x[i, :] + np.random.normal(
                0, np.min(1 / 1000000000, np.abs(
                    np.mean(x[i, :]) / 100000000)))

    # This is the Hierarchical model written in Stan
    hierarchical_code = """
    /*Hierarchical Bayesian model for the analysis of competing cross-validated classifiers on multiple data sets.
    */

      data {

        real deltaLow;
        real deltaHi;

        //bounds of the sigma of the higher-level distribution
        real std0Low; 
        real std0Hi; 

        //bounds on the domain of the sigma of each data set
        real stdLow; 
        real stdHi; 


        //number of results for each data set. Typically 100 (10 runs of 10-folds cv)
        int<lower=2> Nsamples; 

        //number of data sets. 
        int<lower=1> q; 

        //difference of accuracy between the two classifier, on each fold of each data set.
        matrix[q,Nsamples] x;

        //correlation (1/(number of folds))
        real rho; 

        real upperAlpha;
        real lowerAlpha;
        real upperBeta;
        real lowerBeta;

         }


      transformed data {

        //vector of 1s appearing in the likelihood 
        vector[Nsamples] H;

        //vector of 0s: the mean of the mvn noise 
        vector[Nsamples] zeroMeanVec;

        /* M is the correlation matrix of the mvn noise.
        invM is its inverse, detM its determinant */
        matrix[Nsamples,Nsamples] invM;
        real detM;

        //The determinant of M is analytically known
        detM <- (1+(Nsamples-1)*rho)*(1-rho)^(Nsamples-1);

        //build H and invM. They do not depend on the data.
        for (j in 1:Nsamples){
          zeroMeanVec[j]<-0;
          H[j]<-1;
          for (i in 1:Nsamples){
            if (j==i)
              invM[j,i]<- (1 + (Nsamples-2)*rho)*pow((1-rho),Nsamples-2);
            else
              invM[j,i]<- -rho * pow((1-rho),Nsamples-2);
           }
        }
        /*at this point invM contains the adjugate of M.
        we  divide it by det(M) to obtain the inverse of M.*/
        invM <-invM/detM;
      }

      parameters {
        //mean of the  hyperprior from which we sample the delta_i
        real<lower=deltaLow,upper=deltaHi> delta0; 

        //std of the hyperprior from which we sample the delta_i
        real<lower=std0Low,upper=std0Hi> std0;

        //delta_i of each data set: vector of lenght q.
        vector[q] delta;               

        //sigma of each data set: : vector of lenght q.
        vector<lower=stdLow,upper=stdHi>[q] sigma; 

        /* the domain of (nu - 1) starts from 0
        and can be given a gamma prior*/
        real<lower=0> nuMinusOne; 

        //parameters of the Gamma prior on nuMinusOne
        real<lower=lowerAlpha,upper=upperAlpha> gammaAlpha;
        real<lower=lowerBeta, upper=upperBeta> gammaBeta;

      }

     transformed parameters {
        //degrees of freedom
        real<lower=1> nu ;

        /*difference between the data (x matrix) and 
        the vector of the q means.*/
        matrix[q,Nsamples] diff; 

        vector[q] diagQuad;

        /*vector of length q: 
        1 over the variance of each data set*/
        vector[q] oneOverSigma2; 

        vector[q] logDetSigma;

        vector[q] logLik;

        //degrees of freedom
        nu <- nuMinusOne + 1 ;

        //1 over the variance of each data set
        oneOverSigma2 <- rep_vector(1, q) ./ sigma;
        oneOverSigma2 <- oneOverSigma2 ./ sigma;

        /*the data (x) minus a matrix done as follows:
        the delta vector (of lenght q) pasted side by side Nsamples times*/
        diff <- x - rep_matrix(delta,Nsamples); 

        //efficient matrix computation of the likelihood.
        diagQuad <- diagonal (quad_form (invM,diff'));
        logDetSigma <- 2*Nsamples*log(sigma) + log(detM) ;
        logLik <- -0.5 * logDetSigma - 0.5*Nsamples*log(6.283);  
        logLik <- logLik - 0.5 * oneOverSigma2 .* diagQuad;

      }

      model {
        /*mu0 and std0 are not explicitly sampled here.
        Stan automatically samples them: mu0 as uniform and std0 as
        uniform over its domain (std0Low,std0Hi).*/

        //sampling the degrees of freedom
        nuMinusOne ~ gamma ( gammaAlpha, gammaBeta);

        //vectorial sampling of the delta_i of each data set
        delta ~ student_t(nu, delta0, std0);

        //logLik is computed in the previous block 
        increment_log_prob(sum(logLik));   
     }
    """
    datatable = x
    std_within = np.mean(np.std(datatable, 1))

    Nsamples = len(datatable[0])
    q = len(datatable)
    if q > 1:
        std_among = np.std(np.mean(datatable, 1))
    else:
        std_among = np.mean(np.std(datatable, 1))

    # Hierarchical data in Stan
    hierachical_dat = {
        'x': datatable,
        'deltaLow': -np.max(np.abs(datatable)),
        'deltaHi': np.max(np.abs(datatable)),
        'stdLow': 0,
        'stdHi': std_within * std_upper_bound,
        'std0Low': 0,
        'std0Hi': std_among * std_upper_bound,
        'Nsamples': Nsamples,
        'q': q,
        'rho': rho,
        'upperAlpha': upperAlpha,
        'lowerAlpha': lowerAlpha,
        'upperBeta': upperBeta,
        'lowerBeta': lowerBeta
    }

    # Call to Stan code
    fit = pystan.stan(model_code=hierarchical_code,
                      data=hierachical_dat,
                      iter=1000,
                      chains=4)

    la = fit.extract(permuted=True)  # return a dictionary of arrays
    mu = la['delta0']
    stdh = la['std0']
    nu = la['nu']

    samples = np.zeros((len(mu), 3), dtype=float)
    for i in range(0, len(mu)):
        samples[i, 2] = 1 - stats.t.cdf(rope, nu[i], mu[i], stdh[i])
        samples[i, 0] = stats.t.cdf(-rope, nu[i], mu[i], stdh[i])
        samples[i, 1] = 1 - samples[i, 0] - samples[i, 2]

    return samples


def plot_posterior(samples, names=('C1', 'C2'), proba_triplet=None):
    """
    Args:
        x (array): a vector of differences or a 2d array with pairs of scores.
        names (pair of str): the names of the two classifiers

    Returns:
        matplotlib.pyplot.figure
    """
    return plot_simplex(samples, names, proba_triplet)


def plot_simplex(points, names=('C1', 'C2'), proba_triplet=None):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.pylab import rcParams

    def _project(points):
        from math import sqrt, sin, cos, pi
        p1, p2, p3 = points.T / sqrt(3)
        x = (p2 - p1) * cos(pi / 6) + 0.5
        y = p3 - (p1 + p2) * sin(pi / 6) + 1 / (2 * sqrt(3))
        return np.vstack((x, y)).T

    vert0 = _project(
        np.array([[0.3333, 0.3333, 0.3333], [0.5, 0.5, 0], [0.5, 0, 0.5],
                  [0, 0.5, 0.5]]))

    fig = plt.figure()
    fig.set_size_inches(8, 7)

    nl, ne, nr = np.max(points, axis=0)
    for i, n in enumerate((nl, ne, nr)):
        if n < 0.001:
            print("p{} is too small, switching to 2d plot".format(names[::-1] +
                                                                  ["rope"]))
            coords = sorted(set(range(3)) - i)
            return plot2d(points[:, coords], labels[coords])

    # triangle
    fig.gca().add_line(
        Line2D([0, 0.5, 1.0, 0], [0, np.sqrt(3) / 2, 0, 0], color='black'))
    # decision lines
    for i in (1, 2, 3):
        fig.gca().add_line(
            Line2D([vert0[0, 0], vert0[i, 0]], [vert0[0, 1], vert0[i, 1]],
                   color='black'))
    # vertex labels
    rcParams.update({'font.size': 16})
    fig.gca().text(-0.08,
                   -0.08,
                   'p({} ({}))'.format(names[0], proba_triplet[0]),
                   color='black')
    fig.gca().text(0.44, np.sqrt(3) / 2 + 0.05, 'p(rope)', color='black')
    fig.gca().text(0.650,
                   -0.08,
                   'p({} ({}))'.format(names[1], proba_triplet[2]),
                   color='black')

    # project and draw points
    tripts = _project(points[:, [0, 2, 1]])
    plt.hexbin(tripts[:, 0], tripts[:, 1], mincnt=1, cmap=plt.cm.Greens_r)
    # Leave some padding around the triangle for vertex labels
    fig.gca().set_xlim(-0.2, 1.2)
    fig.gca().set_ylim(-0.2, 1.2)
    fig.gca().axis('off')
    return fig
