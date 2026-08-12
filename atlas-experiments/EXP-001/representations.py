from gtda.diagrams import PersistenceLandscape, PersistenceImage, BettiCurve, PersistenceEntropy

def to_landscape(diagrams):
    pl = PersistenceLandscape(n_layers=1, n_bins=100)
    return pl.fit_transform(diagrams)

def to_image(diagrams):
    pi = PersistenceImage(sigma=0.1, n_bins=10, weight_function=None)
    return pi.fit_transform(diagrams)

def to_betti(diagrams):
    bc = BettiCurve(n_bins=100)
    return bc.fit_transform(diagrams)

def to_entropy(diagrams):
    pe = PersistenceEntropy()
    return pe.fit_transform(diagrams)
