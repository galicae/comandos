# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_dotplot_util.ipynb.

# %% auto 0
__all__ = ['godsnot_102', 'prepare_dotplot', 'label_pos', 'calculate_adjacency_matrix', 'gene_order', 'feature_colors',
           'get_dot_size', 'get_dot_color', 'plot_dot_legend', 'plot_colorbar_legend', 'make_dotplot',
           'add_connections', 'add_homology_context']

# %% ../nbs/03_dotplot_util.ipynb 4
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.patches import ConnectionPatch
from numpy.random import default_rng
from scipy.sparse.csgraph import connected_components

try:
    from matplotlib.colors import TwoSlopeNorm as DivNorm
except ImportError:
    # matplotlib<3.2
    from matplotlib.colors import DivergingNorm as DivNorm

from . import util

# %% ../nbs/03_dotplot_util.ipynb 6
def map_array_to_color(x, palette, xmax=None):
    if xmax is None:
        xmax = np.max(x)
    color = palette(x / xmax)
    return color


def map_to_colormap(x, cmap="magma_r", vmin=0, vmax=None):
    if vmax is None:
        vmax = np.max(x)
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    m = cm.ScalarMappable(norm=norm, cmap=cmap)
    return m.to_rgba(x)


def unique_genes(connections):
    real = connections != np.array(None)
    return np.unique(connections[real])


def check_colornorm(vmin=None, vmax=None, vcenter=None, norm=None):
    # from ScanPy
    if norm is not None:
        if (vmin is not None) or (vmax is not None) or (vcenter is not None):
            raise ValueError("Passing both norm and vmin/vmax/vcenter is not allowed.")
    else:
        if vcenter is not None:
            norm = DivNorm(vmin=vmin, vmax=vmax, vcenter=vcenter)
        else:
            norm = Normalize(vmin=vmin, vmax=vmax)

    return norm


def highlight_cluster(clusters, cluster, bg="black", hl="red"):
    clust_col = [bg] * len(clusters)
    if cluster is None or cluster == "":
        print("Invalid cluster name; returning background color.")
        return clust_col
    if cluster not in clusters:
        print("Cluster not found; returning background color.")
        return clust_col
    highlight = np.where(clusters == cluster)[0][0]
    clust_col[highlight] = hl
    return clust_col

# %% ../nbs/03_dotplot_util.ipynb 7
godsnot_102 = np.array(
    [
        "#FFFF00",
        "#1CE6FF",
        "#FF34FF",
        "#FF4A46",
        "#008941",
        "#006FA6",
        "#A30059",
        "#FFDBE5",
        "#7A4900",
        "#0000A6",
        "#63FFAC",
        "#B79762",
        "#004D43",
        "#8FB0FF",
        "#997D87",
        "#5A0007",
        "#809693",
        "#6A3A4C",
        "#1B4400",
        "#4FC601",
        "#3B5DFF",
        "#4A3B53",
        "#FF2F80",
        "#61615A",
        "#BA0900",
        "#6B7900",
        "#00C2A0",
        "#FFAA92",
        "#FF90C9",
        "#B903AA",
        "#D16100",
        "#DDEFFF",
        "#000035",
        "#7B4F4B",
        "#A1C299",
        "#300018",
        "#0AA6D8",
        "#013349",
        "#00846F",
        "#372101",
        "#FFB500",
        "#C2FFED",
        "#A079BF",
        "#CC0744",
        "#C0B9B2",
        "#C2FF99",
        "#001E09",
        "#00489C",
        "#6F0062",
        "#0CBD66",
        "#EEC3FF",
        "#456D75",
        "#B77B68",
        "#7A87A1",
        "#788D66",
        "#885578",
        "#FAD09F",
        "#FF8A9A",
        "#D157A0",
        "#BEC459",
        "#456648",
        "#0086ED",
        "#886F4C",
        "#34362D",
        "#B4A8BD",
        "#00A6AA",
        "#452C2C",
        "#636375",
        "#A3C8C9",
        "#FF913F",
        "#938A81",
        "#575329",
        "#00FECF",
        "#B05B6F",
        "#8CD0FF",
        "#3B9700",
        "#04F757",
        "#C8A1A1",
        "#1E6E00",
        "#7900D7",
        "#A77500",
        "#6367A9",
        "#A05837",
        "#6B002C",
        "#772600",
        "#D790FF",
        "#9B9700",
        "#549E79",
        "#FFF69F",
        "#201625",
        "#72418F",
        "#BC23FF",
        "#99ADC0",
        "#3A2465",
        "#922329",
        "#5B4534",
        "#FDE8DC",
        "#404E55",
        "#0089A3",
        "#CB7E98",
        "#A4E804",
        "#324E72",
    ]
)

