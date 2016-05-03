import numpy as np
import matplotlib.pyplot as plt

class NEURON:
    """
    This class implements several conveniences for 
    visualizing firing activity of single neurons
    
    Parameters
    ----------
    spiketimes: float, array of spike times
    
    
    Methods
    -------
    plot_raster
    plot_psth
    get_trialtype
    get_spikecounts
    plot_tuning_curve
    fit_tuning_curve
    """
    
    def __init__(self, spiketimes, name='neuron'):
        """
        Initialize the object
        """
        self.name = name
        self.spiketimes = spiketimes
        n_seconds = (self.spiketimes[-1]-self.spiketimes[0])
        n_spikes = np.size(spiketimes)
        self.firingrate = (n_spikes/n_seconds)

    #-----------------------------------------------------------------------
    def get_raster(self, events, features=[], selectors=[], \
                   window=[-100, 500], binsize=10, plot=True, sort=True):
        """
        Compute the raster and plot it
        
        Parameters
        ----------
        events: float, n x 1 array of event times 
                (e.g. stimulus/ trial/ fixation onset, etc.)

        """
    
        # Get a set of binary indicators for trials of interest
        if len(selectors) > 0:
            trials = self.get_trialtype(features, selectors)
        else:
            trials = np.transpose(np.atleast_2d(np.ones(np.size(events)) == 1))

        # Initialize rasters
        Rasters = dict()

        # Assign time bins
        firstspike = self.spiketimes[0]
        lastspike = self.spiketimes[-1]
        bins = np.arange(np.floor(firstspike),np.ceil(lastspike), 1e-3*binsize)

        # Loop over each raster
        for r in np.arange(trials.shape[1]):

            # Select events relevant to this raster
            selected_events = events[trials[:,r]]

            # Eliminate events before the first spike after last spike
            selected_events = selected_events[selected_events > firstspike]
            selected_events = selected_events[selected_events < lastspike]

            # bin the spikes into time bins
            spike_counts = np.histogram(self.spiketimes, bins)[0]
             
            # bin the events into time bins 
            event_counts = np.histogram(selected_events, bins)[0]
            event_bins =  np.where(event_counts > 0)[0]

            raster = np.array([(spike_counts[(i+window[0]/binsize): \
                                             (i+window[1]/binsize)]) \
                               for i in event_bins])
            Rasters[r] = raster
    
        # Show the raster     
        if plot == True:
            for i,r in enumerate(Rasters):
                raster = Rasters[r]

                
                if sort == True:
                    # Sorting by total spike count in the duration
                    raster_sorted = raster[np.sum(raster, axis=1).argsort()]
                else:
                    raster_sorted = raster
                plt.imshow(raster_sorted, aspect='auto', interpolation='none')
                plt.ylabel('trials')
                plt.xlabel('time [ms]')

                ax = plt.gca()
                xtics = np.arange(window[0], window[1], binsize*10)
                xtics = [str(i) for i in xtics]

                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['bottom'].set_visible(False)
                ax.spines['left'].set_visible(False)
                plt.xticks(np.arange(0,(window[1]-window[0])/binsize,10), xtics)
                plt.title('%s: Average firing rate %.1f Spks/s' % (self.name, self.firingrate))
                plt.axvline((-window[0])/binsize, color='r', linestyle='solid')
                plt.show()

    
        # Return all the rasters
        return Rasters
             
    #-----------------------------------------------------------------------
    def get_psth(self, events, features=[], selectors=[], \
                 window=[-100, 500], binsize=10, plot=True, \
                 colors=['#F5A21E','#134B64','#EF3E34','#02A68E','#FF07CD']):
        """
        Compute the psth and plot it
        
        Parameters
        ----------
        events: float, n x 1 array of event times 
                (e.g. stimulus/ trial/ fixation onset, etc.)
        """
        
        # Get all the rasters first
        Rasters = self.get_raster(events, features, selectors, window, binsize, plot=False)
        
        # Open the figure
        if plot == True:
            fig = plt.figure()
        
        # Initialize PSTH
        PSTH = dict()
    
        # Compute the PSTH
        for i, r in enumerate(Rasters):
            color = colors[i]
            PSTH[i] = dict()
            raster = Rasters[r]
             
            mean_psth = np.mean(raster,axis=0)/(1e-3*binsize)
            std_psth = np.sqrt(np.var(raster,axis=0))/(1e-3*binsize)
            sem_psth = std_psth/np.shape(mean_psth)[0]

            PSTH[i]['mean'] = mean_psth
            PSTH[i]['sem'] = sem_psth
            
            # Visualize the PSTH
            if plot == True:

                xx = np.linspace(window[0], window[1], num=np.diff(window)/binsize)
                
                fig.suptitle('PSTH', fontsize=14, fontweight='bold')
                ax = fig.add_subplot(111)
                fig.subplots_adjust(top=0.85)

                ax.plot([0,0],[0,np.max(mean_psth)], color='k')

                ax.plot(xx, mean_psth, color=color,lw=2)
                ax.plot(xx, mean_psth+sem_psth, color=color, ls =':')
                ax.plot(xx, mean_psth-sem_psth, color=color, ls =':')
                ax.legend(['event'])
                ax.set_title('%s: Average firing rate %.1f Spks/s' % (self.name, self.firingrate))
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.set_xlabel('time [ms]')
                ax.set_ylabel('spikes per second [spks/s]') 
            
        return PSTH
        
    #-----------------------------------------------------------------------
    def get_trialtype(self, features, selectors):
        """
        For an arbitrary query on features 
        get a subset of trials
        
        Parameters
        ----------
        features: float, n x p array of features, 
                  n trials, p features 
                  (e.g. stimulus/ behavioral features)
        selectors: list of intervals on arbitrary features
        
        Outputs
        -------
        trials: bool, n x 1 array of indicators
        """
        trials = []
        for r in selectors:
            selector = selectors[r]
            trials.append([np.all([np.all((features[r] >= selector[r][0], \
                                 features[r] <= selector[r][-1]), axis=0) \
                                 for r in selector], axis=0)])
        return np.transpose(np.atleast_2d(np.squeeze(trials)))
        
    #-----------------------------------------------------------------------
    def get_spikecounts(self, events, window = 1e-3*np.array([50.0, 100.0])):
        """
        Parameters
        ----------
        events: float, n x 1 array of event times
                (e.g. stimulus onset, trial onset, fixation onset, etc.)
        win: denoting the intervals
        
        Outputs
        -------
        spikecounts: float, n x 1 array of spike counts
        """
        y = np.zeros(events.shape)
        for e in len(events):
            spikecounts[e] = np.sum(np.all((spiketimes >= events[e] + window[0], \
                                            spiketimes <= events[e] + window[1]), \
                                            axis=0))
        return spikecounts
        