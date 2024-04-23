# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_plot.ipynb.

# %% auto 0
__all__ = ['highlighted_dimplot', 'highlighted_heatmap', 'annotated_heatmap', 'paired_dotplot']

# %% ../nbs/02_plot.ipynb 3
import os
import pickle
from typing import Any, Tuple, Union

import scanpy as sc
import anndata as ad
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import Colormap
import numpy as np
import pandas as pd
import plotly
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
import seaborn as sns
from matplotlib.patches import Circle, Rectangle
from plotly.subplots import make_subplots
from samap.mapping import SAMAP

from . import dotplot_util as du
from . import genes, util

# %% ../nbs/02_plot.ipynb 6
def highlighted_dimplot(
    adata: ad.AnnData,
    species: str,
    clustering: str,
    cluster: str,
    embedding: str = "X_umap",
    highlight: str = "red",
    figsize: tuple = (10, 10),
    save: Union[str, None] = None,
):
    """
    Plot a low-dimensional embedding and highlight a chosen cluster with a superimposed circle.

    Parameters
    ----------
    adata : anndata.AnnData
        AnnData object to plot.
    species : str
        Species name. Will be used in the title, and removed from the cluster names if present.
    clustering : str
        Clustering to plot. Must be present in `adata.obs`.
    cluster : str
        Cluster to highlight.
    embedding : str, optional
        Embedding to plot (default: "X_umap").
    highlight : str, optional
        Color of the circle (default: "red").
    figsize : tuple, optional
        Figure size (default: (10, 10)).
    save : str, optional
        Path to save the figure (default: None).

    Returns
    -------
    None
    """
    cluster_cells = adata.obs[clustering] == cluster.replace(species + "_", "")
    coords = adata.obsm[embedding][cluster_cells]
    cx, cy = util.find_center(coords)
    radius = np.mean(np.std(coords, axis=0))
    if radius < 0.5:
        radius = 0.5
    elif radius > 2:
        radius = 2
    _fig, ax = plt.subplots(figsize=figsize)
    g = sc.pl.embedding(
        adata,
        basis=embedding,
        color=clustering,
        legend_loc="on data",
        ax=ax,
        show=False,
        title=species,
    )
    g.axes.add_patch(
        Circle((cx, cy), radius, linewidth=3, facecolor="none", edgecolor=highlight)
    )
    g.set_title(species)
    if save is not None:
        plt.savefig(save)

# %% ../nbs/02_plot.ipynb 13
def highlighted_heatmap(to_plot, celltype_from, celltype_to, figheight=20, save=None):
    """
    Plot a heatmap of pairwise similarities between cell types, with a red box highlighting the
    query cell type.

    Parameters
    ----------
    to_plot : pd.DataFrame
        A dataframe of pairwise similarities between cell types.
    celltype_from : str
        Cell type of the query species to highlight. Must be in `to_plot.columns`.
    celltype_to : str
        Cell type of the target species to highlight. Must be in `to_plot.index`.
    figheight : float, optional
        Height of the resulting plot in inches. Width will be calculated automatically (default:
        20).
    save : str, optional
        Path to result figure; if None, the figure will be plotted but not saved (default: None).

    Returns
    -------
    None
    """
    figwidth = int(to_plot.shape[0] / to_plot.shape[1] * figheight)
    y = np.where(to_plot.columns == celltype_from)[0][0]
    x = np.where(to_plot.index == celltype_to)[0][0]

    fig, ax = plt.subplots(figsize=(figwidth, figheight))
    g = sns.heatmap(to_plot.T, ax=ax, cmap="mako")

    ax = g.axes
    ax.add_patch(Rectangle((x, y), 1, 1, fill=False, edgecolor="red", lw=3))
    ax.hlines(y + 0.5, 0, x, colors="red", linestyles="dashed")
    ymax = to_plot.shape[1]
    ax.vlines(x + 0.5, y + 1, ymax, colors="red", linestyles="dashed")
    if save is not None:
        plt.savefig(save)

