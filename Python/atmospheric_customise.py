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

# Read HTML as lines (preserves Plotly script blocks safely)
lines = html_path.read_text(encoding="utf-8").split("\n")
new_lines = []

favicon_inserted = False
title_replaced = False

favicon_line = '    <link rel="icon" type="image/png" href="../assets/favicon.png">'

for line in lines:

    # 1. Replace title safely (only if not done yet)
    if ("<title>" in line and "</title>" in line and not title_replaced):
        new_lines.append("<title>NZAEA | Atmospheric</title>")
        title_replaced = True

        # 2. Insert favicon immediately after title line
        if not favicon_inserted:
            new_lines.append(favicon_line)
            favicon_inserted = True

    else:
        new_lines.append(line)

# Write the modified lines back
html_path.write_text("\n".join(new_lines), encoding="utf-8")

print("✔ Pages updates complete")
