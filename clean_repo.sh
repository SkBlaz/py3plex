find . -name '*~' -type f -delete
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
find . -name '*.py' -print0 | xargs -0 yapf -i