# %% ../nbs/02_plot.ipynb 16
def _plot_clustermap(
    similarity,
    query_map,
    target_map,
    query_handles,
    target_handles,
    query_lut,
    target_lut,
    query_species,
    target_species,
    query_clustering,
    target_clustering,
    query_coarse,
    target_coarse,
    figsize,
    save,
    **kwargs,
):
    if figsize is None:
        figsize = np.array(similarity.shape) / 3

    sns.clustermap(
        similarity,
        cmap="magma_r",
        figsize=figsize,
        col_cluster=None,
        row_cluster=None,
        dendrogram_ratio=0.1,
        colors_ratio=0.02,
        cbar_pos=(0.04, 0.75, 0.02, 0.15),
        row_colors=target_map.set_index(target_clustering)[target_coarse],
        col_colors=query_map.set_index(query_clustering)[query_coarse],
        linecolor="black",
        linewidths=0.5,
        **kwargs,
    )

    query_legend = plt.legend(
        query_handles,
        query_lut,
        title=f"{query_species}\nmajor cell types",
        bbox_to_anchor=(0.07, 0.7),
        bbox_transform=plt.gcf().transFigure,
        loc="upper right",
    )
    plt.gca().add_artist(query_legend)

    plt.legend(
        target_handles,
        target_lut,
        title=f"{target_species}\nmajor cell types",
        bbox_to_anchor=(0.06, 0.5),
        bbox_transform=plt.gcf().transFigure,
        loc="upper right",
    )

    if save is not None:
        plt.savefig(save)

# %% ../nbs/02_plot.ipynb 17
def _plotly_clustermap(
    similarity,
    query_map,
    target_map,
    query_clustering,
    target_clustering,
    query_coarse,
    target_coarse,
    figsize,
    save,
    dpi=300,
):
    query_colors = query_map.set_index(query_clustering)
    query_colors["cc"] = pd.Categorical(query_colors[query_coarse])
    query_colors["code"] = query_colors.cc.cat.codes
    # query_info = query_colors.drop(columns=["code", "cc"]).loc[similarity.columns]
    query_info = query_map.set_index("Cluster").loc[similarity.columns]
    query_colors = query_colors.drop(columns=[query_coarse, "cc"]).loc[
        similarity.columns
    ]

    target_colors = target_map.set_index(target_clustering)
    target_colors["cc"] = pd.Categorical(target_colors[target_coarse])
    target_colors["code"] = target_colors.cc.cat.codes
    target_info = target_colors.drop(columns=["code", "cc"]).loc[similarity.index]
    target_colors = target_colors.drop(columns=[target_coarse, "cc"]).loc[
        similarity.index
    ]

    make_subplots(
        rows=2,
        cols=2,
        column_widths=[0.95, 0.05],
        row_heights=[0.95, 0.05],
        vertical_spacing=0.02,
        shared_xaxes=True,
        shared_yaxes=True,
    )

    data_heatmap = go.Heatmap(
        z=similarity.T, x=similarity.index, y=similarity.columns, colorscale="magma_r"
    )

    query_annot = go.Heatmap(
        z=query_colors.loc[similarity.columns],
        text=query_info,
        hoverinfo="text",
        colorscale="Rainbow",
        showscale=False,
        xaxis="x2",
        yaxis="y",
    )
    target_annot = go.Heatmap(
        z=target_colors.loc[similarity.index].T,
        text=target_info.T,
        hoverinfo="text",
        colorscale="Rainbow",
        showscale=False,
        xaxis="x",
        yaxis="y2",
    )

    data = [data_heatmap, query_annot, target_annot]

    layout = go.Layout(
        xaxis=dict(domain=[0, 0.95]),
        yaxis=dict(domain=[0, 0.95]),
        xaxis2=dict(domain=[0.95, 1], showticklabels=False),
        yaxis2=dict(domain=[0.95, 1], showticklabels=False),
    )
    fig = go.Figure(data=data, layout=layout)

    if figsize is not None:
        fig.update_layout(width=figsize[0] * dpi, height=figsize[1] * dpi)

    if save is not None:
        fig.write_html(save + ".html")
        fig.write_json(save + ".json")

    return fig

