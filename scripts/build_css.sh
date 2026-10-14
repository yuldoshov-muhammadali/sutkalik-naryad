#!/bin/sh
# Tailwind CSS ni Node.js'siz yig'ish (standalone CLI).
# Birinchi marta CLI ni yuklab oling (Linux x64; boshqa tizimlar: github.com/tailwindlabs/tailwindcss/releases/tag/v3.4.17):
#   curl -sSLo tailwindcss https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-linux-x64 && chmod +x tailwindcss
# Windows: tailwindcss-windows-x64.exe ni yuklab, quyidagi buyruqni o'sha fayl bilan bajaring.
set -e
cd "$(dirname "$0")/.."
TAILWIND="${TAILWIND:-./tailwindcss}"
"$TAILWIND" -c tailwind.config.js -i static/src/input.css -o static/css/app.css --minify
echo "static/css/app.css yangilandi"
