#!/bin/bash

SITES="www.anandtech.com arstechnica.com www.google.com www.engadget.com www.rockpapershotgun.com www.sydsvenskan.se"
BASE="$(dirname "$0")"
DEST="${BASE}/test-suite"

# Make sure we have wget
which wget 2>/dev/null >/dev/null
if [ $? -ne 0 ]; then
	echo "Requires wget"
	exit 255
fi

if [ -d "${DEST}" ]; then
  echo "Output directory exists, please remove it using:"
  echo "  rm -rf \"${DEST}\""
  echo "if you wish to get a new copy."
else
  mkdir -p "${DEST}"
  pushd "${DEST}"
  for SITE in ${SITES}; do
    wget -k -p "http://${SITE}"
  done
  popd
fi

echo "Processing: "
for SITE in ${SITES}; do
  "${BASE}/compile.py" "${DEST}/${SITE}/index.html" "${DEST}/${SITE}.html"
done

echo "Tada! Test by opening the files in the destination folder:"
echo "  ${DEST}"
