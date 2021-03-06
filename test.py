import numpy as np
import matplotlib.pyplot as plt

from scipy.special import polygamma, gamma, kv
seed = 5

from classy import Class

from tools import get_EE, get_TE, get_TT

import healpy as hp

'''
Uses CLASS to plot standard power spectrum, the baseline for our analysis.
'''

from scipy.stats import invwishart
def lnprob(tau, Clhat):
    #  this is going to be a 2x2 matrix with covariance:
    #|TT TE|
    #|TE EE|
    ell = 2
    TT = get_TT(tau=tau)[ell]
    TE = get_TE(tau=tau)[ell]
    EE = get_EE(tau=tau)[ell]
    V = np.array([[TT,TE],[TE,EE]])
    df = 2*ell+1
    # Clhat needs to be in matrix form
    Clhat = np.copy(V)
    print(invwishart.pdf(Clhat, df, scale=V))


def lnprob_EE_ell(tau, taus, EE_arr, Clhat, noise=0):
    # clhat is the observed spectrum
    # return log(P(Clhat | C_l))
    # Working off of equation (8) of HL08
    i = (np.abs(taus - tau)).argmin()
    ell = np.arange(len(EE_arr[i]))
    Cl = EE_arr[i] +noise# the theory power spectrum that we're comparing to.
    #chi2_ell = (2*ell+1)*(Clhat/Cl + \
    #        np.log(Cl)-(2*ell-1)/(2*ell+1)*np.log(Clhat))
    # If you add an arbitrary constant, you get this;
    chi2_ell = (2*ell+1)*(Clhat/Cl + np.log(Cl/Clhat)-1)
    chi2_exp_ell = (2*ell+1)*(np.log(ell+1/2) - polygamma(0,ell+1/2))
    return chi2_ell#-chi2_exp_ell

