# ComAnDOS

<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

[![python](https://img.shields.io/badge/Python-3.9-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
![example
workflow](https://github.com/galicae/comandos/actions/workflows/test.yaml/badge.svg)
[![Code style:
black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8129708.svg)](https://doi.org/10.5281/zenodo.8129708)

As a long-time user of SAMap and a connoisseur of cross-species
comparisons, I was always frustrated by the lack of useful visualization
downstream of SAMap results. We don’t need fancy software to figure out
that ciliated cells are similar to ciliated cells, and muscle to muscle,
but what about those pesky “unknown_sensory_2” and “ciliated?\_2”
clusters?

ComAnDOS is a collection of plotting functions and assorted utilities
that I hacked together to help myself and collaborators make sense of
SAMap results. I think it is very useful downstream of SAMap, but it
mostly works with two “primitives”: AnnData, and Pandas DataFrames. If
you care to read the
[documentation](https://galicae.github.io/comandos/) you can probably
figure out how to adapt the functions to your needs. Mainly contains
advanced visualizations for the comparison of single-cell datasets.
Conceived as a SAMap add-on, but does not require it.

## Background and motivation

<details>
<summary>
click to expand
</summary>

Single-cell RNA-seq (scRNA-seq) is a powerful tool to study the
transcriptome of individual cells. As the technology matured, it became
possible to use it on non-model organisms, facilitating cell type
comparison across species. Early methods for this task subsetted gene
expression matrices to one-to-one orthologous genes, assuming that
sequence conservation also implies conservation of location, magnitude,
and timing of gene expression. Not only is this assumption not true, but
it also requires us to discard a large amount of data.

[SAMap](https://elifesciences.org/articles/66747) was the first method
to try and include many-to-one orthology relations. In alternating
steps, it optimises a cell graph and a gene graph, using the former to
inform the latter and vice versa. The result is a converged
low-dimensional embedding that contains the cells of both species,
allowing for direct comparison.

SAMap comes with a small number of visualization tools, but, as I had to
find out myself, they are not sufficient for in-depth analysis. In
particular:

- Sankey diagrams, SAMap’s default visualization for cluster-cluster
  relationships, obscure the fact that cell types are hierarchically
  organized. They also make it harder to quantify just how similar two
  cell types are according to SAMap.
- Tarashansky *et al.* used network diagrams to demonstrate highly
  connected cell type families. I found that these diagrams are not very
  informative, as they are hard to read and do not scale well to large
  datasets.
- In the publication, heatmaps are used once, but not to their full
  extent.
- Overlapping dimplots with corresponding violin plots are used to
  demonstrate co-expression across species. This is a good idea, but
  results in overloaded plots.
- The authors use dotplots to show gene expression across species,
  color-coding the species. This loses one of the dotplots’ dimensions,
  where color usually encodes expression level, and forces the use of an
  additional axis to show expression magnitude. Furthermore, the
  relationships between the plotted genes in the different species are
  hard to visualize and need to be described in text.

These visualisations have two additional shortcomings: First, they are
not easily reproducible, as they are not part of SAMap but rather custom
solutions for very specific use cases. Second, they are extremely
specific in what they show, and thus not useful for exploratory data
analysis.

</details>

## Install

``` sh
pip install comandos
```

Maybe in time I will also make a conda version, but for now I’ll be
sticking to `pip`.

## How to use

Fill me in please! Don’t forget code examples:

``` python
1 + 1
```

    2
