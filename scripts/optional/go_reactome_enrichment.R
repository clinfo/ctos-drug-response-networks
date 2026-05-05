#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  library(ReactomePA)
  library(clusterProfiler)
  library(org.Hs.eg.db)
  library(ggplot2)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) {
  stop("Usage: go_reactome_enrichment.R <deg_tsv> <output_prefix> <gene_column>")
}

deg_tsv <- args[1]
output_prefix <- args[2]
gene_column <- args[3]

deg <- read.table(deg_tsv, header = TRUE, sep = "\t", stringsAsFactors = FALSE, check.names = FALSE)
if (!(gene_column %in% colnames(deg))) {
  stop(paste0("Missing gene column: ", gene_column))
}

genes <- unique(deg[[gene_column]])
entrez_table <- bitr(genes, fromType = "SYMBOL", toType = "ENTREZID", OrgDb = "org.Hs.eg.db")
if (nrow(entrez_table) == 0) {
  stop("No Entrez IDs could be mapped.")
}

ck <- enrichPathway(gene = entrez_table$ENTREZID, organism = "human", pAdjustMethod = "BH", readable = TRUE)
write.table(as.data.frame(ck), paste0(output_prefix, "_reactome.tsv"), sep = "\t", row.names = FALSE, quote = FALSE)

pdf(paste0(output_prefix, "_reactome.pdf"), width = 8, height = 10)
print(dotplot(ck, font.size = 12, showCategory = 10) + ggplot2::theme(legend.position = "right"))
dev.off()