# %% ../nbs/02_plot.ipynb 18
def annotated_heatmap(
    sm: SAMAP,  # SAMAP object
    similarity: pd.DataFrame,  # Similarity matrix. Contains query species clusters as columns and target species clusters as rows.
    query_species: str,  # Query species ID. Will be used in the title. Should prepend the similarity matrix column names.
    target_species: str,  # Target species ID. Will be used in the title. Should prepend the similarity matrix row names.
    query_clustering: str,  # Query species clustering. Must be present in `sm.sams[query_species].adata.obs`.
    target_clustering: str,  # Target species clustering. Must be present in `sm.sams[target_species].adata.obs`.
    query_coarse: Union[
        str, None
    ] = None,  # Query species coarse clustering. Must be present in `sm.sams[query_species].adata.obs`. If None, will be set to `query_clustering` (default: None).
    target_coarse: Union[
        str, None
    ] = None,  # Target species coarse clustering. Must be present in `sm.sams[target_species].adata.obs`. If None, will be set to `target_clustering` (default: None).
    interactive: bool = False,  # If True, will return a plotly figure. Otherwise, will return a matplotlib figure (default: False).
    figsize: Union[
        Tuple[float, float], None
    ] = None,  # Figure size. If None, will be guessed from the size of the similarity matrix (default: None).
    save: Union[
        str, None
    ] = None,  # If not None, will save the figure to the specified path (default: None).
    **kwargs: Any,  # Additional arguments to pass to `seaborn.heatmap` (matplotlib) or `plotly.graph_objects.Figure` (plotly). Among them: dpi (int), which is only used if `interactive=True` to set the figure size in pixels.
) -> Union[
    None, plotly.graph_objects.Figure
]:  # return None if `interactive=False`, otherwise return a plotly figure.
    "Plot the similarity matrix as an annotated heatmap."
    if query_coarse is None:
        query_coarse = query_clustering
    if target_coarse is None:
        target_coarse = target_clustering

    query_map, query_lut, query_handles = util.map_fine_to_coarse(
        sm, query_species, query_clustering, query_coarse
    )
    target_map, target_lut, target_handles = util.map_fine_to_coarse(
        sm, target_species, target_clustering, target_coarse
    )

    query_map[query_coarse] = query_map[query_coarse].replace(to_replace=query_lut)
    target_map[target_coarse] = target_map[target_coarse].replace(to_replace=target_lut)

    if not interactive:
        return _plot_clustermap(
            similarity,
            query_map,
            target_map,
            query_handles,
            target_handles,
            query_lut,
            target_lut,
            query_species,
            target_species,
            query_clustering,
            target_clustering,
            query_coarse,
            target_coarse,
            figsize,
            save,
            **kwargs,
        )
    else:
        return _plotly_clustermap(
            similarity,
            query_map,
            target_map,
            query_clustering,
            target_clustering,
            query_coarse,
            target_coarse,
            figsize,
            save,
            **kwargs,
        )

