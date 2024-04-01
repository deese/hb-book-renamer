import sys
from collections import defaultdict
from pathlib import Path
import argparse

import PyPDF2
from ebooklib import epub
import mobi_header
from pathvalidate import sanitize_filename
import inquirer



class Manager():
    """ Manager class to handle books."""
    books = defaultdict(dict)
    dispatcher =  {}
    base_dir = None
    verbose = False
    VALID_EXTENSIONS = ["pdf", "epub", "mobi", "prc"]

    def vprint(self, data):
        """ Print data if verbose is enabled."""
        if self.verbose:
            print(data)

    def __init__(self, verbose=False, extra_extensions=None):
        self.dispatcher = {
        "pdf": self.get_pdf_metadata,
        "epub": self.get_epub_metadata,
        "mobi": self.get_mobi_metadata,
        "prc": self.get_mobi_metadata
        }
        self.verbose = verbose
        self.VALID_EXTENSIONS += extra_extensions if extra_extensions else []
        self.vprint(f"Verbose mode is: {self.verbose}")
        self.vprint(f"Valid extensions are: {self.VALID_EXTENSIONS}")

    def generate_filename(self, title):
        """ Sanitize a filename from a title. """
        if not title:
            return title
        return sanitize_filename(title.title())

    def get_pdf_metadata(self, file):
        """Get metadata from a PDF file."""

        pdf = PyPDF2.PdfReader(file)
        try:
            title = pdf.metadata.get('/Title').title() if '/Title' in pdf.metadata else None
        except Exception:
            self.vprint(f"Error reading title from: {file}")
            self.vprint(f"Title : {pdf.metadata.get('/Title', None)}")
            title = None

        try:
            author = pdf.metadata.get('/Author').title() if '/Author' in pdf.metadata else None
        except Exception:
            author = None

        return title, author

    def get_epub_metadata(self, file):
        """Get metadata from an EPUB file."""
        book = epub.read_epub(file)
        try:
            title = book.get_metadata('DC', 'title')[0][0]
        except Exception:
            self.vprint(f"Error reading title from: {file}")
            self.vprint(f"Title: {book.get_metadata('DC', 'title')}")
            title = None
        try:
            author = book.get_metadata('DC', 'creator')[0][0]
        except Exception:
            author = None

        return title, author

    def get_mobi_metadata(self, file):
        """Get metadata from a MOBI file."""
        mobi = mobi_header.MobiHeader(file)

        title = mobi.metadata['full_name']['value']
        author = mobi.get_exth_value_by_id(100)

        return title, author

    def add_book(self, file):
        """ Add a book to the manager."""
        ext = file.suffix[1:]
        self.vprint(f"Processing file: {file}")

        if ext in self.dispatcher:
            title, author = self.dispatcher[ext](file)
        else:
            title, author = None, None

        if ext in self.VALID_EXTENSIONS:
            self.books[file.stem][ext] = { "title": title, "author": author, "filename": self.generate_filename(title), "original_path": file }

    def prnt(self):
        """ Print the books in the manager."""
        for i in self.books:
            print(i)
            for j in self.books[i]:
                print(j, self.books[i][j])

    def generate_choices(self, book):
        """ Generate choices for a book. """
        choices = []
        for _, v in book.items():
            if v['filename'] and v['filename'] not in choices:
                choices.append(v['filename'])
        return choices

    def prepare_rename(self):
        """ Rename the books in the manager."""
        renames = {}
        try:
            for k, v in self.books.items():
                choices = self.generate_choices(v)
                if not choices:
                    choices = [
                        inquirer.Text('filename', message=f"Filename: \"{k}\" -  No choices found, please enter a filename"),
                    ]
                else:
                    choices = [
                        inquirer.List('filename',
                        message=f"Filename: {k} - Choose an option",
                        choices= choices + [ "Enter a custom filename", "Skip"]
                    ),
                    ]
                answers = inquirer.prompt(choices, raise_keyboard_interrupt=True)
                while True:
                    if not any(answers['filename'] == n for n in [ "Enter a custom filename", "", "Skip" ]):
                        print(f"Renaming {k} to {answers['filename']}")
                        renames[k] = answers['filename']
                        break
                    if answers['filename'] == "Enter a custom filename":
                        choices = [
                            inquirer.Text('filename', message=f"Filename: \"{k}\" -  Enter a custom filename"),
                        ]
                        answers = inquirer.prompt(choices, raise_keyboard_interrupt=True)
                    if answers['filename'] == "Skip":
                        break
            ## Now we apply the renames.
            if len(renames) == 0:
                print("No renames found.")
                return
            self.rename(renames)
        except KeyboardInterrupt:
            print("Cancelled by user.")
            sys.exit(0)

    def rename(self, renames):
        """ Rename the books in the manager."""
        for k, v in renames.items():
            if k not in self.books:
                print("Book not found", k)
                continue
            for ext, data in self.books[k].items():
                if not data['original_path'].exists():
                    print(f"File not found: {data['original_path']}")
                    continue
                count = 1
                extra_name = ""
                while True:
                    try:
                        new_name = Path(data['original_path'].parent, f"{v}{extra_name}.{ext}")
                        print(f"{data['original_path']} -> {new_name}")
                        data['original_path'].rename(new_name)
                        break
                    except FileExistsError:
                        extra_name = f"_{count}"



    def set_dir(self, dirname):
        """ Set the base directory for the manager."""
        self.base_dir = dirname
        for f in dirname.iterdir():
            if " " in f.name:
                self.vprint(f"Skipping {f.name} as doesn't seem a HB book name.")
                continue
            self.add_book(f)
        self.prepare_rename()


def main():
    """ Main function."""
    mgr = Manager()

    parser = argparse.ArgumentParser(description='HB Book Renamer')
    parser.add_argument('-v', '--verbose', action='store_true', help='enable verbose mode')
    parser.add_argument('-a', '--add-ext', action="extend", nargs=1, dest="extensions", help='Add extra extension to list of valid extensions (e.g. --add-ext cbz to add cbz)')
    parser.add_argument('folder', type=str, help='input folder path')
    args = parser.parse_args()

    mgr = Manager(verbose=args.verbose, extra_extensions=args.extensions)

    file = Path(args.folder)
    if file.is_dir():
        mgr.set_dir(file)



if __name__ == "__main__":
    main()