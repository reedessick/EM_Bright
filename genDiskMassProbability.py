import numpy as np
import em_progenitors
#import readMassXML
import sys


class genDiskMass:
    def __init__(self, input, output, threshold):	# RE: different from Reed's patch here. Probably this does not need modification
							# New instance variable used by Reed is already present as self.max_ns_g_mass
        '''
        input could be a posterior sample from lalinference output,
        3D ambiguiity ellipsoid sample, 2D ambiguity ellipse samples
        from xml file or 3D ellipsoid samples in the form of numpy arrays.
        Output is not used right now, but a dummy name could be given.
        Threshold determines condition for EM brightness (0.03 in Pannarale-Ohme)
        '''
        [self.ns_sequence, self.max_ns_g_mass] = em_progenitors.load_ns_sequence('2H')
        self.inputFile = input
        self.outputFile = output
        self.threshold = threshold

    def fromPostSamp(self, burn=None, skipHeader=12):
        '''
        This method uses lalinference samples. If not burn value is given then the
        entire posterior sample is used. If the burn option is supplied then the
        initial part of the chain (upto iteration number = burn) is ignored.
        Output is a list whose first two elements are the probability that the primary
        and secondary object is a NS respectively. The third element gives the remnant
        mass outside the black hole in access of the threshold mass supplied.
        '''
        data = np.recfromtxt(self.inputFile, names=True, skip_header=skipHeader)
        burnin = 0
        if burn: burnin = burn
        mc = data['mc'][burnin:]
        massRatio = data['q'][burnin:]
        self.chi = data['a1'][burnin:]
        self.eta = massRatio/((1 + massRatio)**2)
        self.mPrimary = (massRatio**(-0.6)) * mc * (1. + massRatio)**0.2
        self.mSecondary = (massRatio**0.4) * mc * (1. + massRatio)**0.2
        NS_prob_2 = np.sum(self.mSecondary < self.max_ns_g_mass)*100./len(self.mSecondary) # RE: Max NS mass was hardcoded as 3.0. Should be gotten from class variable
        NS_prob_1 = np.sum(self.mPrimary < self.max_ns_g_mass)*100./len(self.mPrimary)
        return [NS_prob_1, NS_prob_2, self.computeRemMass()]

    def fromMassSpinAmbiguity(self):
        '''
        This method reads the samples from the 3D ambiguity ellipsoid from a txt file
        generated by the function getSamples in the script getEllipsoidSamples.py
        Use this if the saveData argument was used in calling of the getSamples function.
        '''
        data = np.loadtxt(self.inputFile)
        mc = data[:,1]
        self.eta = data[:,2]
        self.chi = data[:,3]
        self.mPrimary = 0.5*mc*(self.eta**(-3./5.))*(1 + np.sqrt(1 - 4*self.eta))
        self.mSecondary = 0.5*mc*(self.eta**(-3./5.))*(1 - np.sqrt(1 - 4*self.eta))
        NS_prob_2 = np.sum(self.mSecondary < self.max_ns_g_mass)*100./len(self.mSecondary)
        NS_prob_1 = np.sum(self.mPrimary < self.max_ns_g_mass)*100./len(self.mPrimary)
        return [NS_prob_1, NS_prob_2, self.computeRemMass()]

    def fromEllipsoidSample(self):
        '''
        This method takes the input from the return value of getSamples and computes the
        EM-bright probabilities. Use this if no output file was generated in the fucntion
        call of getSamples, or if this function (fromEllipsoidSample) immediately after
        getSamples was called to generate the ambiguity ellipsoid samples
        '''
        data = self.inputFile
        mc = data[:,0]
        self.eta = data[:,1]
        self.chi = data[:,2]
        self.mPrimary = 0.5*mc*(self.eta**(-3./5.))*(1 + np.sqrt(1 - 4*self.eta))
        self.mSecondary = 0.5*mc*(self.eta**(-3./5.))*(1 - np.sqrt(1 - 4*self.eta))
        NS_prob_2 = np.sum(self.mSecondary < self.max_ns_g_mass)*100./len(self.mSecondary)
        NS_prob_1 = np.sum(self.mPrimary < self.max_ns_g_mass)*100./len(self.mPrimary)
        return [NS_prob_1, NS_prob_2, self.computeRemMass()]


    def computeRemMass(self):
        '''
        This method calls the em_progenitors.py script to compute the remnant disk mass
        for the posterior or ambiguity ellipsoid samples.
        '''
        remnant_mass = []
        for ii in range(0, len(self.eta)):
            try:
                mm = em_progenitors.remnant_mass(self.eta[ii], self.mSecondary[ii], self.ns_sequence, self.chi[ii], 0, self.threshold)[0]
            except ValueError: mm = 0.
            if mm <= 0: mm = 0
            remnant_mass.append(mm)
        return np.array(remnant_mass)


# Reed's edit. New function to give the EM bright probability using new EMbright boundary
    def computeEMBrightProb(self):
	'''
	Computes EM bright probability using remnant disk mass and max NS mass.
	Draws the boundary of max NS mass and Foucart expression
	'''
	remMass = self.computeRemMass()
	prob	= (self.mPrimary < self.max_ns_g_mass)*(self.mSecondary < self.max_ns_g_mass) + (remMass > self.threshold)
	return 100.0*np.sum(prob > 0.) / len(prob)