# %% ../nbs/03_dotplot_util.ipynb 8
def prepare_dotplot(
    avg_expr,
    perc_expr,
    cmap="magma_r",
    vmin=0,
    vmax=None,
    size_exponent=1.5,
    dot_size=200,
):
    """Pivots average expression and percent expressed tables to make them dotplot-friendly.

    Parameters
    ----------
    avg_expr : pandas DataFrame
        Data frame that holds average expression for all genes and all clusters.
    perc_expr : pandas DataFrame
        Data frame that tracks the percentage of cells expressing each gene in every cluster.
    cmap : str or Colormap, optional
        The Colormap instance or registered colormap name used to map scalar data to colors, by
        default "magma_r"
    vmin : int, optional
        Minimum average expression value to show, by default 0
    vmax : _type_, optional
        Maximum average expression value to show, by default None (defaults to maximum average expr.
        value).
    size_exponent : float, optional
        Dot size is computed as fraction ** size_exponent * dot_size. By default 1.5.

    Returns
    -------
    df_avg_expr : pandas DataFrame
        Melted data frame. Each row contains a cluster name, gene name, and the average expression
        value of that gene in that cluster.
    df_perc_expr : pandas DataFrame
        Melted data frame. Each row contains a cluster name, gene name, and the percentage of cells
        expressing the gene in that cluster.
    color : numpy array
        An array that holds RGBA-coded color values for the average expression in a cluster/gene
        combination, according to the input color map.
    """
    df_avg_expr = avg_expr.reset_index().melt("index")
    df_avg_expr.columns = ["row", "column", "value"]
    color = map_to_colormap(df_avg_expr["value"], cmap=cmap, vmin=vmin, vmax=vmax)

    df_perc_expr = perc_expr.reset_index().melt("index")
    df_perc_expr.columns = ["row", "column", "value"]
    df_perc_expr["value"] = df_perc_expr["value"] ** size_exponent * dot_size
    return df_avg_expr, df_perc_expr, color


def label_pos(display_coords, key, side="left"):
    """Get the edge coordinates of a label. Keep either the left or the right end of the word.

    Parameters
    ----------
    display_coords : dict
        A dictionary that holds the window extents of tick labels.
    key : str
        The label to retrieve; a gene name.
    side : str, optional
        One of "left" or "right"; depending on orientation will return the leftmost or rightmost
        position of the label. By default "left"

    Returns
    -------
    x : float
        The left or right edge of the label.
    y : float
        The middle of the label.
    """
    x0, y0, x1, y1 = display_coords[key].flatten()
    if side == "left":
        x = x1
    else:
        x = x0
    y = (y0 + y1) / 2
    return x, y


def calculate_adjacency_matrix(connections, query_genes, target_genes):
    query_G = len(query_genes)
    target_G = len(target_genes)
    adjacency = np.zeros(
        (query_G, target_G), dtype=bool
    )  # not a true adjacency matrix; targetely the top right corner.
    query_connected = {gene: i for i, gene in enumerate(query_genes)}
    target_connected = {gene: i for i, gene in enumerate(target_genes)}

    if connections.shape[1] == 3:
        connections = connections[:, :2]
    for [g1, g2] in connections:
        if g1 is None or g2 is None:
            continue
        i1 = query_connected[g1]
        i2 = target_connected[g2]
        adjacency[i1, i2] = True

    full_adjacency = np.zeros((query_G + target_G, query_G + target_G), dtype=bool)
    full_adjacency[:query_G][:, query_G:] = adjacency
    full_adjacency[query_G:][:, :query_G] = adjacency.T
    return full_adjacency


