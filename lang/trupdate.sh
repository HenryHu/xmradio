#!/bin/sh

QMLS=../main.qml
PYS=../gui.py

echo "Updating qml"
lupdate -verbose $QMLS -ts qml.ts
echo "Updating py"
pylupdate5 -verbose $PYS -ts py.ts
sed -I .orig -e 's/filename="/filename="..\//' py.ts

for lang in "zh_CN"; do
    echo "Updating $lang"
    name=xmradio_${lang}
    path=${name}.ts
    compiled=${name}.qm
    echo "Merging to $path"
    if [ -e $path ]; then
        lconvert -verbose -target-language $lang qml.ts py.ts $path -o tmp
    else
        lconvert -verbose -target-language $lang qml.ts py.ts -o tmp
    fi
    mv tmp $path
    echo "Generating $compiled"
    lrelease -verbose $path -qm $compiled
done

rm qml.ts py.ts py.ts.orig
