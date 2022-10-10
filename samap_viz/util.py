# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_util.ipynb.

# %% auto 0
__all__ = ['procrustes', 'grouped_obs_mean', 'grouped_obs_present', 'grouped_obs_percent']

# %% ../nbs/00_util.ipynb 6
def procrustes(x:str, # input string
               appropriate_length:int=50, # desired length
               pad_with:str=" ", # character to pad with
               side:str="right" # which side to pad on ("left", "right")
              )->str: # string with desired length
    "A function to regulate string length."
    if len(x) > appropriate_length:
        return x[:appropriate_length]
    if len(x) < appropriate_length:
        to_pad = appropriate_length - len(x)
        pad = "".join([pad_with] * to_pad)
        if side == "right":
            x = x + pad
        elif side == "left":
            x = pad + x
        else:
            print("Invalid side argument; returning string as-is.")
    return x

# %% ../nbs/00_util.ipynb 11
def grouped_obs_mean(adata:ad.AnnData, # AnnData object to analyse
                        group_key:str, # `.obs` category to group by
                        layer:str=None # layer to use. If none, use `.X`
                    )->pd.DataFrame: # a groups$\times$genes dataframe with the average expression
    "Helper function to calculate average expression per group in an `AnnData` object."
    if layer is not None:
        getX = lambda x: x.layers[layer]
    else:
        getX = lambda x: x.X

    grouped = adata.obs.groupby(group_key)
    out = pd.DataFrame(
        np.zeros((adata.shape[1], len(grouped)), dtype=np.float64),
        columns=list(grouped.groups.keys()),
        index=adata.var_names,
    )

    for group, idx in grouped.indices.items():
        X = getX(adata[idx])
        out[group] = np.ravel(X.mean(axis=0, dtype=np.float64))
    return out

# %% ../nbs/00_util.ipynb 19
def grouped_obs_present(adata:ad.AnnData, # AnnData object to analyse
                        group_key:str, # `.obs` category to group by
                        layer:str=None # layer to use. If none, use `.X`
                       )->pd.DataFrame: # a groups$\times$genes dataframe with the number of expressing cells
    "Helper function to calculate how many cells express each gene per group in an `AnnData` object."
    if layer is not None:
        getX = lambda x: x.layers[layer]
    else:
        getX = lambda x: x.X

    grouped = adata.obs.groupby(group_key)
    out = pd.DataFrame(
        np.zeros((adata.shape[1], len(grouped)), dtype=np.float64),
        columns=list(grouped.groups.keys()),
        index=adata.var_names,
    )

    for group, idx in grouped.indices.items():
        X = getX(adata[idx])
        out[group] = np.ravel((X > 0).sum(axis=0, dtype=np.float64))
    return out

# %% ../nbs/00_util.ipynb 26
def grouped_obs_percent(adata:ad.AnnData, # AnnData object to analyse
                        group_key:str, # `.obs` category to group by
                        layer:str=None # layer to use. If none, use `.X`
                       )->pd.DataFrame: # a groups$\times$genes dataframe with the number of expressing cells
    "Helper function to calculate how many cells express each gene per group in an `AnnData` object."
    num_expressing = grouped_obs_present(adata, group_key, layer=layer)
    no_cells_per_cluster = adata.obs[group_key].value_counts()
    return num_expressing / no_cells_per_cluster
