
## emacs noise
find . -name '*~' -type f -delete

## noise
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

## import cleanup
find . -name '*.py' | xargs autoflake --in-place --remove-unused-variables --remove-all-unused-imports 

## formatting
find . -name '*.py' -print0 | xargs -0 yapf -i
