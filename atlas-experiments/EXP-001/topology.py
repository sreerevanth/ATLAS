from gtda.homology import VietorisRipsPersistence

def compute_persistence(point_clouds, homology_dimensions=(0, 1)):
    # point_clouds is a list of arrays (n_samples, n_features)
    vr = VietorisRipsPersistence(homology_dimensions=homology_dimensions)
    diagrams = vr.fit_transform(point_clouds)
    return diagrams
