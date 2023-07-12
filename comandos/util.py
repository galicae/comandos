# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_util.ipynb.

# %% auto 0
__all__ = ['procrustes', 'grouped_obs_mean', 'grouped_obs_present', 'grouped_obs_percent', 'find_center', 'map_fine_to_coarse']

# %% ../nbs/00_util.ipynb 3
import os
from pathlib import Path
from typing import Union
from urllib.error import HTTPError
from urllib.request import urlopen

import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import scanpy as sc
from matplotlib.patches import Patch
from scipy.stats import gaussian_kde
from tqdm.auto import tqdm

# %% ../nbs/00_util.ipynb 6
def procrustes(
    x: str,  # input string
    appropriate_length: int = 50,  # desired length
    pad_with: str = " ",  # character to pad with
    side: str = "right",  # which side to pad on ("left", "right")
) -> str:  # string with desired length
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

# %% ../nbs/00_util.ipynb 10
def grouped_obs_mean(
    adata: ad.AnnData,  # AnnData object to analyse
    group_key: str,  # `.obs` category to group by
    layer: Union[str, None] = None,  # layer to use. If none, use `.X`
) -> pd.DataFrame:  # a groups$\times$genes dataframe with the average expression
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

# %% ../nbs/00_util.ipynb 17
def grouped_obs_present(adata, group_key, layer: Union[str, None] = None):
    """
    Helper function to calculate how many cells express each gene per group in an `AnnData` object.

    Parameters
    ----------
    adata : AnnData
        AnnData object to analyse.
    group_key : str
        `.obs` category to group by.
    layer : Union[str, None], optional
        Layer to use. If none, use `.X`.

    Returns
    -------
    pd.DataFrame
        A clusters$\times$genes dataframe with the number of expressing cells per cluster.
    """
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

# %% ../nbs/00_util.ipynb 24
def grouped_obs_percent(adata, group_key, layer: Union[str, None] = None):
    """
    Helper function to calculate what percentage of cells express each gene per group in an
    `AnnData` object.

    Parameters
    ----------
    adata : AnnData
        AnnData object to analyse.
    group_key : str
        `.obs` category to group by.
    layer : str, optional
        Layer to use. If none, use `.X`.

    Returns
    -------
    pd.DataFrame
        A clusters$\times$genes dataframe with the percentage of expressing cells per cluster.
    """
    num_expressing = grouped_obs_present(adata, group_key, layer=layer)
    no_cells_per_cluster = adata.obs[group_key].value_counts()
    return num_expressing / no_cells_per_cluster

# %% ../nbs/00_util.ipynb 28
def find_center(coords):
    """
    A function that estimates a Gaussian probability density for the input data and returns the
    mode. From https://stackoverflow.com/a/60185876.

    Parameters
    ----------
    coords : np.ndarray
        A 2D array with X, Y-coordinates from xs, ys.

    Returns
    -------
    float
        The X-coordinate of the mode.
    float
        The Y-coordinate of the mode.
    """
    kernel = gaussian_kde(coords.T)
    min_x, min_y = np.min(coords, axis=0)
    max_x, max_y = np.max(coords, axis=0)
    grid_xs, grid_ys = np.mgrid[min_x:max_x:50j, min_y:max_y:50j]
    positions = np.vstack(
        [grid_xs.ravel(), grid_ys.ravel()]
    )  # 2-dim array with X, Y-coordinates from xs, ys
    Z = np.reshape(kernel(positions).T, grid_xs.shape)  # get densities

    idx = np.unravel_index(np.argmax(Z), Z.shape)
    return grid_xs[idx], grid_ys[idx]

# %% ../nbs/00_util.ipynb 34
def map_fine_to_coarse(
    sm, species, fine, coarse=None, plot=sc.pl.umap, include_coarse=False
):
    """
    Extract the mapping of fine to coarse clusters from a SAMap object.

    Parameters
    ----------
    sm : sm.maps.SAMAP
        SAMAP object to process.
    species : str
        Species ID of the correct SAM object.
    fine : str
        Fine clustering slot name.
    coarse : str, optional
        Coarse clustering slot name. If None, use the same as `fine`, mapping each cluster to
        itself. (default: `None`).
    plot : function, optional
        Plotting function to use; this will correctly set the colors (default: `sc.pl.umap`).
    include_coarse : bool, optional
        If True, preface the fine cluster names with the coarse cluster names (default: `False`).

    Returns
    -------
    fine_to_coarse: pd.DataFrame
        A dataframe with the mapping of fine to coarse clusters.
    lut: dict
        A dictionary with the colors for each coarse cluster.
    handles: list
        A list of `matplotlib.patches.Patch` objects with the colors for each coarse cluster.
    """
    if coarse is None:
        coarse = fine

    fine_to_coarse = (
        sm.sams[species]
        .adata.obs[[fine, coarse]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    plt.ioff()
    _fig = plot(sm.sams[species].adata, color=coarse, return_fig=True)
    plt.close(_fig)
    plt.ion()

    lut = dict(
        zip(
            sm.sams[species].adata.obs[coarse].cat.categories,
            sm.sams[species].adata.uns[coarse + "_colors"],
        )
    )
    handles = [Patch(facecolor=lut[name]) for name in lut]
    if include_coarse:
        fine_to_coarse[fine] = (
            species
            + "_"
            + fine_to_coarse[coarse].astype(str)
            + "_"
            + fine_to_coarse[fine].astype(str)
        )
    else:
        fine_to_coarse[fine] = species + "_" + fine_to_coarse[fine].astype(str)
    return fine_to_coarse, lut, handles
