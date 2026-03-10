library(tidyverse)
options(scipen=999)


# Create a sequence of monthly dates
dates <- seq.Date(
  from = as.Date("1990-01-01"),
  to   = Sys.Date(),
  by   = "month"
)

# Convert to YYMM format
the_value <- format(dates, "%y%m")

# Build URLs
file_string <- paste0(
  "https://www-air.larc.nasa.gov/cgi-bin/ndaccPub?stations/arrival.heights/ames/uvspect/aruv",
  the_value,
  ".gbu"
)



################################################################################
# Run the downloads; collect per-file outcome
results <- lapply(file_string, function(x) {
  dest <- file.path(
    "C:/Users/ANTNZDEV/michaelmeredythyoung/github/atmospheric/data",
    basename(x)
  )
  
  status <- "ok"
  reason <- NA_character_
  
  tryCatch({
    # Download
    download.file(x, destfile = dest, mode = "wb", quiet = TRUE)
    
    # Read small header to validate (close exactly once)
    con <- file(dest, "rt")
    head_lines <- tryCatch(readLines(con, n = 5, warn = FALSE), finally = close(con))
    
    # --- ONLY THESE TWO CHECKS, AS REQUESTED ---
    
    # 1) detect HTML failure page
    if (any(grepl("<html", head_lines, ignore.case = TRUE))) {
      message("❌ HTML returned instead of data: ", basename(x))
      status <- "failed"; reason <- "html returned"
      if (file.exists(dest)) file.remove(dest)
      return(data.frame(
        url = x, file = basename(dest), status = status, reason = reason,
        stringsAsFactors = FALSE
      ))
    }
    
    # 2) detect empty file
    if (length(head_lines) == 0) {
      message("❌ Empty file returned: ", basename(x))
      status <- "failed"; reason <- "empty file"
      if (file.exists(dest)) file.remove(dest)
      return(data.frame(
        url = x, file = basename(dest), status = status, reason = reason,
        stringsAsFactors = FALSE
      ))
    }
    
    # Success
    message("✅ Downloaded OK: ", basename(x))
    data.frame(
      url = x, file = basename(dest), status = status, reason = reason,
      stringsAsFactors = FALSE
    )
    
  }, error = function(e) {
    # Keep going on error; log and clean up
    message("❌ Failed to download: ", basename(x), " — ", conditionMessage(e))
    if (file.exists(dest)) file.remove(dest)
    data.frame(
      url = x, file = basename(dest), status = "failed",
      reason = paste0("download error: ", conditionMessage(e)),
      stringsAsFactors = FALSE
    )
  })
})

# Bind all outcomes into a single data.frame
results_df <- do.call(rbind, results)

# Failures to review at the end
failed_df <- subset(results_df, status == "failed")

# Optional summary
cat("\nSummary:\n")
cat("  OK:     ", sum(results_df$status == "ok", na.rm = TRUE), "\n")
cat("  Failed: ", nrow(failed_df), "\n")

# Inspect failures
failed_df
