# from pathlib import Path

# html_path = Path("docs/index.html")

# # Read HTML as lines (preserves Plotly script blocks safely)
# lines = html_path.read_text(encoding="utf-8").split("\n")
# new_lines = []

# favicon_inserted = False
# title_replaced = False

# favicon_line = '    <link rel="icon" type="image/png" href="../assets/favicon.png">'

# for line in lines:

#     # 1. Replace title safely (only if not done yet)
#     if ("<title>" in line and "</title>" in line and not title_replaced):
#         new_lines.append("<title>NZAEA | Atmospheric</title>")
#         title_replaced = True

#         # 2. Insert favicon immediately after title line
#         if not favicon_inserted:
#             new_lines.append(favicon_line)
#             favicon_inserted = True

#     else:
#         new_lines.append(line)

# # Write the modified lines back
# html_path.write_text("\n".join(new_lines), encoding="utf-8")

# print("✔ Pages updates complete")


from pathlib import Path

html_path = Path("docs/index.html")

# Read HTML as lines (preserves Plotly/JS blocks safely)
lines = html_path.read_text(encoding="utf-8").split("\n")
new_lines = []

title_replaced = False
favicon_inserted = False
inside_title = False
title_buffer = []

# GH Pages project site: repo-root absolute path + cache-busting
# Resolves to: https://antarcticanz.github.io/nzaea-atmospheric/assets/favicon.png?v=4
favicon_line = '    <link rel="icon" type="image/png" href="/nzaea-atmospheric/assets/favicon.png?v=4">'

for line in lines:
    if inside_title:
        title_buffer.append(line)
        if "</title>" in line:
            # Replace entire title block with the normalized one-liner
            new_lines.append("<title>NZAEA | Atmospheric</title>")
            title_replaced = True

            # Insert favicon immediately after title (once)
            if not favicon_inserted:
                new_lines.append(favicon_line)
                favicon_inserted = True

            inside_title = False
        # Do not append original title lines (we’re replacing them)
        continue

    # One-line <title>...</title>
    if not title_replaced and "<title>" in line and "</title>" in line:
        new_lines.append("<title>NZAEA | Atmospheric</title>")
        title_replaced = True

        if not favicon_inserted:
            new_lines.append(favicon_line)
            favicon_inserted = True
        continue

    # Start of multi-line <title> (no closing on this line)
    if not title_replaced and "<title>" in line and "</title>" not in line:
        inside_title = True
        title_buffer = [line]  # collect until we see </title>
        continue

    new_lines.append(line)

# Fallback: if title wasn’t matched at all, inject favicon before </head> (so you still get the icon)
if not favicon_inserted:
    merged = "\n".join(new_lines)
    if "</head>" in merged and '<link rel="icon"' not in merged:
        merged = merged.replace("</head>", f"{favicon_line}\n</head>")
        new_lines = merged.split("\n")

# Write back
html_path.write_text("\n".join(new_lines), encoding="utf-8")
print("✔ Title set to 'NZAEA | Atmospheric' and favicon injected")
