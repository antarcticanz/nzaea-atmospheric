# from pathlib import Path
# import re

# html_path = Path("docs/index.html")

# # Read original HTML
# html = html_path.read_text(encoding="utf-8")

# # -----------------------------------------
# # 1. Replace ONLY the <title>...</title> line
# # -----------------------------------------
# html = re.sub(
#     r"<title>.*?</title>",
#     "<title>NZAEA | Atmospheric</title>",
#     html,
#     flags=re.DOTALL
# )


# # -----------------------------------------
# # 2. Write updated HTML back to disk
# # -----------------------------------------
# html_path.write_text(html, encoding="utf-8")

# print("✔ Updated HTML title and favicon")


# from pathlib import Path

# html_path = Path("docs/index.html")

# lines = html_path.read_text(encoding="utf-8").split("\n")
# new_lines = []
# favicon_inserted = False

# favicon_line = '    <link rel="icon" type="image/png" href="../assets/favicon.png">'

# for line in lines:
#     new_lines.append(line)

#     # When we see </title>, insert favicon AFTER it
#     if "</title>" in line and not favicon_inserted:
#         new_lines.append(favicon_line)
#         favicon_inserted = True

# # Write back exactly the same HTML structure, just with 1 extra line
# html_path.write_text("\n".join(new_lines), encoding="utf-8")

# print("✔ Title and favicon injected safely (no script corruption).")


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
import re

html_path = Path("docs/index.html")
html = html_path.read_text(encoding="utf-8")

# Ensure a <base href="/your-repo/"> exists inside <head>
if "<base " not in html:
    html = re.sub(
        r"(<head[^>]*>)",
        r'\1\n  <base href="/nzaea-atmospheric/">',
        html,
        count=1,
        flags=re.IGNORECASE
    )

# Replace title
html = re.sub(
    r"<title>.*?</title>",
    "<title>NZAEA | Atmospheric</title>",
    html,
    flags=re.DOTALL | re.IGNORECASE
)

# Insert favicon if missing
if 'rel="icon"' not in html:
    html = html.replace(
        "</head>",
        '  <link rel="icon" type="image/png" href="assets/favicon.png?v=2">\n</head>'
    )

html_path.write_text(html, encoding="utf-8")
print("✔ Title and favicon injected for GitHub Pages (project site)")