def prob_TE_ell(tau, taus, theory_arrs, TEhat):
    c = TEhat
    taui = (np.abs(taus - tau)).argmin()
    TT, TE, EE = theory_arrs
    TTi = TT[taui]
    TEi = TE[taui]
    EEi = EE[taui]
    rho = TEi/np.sqrt(TTi*EEi)
    z = (1-rho**2)*np.sqrt(TTi*EEi)
    ell = np.arange(len(TTi))
    N = 2*ell+1
    num = N**((N+1)/2)*abs(c)**((N-1)/2)*np.exp(N*rho*c/z)*kv((N-1)//2, N*abs(c)/z)
    den = 2**((N-1)/2)*np.sqrt(np.pi)*gamma(N/2)*np.sqrt(z)*(TTi*EEi)**(N/4)
    return num/den

if __name__ == '__main__':

    # Define your cosmology (what is not specified will be set to CLASS default parameters)
    params = {
        'output': 'tCl pCl lCl',
        'l_max_scalars': 2500,
        'lensing': 'yes',
        'A_s': 2.3e-9,
        'n_s': 0.965,
        'tau_reio':0.06}
    
    # Create an instance of the CLASS wrapper
    cosmo = Class()
    
    # Set the parameters to the cosmological code
    cosmo.set(params)
    
    # Run the whole code. Depending on your output, it will call the
    # CLASS modules more or less fast. For instance, without any
    # output asked, CLASS will only compute background quantities,
    # thus running almost instantaneously.
    # This is equivalent to the beginning of the `main` routine of CLASS,
    # with all the struct_init() methods called.
    cosmo.compute()
    
    # Access the lensed cl until l=2500
    cls = cosmo.lensed_cl(2500)
    
    # Clean CLASS (the equivalent of the struct_free() in the `main`
    # of CLASS. This step is primordial when running in a loop over different
    # cosmologies, as you will saturate your memory very fast if you ommit
    # it.
    cosmo.struct_cleanup()
    
    # If you want to change completely the cosmology, you should also
    # clean the arguments, otherwise, if you are simply running on a loop
    # of different values for the same parameters, this step is not needed
    cosmo.empty()
    Z = cls['ell']*(cls['ell']+1)/(2*np.pi)*(cosmo.T_cmb()*1e6)**2
    plt.loglog(cls['ell'][2:], cls['ee'][2:]*Z[2:])
    plt.xlabel(r'$\ell$')
    plt.ylabel(r'$D_\ell\ \mathrm{[\mu K^2]}$')
    
    
    plt.figure()
    lmax = 100
    ell = np.arange(lmax+1)
    plt.loglog(ell[2:], get_EE(tau=0.06, lmax=lmax)[2:])
    plt.loglog(ell[2:], get_TE(0.06, lmax=lmax)[2:])
    plt.loglog(ell[2:], -get_TE(0.06, lmax=lmax)[2:], 'C1--')
    plt.xlabel(r'$\ell$')
    plt.ylabel(r'$C_\ell\ \mathrm{[\mu K^2\,sr]}$')
    plt.savefig('theory_curves.png', bbox_inches='tight')
    
    
    
    plt.figure()
    try:
        EE_arr = np.loadtxt('ee.txt')
        TE_arr = np.loadtxt('te.txt')
        TT_arr = np.loadtxt('tt.txt')
        taus = np.loadtxt('taus.txt')
        num = len(EE_arr)
    except IOError:
        #num = 500
        #taus = np.linspace(0.02, 0.1, num)
        taus = np.arange(0.02, 0.1, 0.0001)
        num = len(taus)
        EE_arr = np.zeros((num, lmax+1))
        TE_arr = np.zeros((num, lmax+1))
        TT_arr = np.zeros((num, lmax+1))
        for i in range(num):
            print(i, num)
            TT_arr[i], TE_arr[i], EE_arr[i] = get_all(tau=taus[i], lmax=lmax)
        #for i in range(num):
        #    print(i, num)
        #    EE_arr[i] = get_EE(tau=taus[i], lmax=lmax)
        #
        #for i in range(num):
        #    print(i, num)
        #    TE_arr[i] = get_TE(taus[i], lmax=lmax)
    
        #for i in range(num):
        #    print(i, num)
        #    TT_arr[i] = get_TT(taus[i], lmax=lmax)
    
    cinds = np.linspace(0,1,num)
    Z = ell*(ell+1)/(2*np.pi)
    Z[:2] = 1.
    cm = plt.cm.viridis_r
    cm = plt.cm.cool
    
    
    chi2_eff = (ell.max() - 2 + 1)*1*(2)/2 + 1*(2 + 3 - 1)/24*np.log(ell.max()/2)
    chi2_eff_ell = (2*ell+1)*(np.log(ell+1/2) - polygamma(0,ell+1/2))
    chi2_eff = sum(chi2_eff_ell[2:])
    varchi2_ell = (2*ell+1)*((2*ell+1)*polygamma(1,ell+1/2) -2)
    varchi2 = sum(varchi2_ell[2:])
    
    for i in range(num):
        plt.loglog(ell[2:], (EE_arr[i])[2:], color=cm(cinds[i]))
    sm = plt.cm.ScalarMappable(cmap=cm,
            norm=plt.Normalize(vmin=taus[0], vmax=taus[-1]))
    sm._A = []
    #cbaxes = fig.add_axes([1, 0.15, 0.03, 0.7])
    cbar = plt.colorbar(mappable=sm, label=r'$\tau$, $A_s e^{-2\tau}$ fixed',
            orientation='vertical', ticklocation='right')
    
    i = num //2
    print(taus[i])
    sigma = np.sqrt(2/(2*ell+1))*EE_arr[i]
    plt.fill_between(ell[2:], (EE_arr[i]-sigma)[2:], (EE_arr[i]+sigma)[2:],
            alpha=1, color='k',zorder=-1)
    
    for i in range(num):
        plt.loglog(ell[2:], (TE_arr[i])[2:], color=cm(cinds[i]))
    i = num //2
    print(taus[i])
    sigma = np.sqrt(2/(2*ell+1))*TE_arr[i]
    plt.fill_between(ell[2:], (TE_arr[i]-sigma)[2:], (TE_arr[i]+sigma)[2:],
            alpha=1, color='k',zorder=-1)
    
    
    plt.xlabel(r'$\ell$')
    plt.ylabel(r'$C_\ell^\mathrm{EE}\ [\mathrm{\mu K^2\,sr}]$')
    plt.savefig('cv_v_theoryv.pdf', bbox_inches='tight')
    np.savetxt('ee.txt', EE_arr)
    np.savetxt('te.txt', TE_arr)
    np.savetxt('tt.txt', TT_arr)
    np.savetxt('taus.txt', taus)
    
    plt.figure()
    
    np.random.seed(seed)
    f = (np.abs(taus - 0.06)).argmin()
    Clhat = hp.alm2cl(hp.synalm(EE_arr[f]))
    taus = np.linspace(0.03, 0.09, 21)
    chi2_0 = lnprob_EE_ell(0.06, taus, EE_arr, Clhat)
    for i in range(len(taus)):
        chi2 = lnprob_EE_ell(taus[i], taus, EE_arr, Clhat)
        plt.figure('total')
        plt.semilogx(ell, chi2, color=plt.cm.coolwarm(i/30))
        plt.figure('relative')
        plt.semilogx(ell, chi2-chi2_0, color=plt.cm.coolwarm(i/30))
        print(taus[i], sum(chi2[2:]))
    plt.figure('total')
    plt.xlabel(r'$\ell$')
    plt.ylabel(r'$\ln\mathcal L(\tau|\hat C_\ell^\mathrm{EE})$')
    plt.savefig('single_chi2.png', bbox_inches='tight')
    
    plt.figure('relative')
    plt.xlabel(r'$\ell$')
    plt.ylabel(r'$\ln\mathcal L(\tau|\hat C_\ell^\mathrm{EE}) -\ln\mathcal L(\tau_0|\hat C_\ell^\mathrm{EE})$')
    plt.savefig('single_chi2_relative.png', bbox_inches='tight')
    plt.show()
    
    
    taus = np.loadtxt('taus.txt')
    f = (np.abs(taus - 0.06)).argmin()
    plt.figure()
    chi2s = []
    np.random.seed(seed)
    Clhat = hp.alm2cl(hp.synalm(EE_arr[f]))
    for i in range(len(EE_arr)):
        plt.loglog(ell, EE_arr[i], color=plt.cm.coolwarm(i/len(EE_arr)))
        chi2 = lnprob_EE_ell(taus[i], taus, EE_arr, Clhat)
        chi2s.append(sum(chi2[2:]))
    plt.plot(ell, Clhat, 'k')
    plt.xlabel(r'$ell$')
    plt.ylabel(r'$\hat C_\ell^\mathrm{EE}$')
    plt.savefig('single_ps.png', bbox_inches='tight')
    
    plt.figure()
    chi2s = np.array(chi2s)
    plt.plot(taus, chi2s)
    chi2_exp_ell = (2*ell+1)*(np.log(ell+1/2) - polygamma(0,ell+1/2))
    #plt.axhline(sum(chi2_exp_ell[2:]))
    plt.fill_between(taus, chi2_eff-varchi2**0.5, chi2_eff+varchi2**0.5)
    plt.xlabel(r'$\tau$')
    plt.ylabel(r'$\chi^2$')
    print(taus[np.argmin(chi2s)], chi2s.min())
    plt.savefig('single_tau_chi2.png', bbox_inches='tight')
    
    plt.figure()
    
    plt.plot(taus, np.exp(-(chi2s-chi2s.min())/2))
    plt.axvline(0.06)
    plt.xlabel(r'$\tau$')
    plt.ylabel(r'$e^{-(\chi^2-\chi^2_\mathrm{min})}$')
    
    L = np.exp(-(chi2s-chi2s.min())/2)
    mu = sum(taus*L)/sum(L)
    var = sum(taus**2*L)/sum(L) - mu**2
    plt.title(r'$\hat\tau={0}\pm{1}$'.format(np.round(mu,4), np.round(var**0.5,4)))
    
    chi2_exp_ell = (2*ell+1)*(np.log(ell+1/2) - polygamma(0,ell+1/2))
    plt.savefig('chi2_bestfit.png', bbox_inches='tight')
    #plt.figure('curves')
    #for i in range(len(EE_arr)):
    #    plt.loglog(ell, EE_arr[i], color=plt.cm.coolwarm(i/len(EE_arr)))
    
    tauhats = []
    minchis = []
    
    for s in range(100):
        chi2s = []
        np.random.seed(s)
        Clhat = hp.alm2cl(hp.synalm(EE_arr[f]))
        #plt.figure('curves')
        for i in range(len(EE_arr)):
            chi2 = lnprob_EE_ell(taus[i], taus, EE_arr, Clhat)
            chi2s.append(sum(chi2[2:]))
        chi2_exp = sum(chi2_exp_ell[2:])
        #cind = np.exp((min(chi2s) - chi2_exp)/2)
        #cind = min(cind, 1)
        #print(taus[np.argmin(chi2s)], cind, min(chi2s), chi2_exp)
        #cind = deltachi2/chi2_exp # between 0 to + infty
        #plt.plot(ell, Clhat, color=plt.cm.viridis(cind))
        chi2s = np.array(chi2s)
        #plt.figure('chi2s')
        #plt.plot(taus, chi2s, color=plt.cm.viridis(cind))
        
        #plt.figure('likelihood')
        
        #plt.plot(taus, np.exp(-(chi2s-chi2s.min())/2), color=plt.cm.viridis(cind),
        #        zorder=cind)
        #plt.axvline(0.06)
        tauhats.append(taus[np.argmin(chi2s)])
        minchis.append(min(chi2s))
    
    
    plt.figure()
    plt.hist(tauhats, 20)
    plt.xlabel(r'$\hat\tau$')
    print('np.mean(tauhatsEE), np.std(tauhatsEE)')
    print(np.mean(tauhats), np.std(tauhats))
    plt.title(r'$\hat\tau={0}\pm{1}$'.format(np.round(np.mean(tauhats),4), np.round(np.std(tauhats),4)))
    plt.savefig('tauhat_hist.png', bbox_inches='tight')
    
    
    plt.figure()
    plt.hist(minchis, 20)
    plt.axvline(chi2_eff)
    plt.axvline(chi2_eff - varchi2**0.5)
    plt.axvline(chi2_eff + varchi2**0.5)
    plt.xlabel(r'$\chi^2$')
    print(np.mean(minchis), np.std(minchis))
    plt.savefig('chi2_hist.png', bbox_inches='tight')
    
    
    
    '''
    I more or less have the EE stuff figured out. The TE stuff mostly, I want to
    check that I get the right answer, that I have a good "goodness-of-fit"
    parameter to compare against theory.
    '''
    
    theory_arrs = np.array([TT_arr, TE_arr, EE_arr])
    clth = np.array([TT_arr[f], EE_arr[f], EE_arr[f]*0, TE_arr[f]])
    np.random.seed(seed)
    Clhat = hp.alm2cl(hp.synalm(clth, new=True))
    TEhat = Clhat[3]
    
    taus = np.linspace(0.03, 0.09, 21)
    f = (np.abs(taus - 0.06)).argmin()
    clth = np.array([TT_arr[f], EE_arr[f], EE_arr[f]*0, TE_arr[f]])
    np.random.seed(seed)
    Clhat = hp.alm2cl(hp.synalm(clth, new=True))
    TEhat = Clhat[3]
    chi2_0 = -2*np.log(prob_TE_ell(0.06, taus, theory_arrs, TEhat))
    for i in range(len(taus)):
        chi2 = -2*np.log(prob_TE_ell(taus[i], taus, theory_arrs, TEhat))
        plt.figure('absolute TE')
        plt.semilogx(ell, chi2, color=plt.cm.coolwarm(i/21))
        plt.figure('relative TE')
        plt.semilogx(ell, chi2-chi2_0, color=plt.cm.coolwarm(i/21))
        print(taus[i], sum(chi2[2:]))
    
    plt.figure('absolute TE')
    plt.xlabel(r'$\ell$')
    plt.ylabel(r'$\ln\mathcal L(\tau|\hat C_\ell^\mathrm{TE})$')
    plt.savefig('single_chi2_te.png', bbox_inches='tight')
    
    plt.figure('relative TE')
    plt.xlabel(r'$\ell$')
    plt.ylabel(r'$\ln\mathcal L(\tau|\hat C_\ell^\mathrm{TE})-\ln\mathcal L(\tau_0|\hat C_\ell^\mathrm{TE})$')
    plt.savefig('single_chi2_te_ratio.png', bbox_inches='tight')
    plt.show()
    
    taus = np.loadtxt('taus.txt')
    f = (np.abs(taus - 0.06)).argmin()
    clth = np.array([TT_arr[f], EE_arr[f], EE_arr[f]*0, TE_arr[f]])
    np.random.seed(seed)
    Clhat = hp.alm2cl(hp.synalm(clth, new=True))
    TEhat = Clhat[3]
    chi2s = []
    plt.figure()
    plt.loglog(Clhat[0])
    plt.loglog(Clhat[1])
    plt.loglog(Clhat[3])
    
    plt.loglog(clth[0],color='k')
    plt.loglog(clth[1],color='k')
    plt.loglog(clth[3],color='k')
    
    plt.xlabel(r'$\ell$')
    plt.ylabel(r'$C_\ell\ \mathrm{\mu K^2\,sr}$')
    plt.savefig('all_ps.png', bbox_inches='tight')
    
    
    
    plt.figure()
    for i in range(len(TE_arr)):
        plt.loglog(ell[2:], TT_arr[i][2:], color=plt.cm.coolwarm(i/len(EE_arr)))
        plt.loglog(ell[2:], TE_arr[i][2:], color=plt.cm.coolwarm(i/len(EE_arr)))
        plt.loglog(ell[2:], EE_arr[i][2:], color=plt.cm.coolwarm(i/len(EE_arr)))
        chi2 = -2*np.log(prob_TE_ell(taus[i], taus, theory_arrs, TEhat))
        chi2s.append(sum(chi2[2:]))
    plt.plot(ell, TEhat, 'k')
    plt.xlabel(r'$\ell$')
    plt.ylabel(r'$C_\ell$')
    plt.savefig('tehat_v_theory.png', bbox_inches='tight')
    
    plt.figure()
    chi2s = np.array(chi2s)
    plt.plot(taus, chi2s)
    plt.xlabel(r'$\tau$')
    plt.ylabel(r'$-2\ln(\mathcal L/\mathcal L_\mathrm{max})$')
    print(taus[np.argmin(chi2s)], chi2s.min())
    plt.xlim([0.04, 0.08])
    plt.ylim([-1, 20])
    plt.savefig('chi2_te.png', bbox_inches='tight')
    
    plt.figure()
    
    plt.plot(taus, np.exp(-(chi2s-chi2s.min())/2))
    plt.axvline(0.06)
    plt.xlabel(r'$\tau$')
    plt.ylabel(r'$e^{-(\chi^2-\chi^2_\mathrm{min})}$')
    
    L = np.exp(-(chi2s-chi2s.min())/2)
    mu = sum(taus*L)/sum(L)
    var = sum(taus**2*L)/sum(L) - mu**2
    plt.title(r'$\hat\tau={0}\pm{1}$'.format(np.round(mu,4), np.round(var**0.5,4)))
    plt.savefig('muhat_te.png', bbox_inches='tight')
    
    tauhats = []
    minchis = []
    
    for s in range(100):
        print(s)
        chi2s = []
        np.random.seed(s)
        Clhat = hp.alm2cl(hp.synalm(clth, new=True))
        TEhat = Clhat[3]
        #plt.figure('curves')
        for i in range(len(EE_arr)):
            chi2 = -2*np.log(prob_TE_ell(taus[i], taus, theory_arrs, TEhat))
            chi2s.append(sum(chi2[2:]))
        chi2s = np.array(chi2s)
        tauhats.append(taus[np.argmin(chi2s)])
        minchis.append(min(chi2s))
    
    
    plt.figure()
    plt.hist(tauhats, 20)
    plt.xlabel(r'$\hat\tau$')
    print('np.mean(tauhatsTE), np.std(tauhatsTE)')
    print(np.mean(tauhats), np.std(tauhats))
    plt.title(r'$\hat\tau={0}\pm{1}$'.format(np.round(np.mean(tauhats),4), np.round(np.std(tauhats),4)))
    plt.savefig('tauhats_te.png', bbox_inches='tight')
    
    minchis = np.array(minchis)
    minchis = minchis[np.isfinite(minchis)]
    plt.figure()
    plt.hist(minchis, 20)
    plt.xlabel(r'$-2\ln\mathcal L$')
    print(np.mean(minchis), np.std(minchis))
    plt.savefig('te_minchi.png', bbox_inches='tight')
    plt.close('all')
    plt.show()
    
    
    
    '''
    Simultaneous versus joint fits.
    '''
    taus = np.loadtxt('taus.txt')
    f = (np.abs(taus - 0.06)).argmin()
    clth = np.array([TT_arr[f], EE_arr[f], EE_arr[f]*0, TE_arr[f]])
    np.random.seed(seed)
    Clhat = hp.alm2cl(hp.synalm(clth, new=True))
    TEhat = Clhat[3]
    EEhat = Clhat[1]
    plt.figure()
    plt.loglog(Clhat[0])
    plt.loglog(Clhat[1])
    plt.loglog(Clhat[3])
    
    plt.loglog(clth[0],color='k')
    plt.loglog(clth[1],color='k')
    plt.loglog(clth[3],color='k')
    
    
    plt.figure()
    chi2TEs = []
    chi2EEs = []
    for i in range(len(TE_arr)):
        plt.loglog(ell[2:], TE_arr[i][2:], color=plt.cm.coolwarm(i/len(EE_arr)))
        plt.loglog(ell[2:], TT_arr[i][2:], color=plt.cm.coolwarm(i/len(EE_arr)))
        plt.loglog(ell[2:], EE_arr[i][2:], color=plt.cm.coolwarm(i/len(EE_arr)))
        chi2TE = -2*np.log(prob_TE_ell(taus[i], taus, theory_arrs, TEhat))
        chi2EE = lnprob_EE_ell(taus[i], taus, EE_arr, EEhat)
        chi2TEs.append(sum(chi2TE[2:]))
        chi2EEs.append(sum(chi2EE[2:]))
    plt.plot(ell[2:], TEhat[2:], 'C1o')
    plt.plot(ell[2:], EEhat[2:], 'C2o')
    plt.plot(ell[2:], Clhat[0][2:], 'C0o')
    plt.xlabel(r'$\ell$')
    plt.ylabel(r'$C_\ell^\mathrm{EE}\ [\mathrm{\mu K^2\,sr}]$')
    sm = plt.cm.ScalarMappable(cmap=plt.cm.coolwarm,
            norm=plt.Normalize(vmin=taus.min(), vmax=taus.max()))
    # fake up the array of the scalar mappable. Urgh...
    sm._A = []
    plt.colorbar(sm, label=r'$\tau$')
    #plt.show()
    plt.savefig('all_data.png', bbox_inches='tight')
    
    plt.figure()
    chi2EEs = np.array(chi2EEs)
    chi2TEs = np.array(chi2TEs)
    chi2s = chi2EEs + chi2TEs
    plt.plot(taus, chi2EEs - chi2EEs.min(), label=r'EE')
    plt.plot(taus, chi2TEs - chi2TEs.min(), label=r'TE')
    plt.plot(taus, chi2EEs+chi2TEs - chi2EEs.min()-chi2TEs.min(), label=r'TE+EE')
    plt.xlabel(r'$\tau$')
    plt.ylabel(r'$-2\ln(\mathcal L/\mathcal L_\mathrm{max})$')
    plt.xlim([0.04, 0.08])
    plt.ylim([-1, 20])
    plt.legend(loc='best')
    #plt.show()
    plt.savefig('comparitive_chi2s.png', bbox_inches='tight')
    
    plt.figure()
    
    plt.axvline(0.06)
    plt.xlabel(r'$\tau$')
    plt.ylabel(r'$e^{-(\chi^2-\chi^2_\mathrm{min})}$')
    #plt.show()
    
    L = np.exp(-(chi2s-chi2s.min())/2)
    inds = np.isfinite(L)
    mu = sum(taus[inds]*L[inds])/sum(L[inds])
    var = sum(taus[inds]**2*L[inds])/sum(L[inds]) - mu**2
    print(mu, var**0.5, 'All')
    #plt.title(r'$\hat\tau={0}\pm{1}$'.format(np.round(mu,4), np.round(var**0.5,4)))
    plt.plot(taus, np.exp(-(chi2s-chi2s.min())/2),
            label=r'TE+EE, ${0}\pm{1}$'.format(np.round(mu,4),np.round(var**0.5,4)))
    
    L = np.exp(-(chi2EEs-chi2EEs.min())/2)
    inds = np.isfinite(L)
    mu = sum(taus[inds]*L[inds])/sum(L[inds])
    var = sum(taus[inds]**2*L[inds])/sum(L[inds]) - mu**2
    print(mu, var**0.5, 'EE')
    plt.plot(taus, np.exp(-(chi2EEs-chi2EEs.min())/2),
            label=r'EE, ${0}\pm{1}$'.format(np.round(mu,4),np.round(var**0.5,4)))
    
    L = np.exp(-(chi2TEs-chi2TEs.min())/2)
    inds = np.isfinite(L)
    mu = sum(taus[inds]*L[inds])/sum(L[inds])
    var = sum(taus[inds]**2*L[inds])/sum(L[inds]) - mu**2
    print(mu, var**0.5, 'TE')
    plt.plot(taus, np.exp(-(chi2TEs-chi2TEs.min())/2),
            label=r'TE, ${0}\pm{1}$'.format(np.round(mu,4),np.round(var**0.5,4)))
    plt.legend(loc='best')
    #plt.show()
    plt.savefig('comparative_probabilities.png', bbox_inches='tight')
    
    tauhats = []
    minchis = []
    tauhatsEE = []
    minchisEE = []
    tauhatsTE = []
    minchisTE = []
    
    '''
    for s in np.arange(2000,3000):
        chi2EEs = []
        chi2TEs = []
        np.random.seed(s)
        Clhat = hp.alm2cl(hp.synalm(clth, new=True))
        TEhat = Clhat[3]
        EEhat = Clhat[1]
        #plt.figure('curves')
        #plt.loglog(Clhat[1], color='C0', alpha=0.1)
        #plt.loglog(Clhat[3], color='C1', alpha=0.1)
        for i in range(len(EE_arr)):
            chi2TE = -2*np.log(prob_TE_ell(taus[i], taus, theory_arrs, TEhat))
            chi2TEs.append(sum(chi2TE[2:]))
            chi2EE = lnprob_EE_ell(taus[i], taus, theory_arrs[2], EEhat)
            chi2EEs.append(sum(chi2EE[2:]))
        chi2EEs = np.array(chi2EEs)
        chi2TEs = np.array(chi2TEs)
        chi2s = chi2EEs + chi2TEs
        tauhatsEE.append(taus[np.argmin(chi2EEs)])
        minchisEE.append(min(chi2EEs))
        tauhatsTE.append(taus[np.argmin(chi2TEs)])
        minchisTE.append(min(chi2TEs))
        tauhats.append(taus[np.argmin(chi2s)])
        minchis.append(min(chi2s))
    
    
    plt.figure()
    bins = np.linspace(0.04, 0.09, 50)
    plt.xlabel(r'$\hat\tau$')
    plt.title(r'$\hat\tau={0}\pm{1}$'.format(np.round(np.mean(tauhats),4), np.round(np.std(tauhats),4)))
    plt.hist(tauhatsTE, bins, label=r'TE', alpha=0.5)
    plt.hist(tauhatsEE, bins, label=r'EE', alpha=0.5)
    plt.hist(tauhats, bins, label=r'TE+EE', alpha=0.5)
    print('np.std(tauhatsTE), np.std(tauhatsEE), np.std(tauhats)')
    print(np.std(tauhatsTE), np.std(tauhatsEE), np.std(tauhats))
    plt.legend(loc='best')
    
    minchis = np.array(minchis)
    minchis = minchis[np.isfinite(minchis)]
    plt.savefig('tauhats_comp.png', bbox_inches='tight')
    
    plt.figure()
    plt.hist(minchis, 20)
    plt.xlabel(r'$-2\ln\mathcal L$')
    plt.title('Goodness of fit for TE+EE')
    print(np.mean(minchis), np.std(minchis))
    #plt.close('all')
    plt.savefig('ee_te_chi2.png', bbox_inches='tight')
    
    minchisTE = np.array(minchisTE)
    minchisTE = minchisTE[np.isfinite(minchisTE)]
    plt.figure()
    plt.hist(minchisTE, 20)
    plt.xlabel(r'$-2\ln\mathcal L$')
    plt.title('Goodness of fit for TE')
    plt.savefig('te_chi2.png', bbox_inches='tight')
    print(np.mean(minchis), np.std(minchis))
    
    minchisEE = np.array(minchisEE)
    minchisEE = minchisEE[np.isfinite(minchisEE)]
    plt.figure()
    plt.hist(minchisEE, 20)
    plt.xlabel(r'$-2\ln\mathcal L$')
    plt.title('Goodness of fit for EE')
    print(np.mean(minchis), np.std(minchis))
    plt.savefig('ee_chi2.png', bbox_inches='tight')
    plt.show()
    '''
