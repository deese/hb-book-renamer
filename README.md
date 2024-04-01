## Humble Bundle Book renamer

This small script reads books from a folder in the Humble bundle format (without any spaces) and tries to retrieve the title using the metadata.

It provides a text-based selection menu to select the title or enter a custom one.

The script has been tested only with a few number of files (like 5 or 6 bundles) so it may have errors, feel free to PR or send issues :D

Setup
=====

Run the following command to install dependencies:

``` pip install -r requirements.txt ```


usage:
```
usage: hb-book-renamer.py [-h] [-v] [-a EXTENSIONS] folder

HB Book Renamer

positional arguments:
  folder                input folder path

options:
  -h, --help            show this help message and exit
  -v, --verbose         enable verbose mode
  -a EXTENSIONS, --add-ext EXTENSIONS
                        Add extra extension to list of valid extensions (e.g. --add-ext cbz to add cbz)

```


Tested on Linux and Windows using Python 3.12.


