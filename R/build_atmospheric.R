library(readr)
library(dplyr)
library(stringr)
library(lubridate)
library(purrr)


# -----------------------------
# Single-file reader (safe)
# -----------------------------
read_ndacc_gbu <- function(file) {
  x <- readLines(file, warn = FALSE)
  
  # Find first real observation line: DOY.dec + YYYY MM DD
  start <- grep("^\\s*\\d+\\.\\d+\\s+\\d{4}\\s+\\d{2}\\s+\\d{2}", x)[1]
  if (is.na(start)) {
    stop(sprintf("No NDACC observation block detected in %s", basename(file)))
  }
  
  dat <- x[start:length(x)]
  dat <- dat[dat != ""]  # drop blank lines
  
  # Classify timing vs UV lines by structure (safer than odd/even)
  timing_idx <- grep("^\\s*\\d+\\.\\d+\\s+\\d{4}\\s+\\d{2}\\s+\\d{2}", dat)
  uv_idx     <- grep("^\\s*\\d+\\.\\d+[eE][+-]\\d+", dat)
  
  line1 <- dat[timing_idx]
  line2 <- dat[uv_idx]
  
  # (Optional) validate timing row structure: 17 tokens after squish
  line1_clean <- stringr::str_squish(line1)
  split_test  <- strsplit(line1_clean, "\\s+")
  lens        <- sapply(split_test, length)
  
  if (!all(lens == 17)) {
    bad <- which(lens != 17)
    stop(sprintf(
      "Malformed timing rows (%d) in %s. Example indices: %s",
      length(bad), basename(file), paste(head(bad, 10), collapse = ", ")
    ))
  }
  
  # Parse timing block with explicit types
  txt <- paste0(paste(line1, collapse = "\n"), "\n")  # ensure newline at end
  
  t1 <- readr::read_table(
    I(txt),  # <- IMPORTANT: treat as literal text, not path
    col_names = c(
      "DECDAY","Year","Month","Day","ExcelTime",
      "Start_h","Start_m",
      "T310_h","T310_m","T310_s",
      "T360_h","T360_m","T360_s",
      "SZA","Vol","Sky","Flag"
    ),
    col_types = readr::cols(
      DECDAY    = readr::col_double(),
      Year      = readr::col_integer(),
      Month     = readr::col_integer(),
      Day       = readr::col_integer(),
      ExcelTime = readr::col_double(),
      Start_h   = readr::col_integer(),
      Start_m   = readr::col_integer(),
      T310_h    = readr::col_integer(),
      T310_m    = readr::col_integer(),
      T310_s    = readr::col_integer(),
      T360_h    = readr::col_integer(),
      T360_m    = readr::col_integer(),
      T360_s    = readr::col_integer(),
      SZA       = readr::col_double(),
      Vol       = readr::col_integer(),
      Sky       = readr::col_integer(),
      Flag      = readr::col_integer()
    ),
    show_col_types = FALSE
  )
  
  # Parse UV block (should be 6 doubles per row)
  
  # line2 is a character vector containing the second line of data
  txt2 <- paste0(paste(line2, collapse = "\n"), "\n")  # ensure trailing newline
  
  t2 <- readr::read_table(
    I(txt2),  # treat as literal text, not a filepath
    col_names = c("UVB","UVA","UVEry","UVDNA","UVPlant","UVVitD"),
    col_types = readr::cols(.default = readr::col_double()),
    # If the files use 9.999E+09 as a missing sentinel, uncomment:
    # na = "9.999E+09",
    show_col_types = FALSE
  )
    
  
  # Align in case one block is shorter (truncate to min rows)
  n <- min(nrow(t1), nrow(t2))
  if (n == 0) {
    stop(sprintf("No aligned observations found in %s", basename(file)))
  }
  
  uv <- cbind(t1[1:n, ], t2[1:n, ])
  
  return(uv)
}



# -----------------------------
# Batch over directory
# -----------------------------
files <- list.files("data/", pattern = "\\.gbu$", full.names = TRUE)


# Extract the 4-digit YYMM at the end of the filename (before .gbu)
yymm <- sub("^.*?(\\d{4})\\.gbu$", "\\1", files)

yy <- as.integer(substr(yymm, 1, 2))
mm <- as.integer(substr(yymm, 3, 4))

# Map to full year: 90–99 -> 1990–1999, else 2000+YY
yyyy <- ifelse(yy >= 90, 1900 + yy, 2000 + yy)

# Build a sortable key (e.g., 199902 for 1999-02)
key <- yyyy * 100 + mm

# Sort files by this key
files_sorted <- files[order(key)]


# Safe wrapper so a single bad file doesn't stop the run
safe_read <- purrr::safely(read_ndacc_gbu, otherwise = NULL)

# Read with a simple progress message
results <- vector("list", length(files))
for (i in seq_along(files)) {
  f <- files[i]
  cat(sprintf("[%d/%d] %s ... ", i, length(files), basename(f)))
  res <- safe_read(f)
  if (!is.null(res$error)) {
    cat("FAILED\n")
    message(sprintf("  -> %s", res$error$message))
    results[[i]] <- NULL
  } else {
    cat("OK\n")
    results[[i]] <- res$result
  }
}

# Bind successful results
ds <- dplyr::bind_rows(results)

#write_csv(ds, "uv_data.csv")

## https://github.com/oceanum-io/oceanum-R

library(oceanumR)
