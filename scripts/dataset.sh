#!/usr/bin/env bash

COMMIT=54bbd6880add9f874368d5c266790d7af9c94b66
TARGET=fonts
TMP=$(mktemp -d)

curl -L https://github.com/google/fonts/archive/${COMMIT}.zip -o ${TMP}/fonts.zip
unzip -q ${TMP}/fonts.zip -d ${TMP}
mkdir -p ${TARGET}
mv ${TMP}/fonts-${COMMIT}/* ${TARGET}/
rm -rf ${TMP}
