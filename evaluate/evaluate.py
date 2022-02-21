"""D4C3 scoring function

Based on Matlab script available on
https://www.synapse.org/#!Synapse:syn2825304, which is an
original code from  Gustavo A. Stolovitzky and Robert Prill.
"""
import os
from dreamtools.core.challenge import Challenge
import pandas as pd
import numpy as np
import pylab


class D4C3(Challenge):
    """A class dedicated to D4C3 challenge

    ::

        from dreamtools import D4C3
        s = D4C3()
        filename = s.download_template()
        s.edge_count = 20
        s.score(filename)

    Data and templates are inside Dreamtools.


    .. note:: A parameter called cost_per_link is hardcoded for the challenge.
        It was compute as min {Prediction Score / Edge Count} amongst all 
        submissions. For this scoring function, :attr:`cost_per_link` is set 
        to 0.0827 and may be changed by the user.

    """
    def __init__(self, verbose=True, download=True, edge_count=None,
                 cost_per_link=0.0827, **kargs):
        """.. rubric:: constructor

        :param int edge_count: if not provided, a prompt will ask for its 
            value.
        :param float cost_per_link: a cost

        """
        super(D4C3, self).__init__('D4C3', verbose, download, **kargs)

        # cost_per_link Was determined empirically from all the teams' submissions
        # as r = min(prediction_score / edge_count).
        self.cost_per_link = cost_per_link
        self.edge_count = edge_count
        self.species = ['AKT', 'ERK12', 'Ikb', 'JNK12', 'p38', 
                'HSP27', 'MEK12']

        self._load_gold_standard()
        self._fetch_normalisation()

    def download_goldstandard(self):
        filename = self._pj([self.classpath, 'goldstandard', 'D4C3_goldstandard.csv'])
        return filename


    def _load_gold_standard(self):
        filename = self.download_goldstandard()
        df = pd.read_csv(filename)
        df.replace('NOT AVAILABLE', np.nan, inplace=True)
        self.goldstandard = df.copy()
        pass

    def download_template(self):
        filename = self._pj([self.classpath, 'templates', 'D4C3_templates.csv'])
        return filename


    def _load_prediction(self, filename):
        df = pd.read_csv(filename)
        df.replace('NOT AVAILABLE', np.nan, inplace=True)
        self.prediction = df.copy()
        pass

    def score(self, filename):
        """Compute the score

        See synapse page for details about the scoring function.

        """
        self._load_prediction(filename)
        # compute error and pval for each molecular species

        # some columns have NA that were originally string (NOT AVAILABLE) so
        # those columns are not float type. We need to cast them to float.
        # Besides, we care only about species and time 30
        T = self.prediction[self.species][self.prediction.Time==30].astype(float)
        G = self.goldstandard[self.species][self.goldstandard.Time==30].astype(float)

        self.errors = {}
        self.x_norm_log = {}
        self.y_log = {}
        self.pvals = {}
        for i, species in enumerate(self.species):

            m, b, rho = self._fit_line(species)

            t = T[species]
            g = G[species]

            # zero counting correction prevents log(0)
            x_log = pylab.log10(t + 1.)
            y_log = pylab.log10(g + 1.)

            # normalise
            x_norm_log = m * x_log + b

            # transform back to original space
            x_norm_lin = 10 ** x_norm_log
            y_lin = 10 ** y_log

            # the same prediction score from DREAM3
            numerator = (y_lin - x_norm_lin) ** 2    # cancels +1 correction
            denominator = 300**2 + (0.08*g) ** 2
            error_individual = numerator / denominator

            # add the individual scores
            self.errors[species] = error_individual.sum()

            # load prob density function
            import scipy.io
            filename = self._pj([self.classpath, 'data', 
                'pdf_score_%s.mat' % str(i+1)])
            proba = scipy.io.loadmat(filename)
            X, Y, C = proba['X'][0], proba['Y'][0], proba['C'][0]

            # save some information
            self.x_norm_log[species] = x_norm_log.copy()
            self.y_log[species] = y_log.copy()
            self.pvals[species] = self._probability(X, Y, self.errors[species])

        # cast to list is required in py3
        self.prediction_score = -pylab.mean(pylab.log10(
            list(self.pvals.values())))

        if self.edge_count is None:
            try:
                input = raw_input
            except NameError: pass
            edge_count = int(input("Please enter an edge count values\n" + 
            "It should be number of edges in your network (20 for the template):"))
            assert edge_count >= 0
        else:
            edge_count = self.edge_count

        self.overall_score = self.prediction_score - self.cost_per_link * edge_count

        df = pd.DataFrame()
        df['Edge_count'] = [edge_count]
        df['Overall_score'] = [self.overall_score]
        df['Prediction_score'] = [self.prediction_score]
        for species in self.species:
            df[species+'_pvalue'] = [self.pvals[species]]
        return df


        #return a final data dataframe

    def plot(self):
        """Plots prediction versus gold standard for each species

        .. plot::
            :include-source:
            :width: 80%

            from dreamtools import D4C3
            s = D4C3()
            filename = s.download_template()
            s.edge_count = 20
            s.score(filename)
            s.plot()

        """
        if hasattr(self, 'x_norm_log') is False:
            print('Call score() method first. Nothing to plot.')
            return
        pylab.clf()

        for i, species in enumerate(self.species):
            pylab.subplot(4, 2, i+1)
            pylab.plot(self.x_norm_log[species], self.y_log[species], '.')
            pylab.grid(True)
            #pylab.axis('equal')

            Xlim = np.array(pylab.xlim())
            Xlim[1] = max([Xlim[1], self.y_log[species].max()])
            Xlim[0]-= 0.5
            Xlim[1]+=0.5

            pylab.plot(Xlim, Xlim, 'k--')

            X = self.x_norm_log[species]
            mask = X.isnull() == False
            N = mask.sum()
            Y = self.y_log[species]
            b, m = np.linalg.lstsq(np.vstack([np.ones(N), X[mask]]).T, 
                    Y[mask])[0]
            ax = pylab.plot(Xlim, np.array(Xlim*m+b), 'g-')
            pylab.xlim(Xlim)
            pylab.ylim(Xlim)
            pylab.title(species)
        pylab.subplot(4,2,8)
        pylab.text(.05,.5,
                '- Prediction (y-axis) versus gold \n' +\
                "  standard (x-axis).\n" +\
                '- Dashed lines shows the y=x best fit')
        pylab.axis('off')
        pylab.tight_layout()


    def _probability(self, X, Y, x):
        dx = X[1]-X[0]
        P = sum(Y[X <= x])*dx
        return P

    def _fetch_normalisation(self):
        # x is training
        # y is gold
        filename = self._pj([self.classpath, 'data', 'common_training.csv'])
        training = pd.read_csv(filename)

        #filename = self._pj([self.classpath, 'data', 'common_gold.csv'])
        self.download_goldstandard()
        goldfile = pd.read_csv(filename)

        #"""function [m b rho] = fetch_normalization(jj)
        #%% jj is the index of the molecule (1-7)

        colnames = self.species

        self.norm_training = pylab.log10(training[colnames] + 1)
        self.norm_gold = pylab.log10(goldfile[colnames] + 1)

        #which one is x/y?
        #[m b rho] = fit_line(x,y);

    def _fit_line(self, species):

        x = self.norm_training[species].dropna().values
        y = self.norm_gold[species].dropna().values
        N = len(x)

        # equivalent to X/y in matlab
        [solution, residuals, ranks, s] = np.linalg.lstsq(np.vstack([np.ones(N), x]).T, y)

        b,m =  solution
        rho = np.corrcoef(x,y)[1,0]
        return m, b, rho