# %% ../nbs/02_plot.ipynb 31
def paired_dotplot(
    query: ad.AnnData,  # query species AnnData object
    target: ad.AnnData,  # target species AnnData object
    connections: np.array,  # array of connected genes. Each row has at least two columns containing the query species gene and corresponding target species gene, and optionally their connection strength. Genes are allowed to be repeated on both sides.
    query_clustering: str,  # `.obs` column in the query AnnData object containing the query species clustering.
    target_clustering: str,  # `.obs` column in the target AnnData object containing the target species clustering.
    query_species: str,  # query species name. Will only be used in the title, so does not have to conform with the query species ID in the similarity matrix/SAMap object.
    target_species: str,  # target species name. Will only be used in the title, so does not have to conform with the target species ID in the similarity matrix/SAMap object.
    query_cluster: Union[
        str, None
    ] = None,  # the cell type/cluster of the query species that is being compared (default: None).
    target_cluster: Union[
        str, None
    ] = None,  # the cell type/cluster of the target species that is being compared (default: None).
    pad: bool = True,  # whether to pad the gene names with spaces to make them all of a similar length (default: True).
    x_offset: float = 1,  # Number of inches to add to the horizontal size of the canvas (default: 1).
    y_offset: float = 0,  # Number of inches to add to the vertical size of the canvas (default: 0).
    grid_offset: float = 30,  # Grid segments to add between the two dotplots. Might be useful if the gene names are not legible/lines overlap (default: 30).
    query_gene_names: Union[
        str, None
    ] = None,  # `.var` column that holds unique gene names for the query species (default: None).
    target_gene_names: Union[
        str, None
    ] = None,  # `.var` column that holds unique gene names for the target species (default: None).
    output: str = "./paired_dotplot.png",  # path to save the plot to (default: "./paired_dotplot.png").
    center: bool = True,  # whether to center the dotplot (default: True).
    title: Union[str, None] = None,  # overall title of the plot (default: None).
    title_font_size: float = 16,  # font size of the overall plot title (default: 16).
    scale: bool = False,  # whether to scale the expression values to be between 0 and 1 for each gene (default: False).
    cmap: Colormap = "magma_r",  # colormap to use for the dotplot (default: "viridis").
    layer: Union[
        str, None
    ] = None,  # layer : Union[str, None], optional The layer to use for the average expression calculation. If not specified, it will use the `.X` slot of the `AnnData` objects. It is vital to set this correctly to avoid calculating average expression on log1p-transformed data (default: None).
) -> None:
    # make a local copy, since connections is mutable
    # and we might change it inadvertently
    links = connections.copy()
    # demultiplex the connected genes
    query_genes = du.unique_genes(links[:, 0])
    target_genes = du.unique_genes(links[:, 1])

    # get average expression for each dot
    query_avg_expr, target_avg_expr = du.get_dot_color(
        query,
        target,
        query_clustering,
        target_clustering,
        query_genes=query_genes,
        target_genes=target_genes,
        query_gene_names=query_gene_names,
        target_gene_names=target_gene_names,
        layer=layer,
    )
    # scale the expression values to be between 0 and 1 for each gene
    if scale:
        query_avg_expr = util.rescale(query_avg_expr.T).fillna(0).T
        target_avg_expr = util.rescale(target_avg_expr.T).fillna(0).T
    # get expression percentage for each dot
    query_perc_expr, target_perc_expr = du.get_dot_size(
        query,
        target,
        query_clustering,
        target_clustering,
        query_genes=query_genes,
        target_genes=target_genes,
        query_gene_names=query_gene_names,
        target_gene_names=target_gene_names,
    )

    # replace gene IDs with gene names, if so chosen
    if query_gene_names is not None:
        for i, gene in enumerate(links[:, 0]):
            if gene is not None:
                links[i, 0] = query.var[query_gene_names].loc[gene]
        query_genes = du.unique_genes(links[:, 0])
    if target_gene_names is not None:
        for i, gene in enumerate(links[:, 1]):
            if gene is not None:
                links[i, 1] = target.var[target_gene_names].loc[gene]
        target_genes = du.unique_genes(links[:, 1])

    # pad gene names with spaces to make plotting more beautiful
    if pad:
        query_genes = np.array(
            [util.procrustes(g[:50], 50, side="right") for g in query_genes]
        )
        target_genes = np.array(
            [util.procrustes(g[:50], 50, side="left") for g in target_genes]
        )
        for i, g in enumerate(links[:, 0]):
            if g is not None:
                links[i, 0] = util.procrustes(g[:50], 50, side="right")
        for i, g in enumerate(links[:, 1]):
            if g is not None:
                links[i, 1] = util.procrustes(g[:50], 50, side="left")

    # keep track of what the clusters are:
    query_clusters = np.sort(query_avg_expr.index.values)
    target_clusters = np.sort(target_avg_expr.index.values)

    # reorder alphabetically so that both tables are oriented exactly the same way
    query_perc_expr = query_perc_expr.loc[query_clusters]
    query_avg_expr = query_avg_expr.loc[query_clusters]
    target_perc_expr = target_perc_expr.loc[target_clusters]
    target_avg_expr = target_avg_expr.loc[target_clusters]

    # highlight target and query clusters to make inspecting the dotplot easier
    query_clust_col = du.highlight_cluster(query_clusters, query_cluster)
    target_clust_col = du.highlight_cluster(target_clusters, target_cluster)

    # convert the links to an adjacency matrix and use it to find an optimal
    # plotting order for the query/target genes
    adj_matrix = du.calculate_adjacency_matrix(links, query_genes, target_genes)
    _no_components, components = du.connected_components(adj_matrix, directed=False)
    query_order, target_order = du.gene_order(adj_matrix, components, len(query_genes))

    query_comp_color, target_comp_color = du.feature_colors(
        components, len(query_genes)
    )

    query_genes = query_genes[query_order]
    query_comp_color = query_comp_color[query_order]
    target_genes = target_genes[target_order]
    target_comp_color = target_comp_color[target_order]
    # don't forget to reorder the genes and colors according to the optimal order.
    # Thanks to Phil for helping me figure this out and debug it!
    query_avg_expr = query_avg_expr.iloc[:, query_order]
    target_avg_expr = target_avg_expr.iloc[:, target_order]
    query_perc_expr = query_perc_expr.iloc[:, query_order]
    target_perc_expr = target_perc_expr.iloc[:, target_order]

    if len(target_genes) > 0 and len(query_genes) > 0:
        du.plot_dotplot(
            query_avg_expr,
            target_avg_expr,
            query_perc_expr,
            target_perc_expr,
            query_genes,
            target_genes,
            links,
            query_clust_col,
            target_clust_col,
            query_comp_color,
            target_comp_color,
            query_species,
            target_species,
            x_offset=x_offset,
            y_offset=y_offset,
            grid_offset=grid_offset,
            query_clustering=query_clustering,
            target_clustering=target_clustering,
            output=output,
            center=center,
            title=title,
            title_font_size=title_font_size,
            cmap=cmap,
        )
    else:
        pass

    # return query_avg_expr, target_avg_expr