def gene_order(full_adjacency, components, query_G):
    comp, freq = np.unique(components, return_counts=True)
    degrees = np.sum(full_adjacency, axis=0)

    keep = freq > 1
    descending = np.argsort(-freq[freq > 1])

    no_comps = len(comp[freq > 1])
    for i, c in enumerate(comp[keep][descending]):
        # degrees[components == c] *= freq[keep][descending][i] * (no_comps - i)
        degrees[components == c] = no_comps - i

    query_degree = degrees[:query_G]
    target_degree = degrees[query_G:]

    query_order = np.argsort(-query_degree)
    target_order = np.argsort(-target_degree)
    return query_order, target_order


def feature_colors(components, query_G, seed=42):
    comp, freq = np.unique(components, return_counts=True)
    rng = default_rng(seed)
    no_comps = len(comp[freq > 1])
    if no_comps < 102:
        pick_colors = rng.choice(len(godsnot_102), size=no_comps, replace=False)
    else:
        pick_colors = rng.choice(len(godsnot_102), size=no_comps, replace=True)
    godsnot_keep = {}
    for i, component in enumerate(comp[freq > 1]):
        godsnot_keep[component] = godsnot_102[pick_colors][i]

    components_colored = ["black"] * len(components)
    for i, component in enumerate(components):
        if component in comp[freq > 1]:
            components_colored[i] = godsnot_keep[component]

    query_comp_color = np.array(components_colored[:query_G])
    target_comp_color = np.array(components_colored[query_G:])
    return query_comp_color, target_comp_color


def get_dot_size(
    query,
    target,
    query_clustering,
    target_clustering,
    query_genes=None,
    target_genes=None,
    query_gene_names=None,
    target_gene_names=None,
):
    query_cluster_size = query.obs[query_clustering].value_counts()
    target_cluster_size = target.obs[target_clustering].value_counts()

    query_perc_expr = (
        util.grouped_obs_present(query, query_clustering) / query_cluster_size
    )
    target_perc_expr = (
        util.grouped_obs_present(target, target_clustering) / target_cluster_size
    )

    # subset to only the genes we have
    if query_genes is not None and target_genes is not None:
        query_perc_expr = query_perc_expr.loc[query_genes].copy().T
        target_perc_expr = target_perc_expr.loc[target_genes].copy().T
    else:
        print("No genes supplied; returning all genes.")

    if query_gene_names is not None:
        query_perc_expr.columns = query.var[query_gene_names].loc[
            query_perc_expr.columns
        ]
    if target_gene_names is not None:
        target_perc_expr.columns = target.var[target_gene_names].loc[
            target_perc_expr.columns
        ]
    return query_perc_expr, target_perc_expr


def get_dot_color(
    query,
    target,
    query_clustering,
    target_clustering,
    query_genes=None,
    target_genes=None,
    query_gene_names=None,
    target_gene_names=None,
):
    query_avg_expr = util.grouped_obs_mean(query, query_clustering)
    target_avg_expr = util.grouped_obs_mean(target, target_clustering)
    # subset to only the genes we have
    if query_genes is not None and target_genes is not None:
        query_avg_expr = query_avg_expr.loc[query_genes].copy().T
        target_avg_expr = target_avg_expr.loc[target_genes].copy().T
    else:
        print("No genes supplied; returning all genes.")

    if query_gene_names is not None:
        query_avg_expr.columns = query.var[query_gene_names].loc[query_avg_expr.columns]
    if target_gene_names is not None:
        target_avg_expr.columns = target.var[target_gene_names].loc[
            target_avg_expr.columns
        ]
    return query_avg_expr, target_avg_expr


def plot_dot_legend(
    dot_legend,
    size_exponent=1.5,
    dot_size=200,
):
    """Create the dotplot legend, explaining dot size.

    Parameters
    ----------
    dot_legend : matplotlib `axis`
        The subplot of the grid that contains the dotplot legend.
    size_exponent : float, optional
        The exponent to raise the fraction of cells in a group to, to get the dot size. The default
        is 1.5.
    dot_size : int, optional
        The size of the largest dot. The default is 200.
    """
    dot_legend.axis("equal")
    xticks = np.arange(5)
    dot_legend.scatter(
        xticks,
        np.zeros(5),
        s=np.arange(0.2, 1.1, 0.2) ** size_exponent * dot_size,
        c="gray",
        edgecolors="black",
    )
    dot_legend.set_xlim(-0.5, 4.5)
    dot_legend.yaxis.set_visible(False)
    dot_legend.spines[["left", "right", "top", "bottom"]].set_visible(False)
    dot_legend.xaxis.set_ticks(xticks)
    dot_legend.xaxis.set_ticklabels(["20", "40", "60", "80", "100"])
    dot_legend.set_title("Fraction of cells\nin group (%)", fontsize="small")


