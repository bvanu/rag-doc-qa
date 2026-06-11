import urllib.request
from html.parser import HTMLParser


class TableCellReader(HTMLParser):
    """Collects the text inside every <td> so we can read the table."""
    def __init__(self):
        super().__init__()
        self.cells = []
        self.inside_cell = False
        self.text = ""

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            self.inside_cell = True
            self.text = ""

    def handle_endtag(self, tag):
        if tag == "td":
            self.inside_cell = False
            self.cells.append(self.text.strip())

    def handle_data(self, data):
        if self.inside_cell:
            self.text += data


def print_secret_message(doc_url):
    # Grab the published doc's HTML
    html = urllib.request.urlopen(doc_url).read().decode("utf-8")

    # Read out all the table cells
    reader = TableCellReader()
    reader.feed(html)
    cells = reader.cells

    # Cells go in groups of three: x, character, y.
    # Build a lookup of position -> character.
    points = {}
    for i in range(0, len(cells), 3):
        x, char, y = cells[i], cells[i + 1], cells[i + 2]
        if not x.isdigit() or not y.isdigit():
            continue  # to skips the header row
        points[(int(x), int(y))] = char

    # Find out how big the grid is
    width = max(x for x, y in points) + 1
    height = max(y for x, y in points) + 1

    # Print, top row first, spaces where nothing was placed
    for y in range(height):
        print("".join(points.get((x, y), " ") for x in range(width)))


if __name__ == "__main__":
    print_secret_message("https://docs.google.com/document/d/e/2PACX-1vSvM5gDlNvt7npYHhp_XfsJvuntUhq184By5xO_pA4b_gCWeXb6dM6ZxwN8rE6S4ghUsCj2VKR21oEP/pub")