import sys
from collections import defaultdict
from pathlib import Path

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

    def vprint(self, data):
        """ Print data if verbose is enabled."""
        if self.verbose:
            print(data)

    def __init__(self, verbose=False):
        self.dispatcher = {
        "pdf": self.get_pdf_metadata,
        "epub": self.get_epub_metadata,
        "mobi": self.get_mobi_metadata,
        "prc": self.get_mobi_metadata
        }
        self.verbose = verbose

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
        if ext in self.dispatcher:
            title, author = self.dispatcher[ext](file)
        else:
            title, author = None, None

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

        for k, v in self.books.items():
            choices = self.generate_choices(v)
            if not choices:
                choices = [
                    inquirer.Text('filename', message=f"Filename: {k} -  No choices found, please enter a filename"),
                ]
            else:
                choices = [
                    inquirer.List('filename',
                      message=f"Filename: {k} - Choose an option",
                    choices= choices + [ "Enter a custom filename", "Skip"]
                ),
                ]
            answers = inquirer.prompt(choices)
            while True:
                if not any(answers['filename'] == n for n in [ "Enter a custom filename", "", "Skip" ]):
                    print(f"Renaming {k} to {answers['filename']}")
                    renames[k] = answers['filename']
                    break
                if answers['filename'] == "Enter a custom filename":
                    choices = [
                        inquirer.Text('filename', message=f"Filename: {k} -  Enter a custom filename"),
                    ]
                    answers = inquirer.prompt(choices)
                if answers['filename'] == "Skip":
                    break
        ## Now we apply the renames.
        if len(renames) == 0:
            print("No renames found.")
            return
        self.rename(renames)

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
    file = Path(sys.argv[1])
    if file.is_dir():
        mgr.set_dir(file)


if __name__ == "__main__":
    main()