def _get_mappable(query_avg_expr, target_avg_expr, cmap="magma_r"):
    all_expr = np.concatenate(
        (query_avg_expr.values.flatten(), target_avg_expr.values.flatten())
    )
    max_expr = np.max(all_expr)
    norm = check_colornorm(0, max_expr)
    return ScalarMappable(norm, cmap=cmap)


def plot_colorbar_legend(cbar_legend, query_avg_expr, target_avg_expr, cmap="magma_r"):
    mappable = _get_mappable(query_avg_expr, target_avg_expr, cmap=cmap)
    mpl.colorbar.Colorbar(cbar_legend, mappable=mappable, orientation="horizontal")
    cbar_legend.yaxis.set_visible(False)
    cbar_legend.set_title("Mean expression\nin group", fontsize="small")
    cbar_legend.xaxis.set_tick_params(labelsize="small")


def make_dotplot(
    ax,
    avg,
    perc,
    gene_names,
    species,
    clustering,
    clust_color,
    gene_color,
    side="left",
):
    N, G = avg.shape
    df_avg, df_perc, color = prepare_dotplot(avg, perc)
    ax.scatter(
        df_avg["row"],
        df_avg["column"],
        c=color,
        s=df_perc["value"],
        edgecolors="black",
    )
    ax.axis("equal")
    ax.set_title(f"species: {species}, clustering: {clustering}")
    ax.xaxis.set_ticks(np.arange(N))
    ax.xaxis.set_ticklabels(avg.index, rotation=90)
    ax.yaxis.set_ticks(np.arange(G), labels=gene_names)
    if side == "left":
        ax.yaxis.tick_right()
    else:
        ax.yaxis.tick_left()
    ax.invert_yaxis()
    [t.set_color(clust_color[i]) for i, t in enumerate(ax.xaxis.get_ticklabels())]
    [t.set_color(gene_color[i]) for i, t in enumerate(ax.yaxis.get_ticklabels())]


def add_connections(
    fig, connections, query_gene_names, query_gene_colors, label_offset
):
    label_offset = np.array([label_offset, 0])
    left = fig.get_axes()[0]
    right = fig.get_axes()[1]

    left_labels = {}
    for label in left.get_yticklabels():
        bbox = label.get_window_extent()
        coords = fig.transFigure.inverted().transform(bbox)
        left_labels[label.get_text()] = coords + label_offset

    right_labels = {}
    for label in right.get_yticklabels():
        bbox = label.get_window_extent()
        coords = fig.transFigure.inverted().transform(bbox)
        right_labels[label.get_text()] = coords - label_offset

    query_index = {g: i for i, g in enumerate(query_gene_names)}
    for c in connections:
        linestyle = "dotted"
        if len(c) == 3:
            gene_from, gene_to, ls = c
            if ls == 0:
                linestyle = (0, (1, 5))
            elif ls == 1:
                linestyle = (0, (5, 5))
            elif ls == 2:
                linestyle = "solid"
        else:
            gene_from, gene_to = c
        if gene_from is None or gene_to is None:
            continue
        species_a = label_pos(left_labels, gene_from, side="left")
        species_b = label_pos(right_labels, gene_to, side="right")
        con = ConnectionPatch(
            xyA=species_a,
            xyB=species_b,
            coordsA="figure fraction",
            coordsB="figure fraction",
            color=query_gene_colors[query_index[gene_from]],
            linestyle=linestyle,
        )
        right.add_artist(con)


