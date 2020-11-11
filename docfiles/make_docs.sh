## clean the html
rm -rvf html;

## autogenerate the code API docs
sphinx-apidoc -o AUTOGEN_results -f ../py3plex;

## generate the core html folder
make html;

## copy to the core folder
cp -rvf _build/html/* ../docs/
