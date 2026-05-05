#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  library(BiocParallel)
  library(snow)
  library(CopywriteR)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {
  stop("Usage: cna_copywriter_helper.R <bam_directory>")
}

bam_dir <- normalizePath(args[1], mustWork = TRUE)
preCopywriteR(output.folder = bam_dir, bin.size = 20000, ref.genome = "hg38", prefix = "chr")

bp.param <- SnowParam(workers = 1, type = "SOCK")
samples <- list.files(path = bam_dir, pattern = "recal\\.bam$", full.names = TRUE)
if (length(samples) == 0) {
  stop("No recal.bam files found.")
}
controls <- samples
sample.control <- data.frame(samples = samples, controls = controls)
CopywriteR(sample.control = sample.control, destination.folder = bam_dir, reference.folder = file.path(bam_dir, "hg38_20kb_chr"), bp.param = bp.param)
plotCNA(destination.folder = bam_dir)