def _plot_dotplot(
    query_avg_expr,
    target_avg_expr,
    query_perc_expr,
    target_perc_expr,
    query_genes,
    target_genes,
    connections,
    query_cluster_colors,
    target_cluster_colors,
    query_gene_colors,
    target_gene_colors,
    query_species,
    target_species,
    x_offset=1,
    y_offset=0,
    grid_offset=30,
    query_clustering="leiden",
    target_clustering="leiden",
    output="./paired_dotplot.png",
    title=None,
    title_font_size=16,
    center=True,
):
    # make shortcuts for the number of clusters and number of genes
    query_N, query_G = query_avg_expr.shape
    target_N, target_G = target_avg_expr.shape

    # sometimes we end up overcorrecting when batch-producing
    # images this way
    y_size = np.max([query_G, target_G]) / 2 + y_offset
    if y_size < 0:
        y_size = np.max([query_G, target_G]) / 2

    # create empty figure that scales with number of clusters and genes
    figsize = ((query_N + target_N) / 2 + x_offset, y_size)

    fig = plt.figure(figsize=figsize)
    max_genes = np.max([query_G, target_G])
    columns = query_N + target_N + grid_offset + 6
    ax = fig.add_gridspec(max_genes, columns)

    # add space for the left dotplot (query)
    left_start = 0
    if center and query_G > max_genes:
        left_start = (max_genes - query_G) // 2 - 1
    left_end = left_start + query_G
    left = fig.add_subplot(ax[left_start:left_end, 0:query_N])

    # add space for the right dotplot (target)
    right_start = 0
    if center and target_G > max_genes:
        right_start = (max_genes - target_G) // 2 - 1
    right_end = right_start + target_G

    after_blank = query_N + grid_offset
    before_legends = query_N + grid_offset + target_N
    right = fig.add_subplot(
        ax[
            right_start:right_end,
            after_blank:before_legends,
        ]
    )

    left.set_zorder(0)
    right.set_zorder(1)

    make_dotplot(
        left,
        query_avg_expr,
        query_perc_expr,
        query_genes,
        query_species,
        query_clustering,
        query_cluster_colors,
        query_gene_colors,
        side="left",
    )

    make_dotplot(
        right,
        target_avg_expr,
        target_perc_expr,
        target_genes,
        target_species,
        target_clustering,
        target_cluster_colors,
        target_gene_colors,
        side="right",
    )

    # saving the figure: don't forget the dpi option!
    if title is not None:
        fig.suptitle(title, fontsize=title_font_size)
    fig.savefig(output)

    # calculate label offset to make the links between genes more legible
    label_offset = 1 / (query_N + target_N + grid_offset * 2) / 3
    # draw appropriately colored lines between connected genes
    add_connections(fig, connections, query_genes, query_gene_colors, label_offset)

    dot_start = right_start + target_G // 3
    dot_legend = fig.add_subplot(ax[dot_start : (dot_start + 1), -5:])
    plot_dot_legend(dot_legend)

    cbar_start = right_start + 2 * target_G // 3
    cbar_legend = fig.add_subplot(ax[cbar_start : (cbar_start + 1), -3:])
    plot_colorbar_legend(cbar_legend, query_avg_expr, target_avg_expr)

    plt.savefig(output)


def add_homology_context(connections, orthology):
    query_genes = [g for g in connections[:, 0] if g is not None]
    target_genes = [g for g in connections[:, 1] if g is not None]

    query_orthology = np.intersect1d(query_genes, orthology.index)
    target_orthology = np.intersect1d(target_genes, orthology.columns)

    subset = (
        orthology.loc[query_orthology][target_orthology]
        .melt(ignore_index=False)
        .reset_index(drop=False)
    )

    homologs = subset[subset["value"] > 0]
    homologs.columns = ["query_id", "target_id", "value"]
    query_no_homology = np.setdiff1d(query_genes, homologs["query_id"])
    target_no_homology = np.setdiff1d(target_genes, homologs["target_id"])

    query_side = np.concatenate(
        (
            homologs["query_id"].values,
            query_no_homology,
            [None] * len(target_no_homology),
        )
    )
    target_side = np.concatenate(
        (
            homologs["target_id"].values,
            [None] * len(query_no_homology),
            target_no_homology,
        )
    )
    orthology_info = np.concatenate(
        (
            homologs["value"].values,
            [0] * (len(query_no_homology) + len(target_no_homology)),
        )
    )

    connections = np.array([query_side, target_side, orthology_info]).T
    return connections
