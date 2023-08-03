import re
import sys
import datetime

from feedgen.feed import FeedGenerator

# sudo apt install python3-feedgenerator
#import FeedGenerator

class EzineItem:
    def __init__(self):
        self.title = ''
        self.category = ''
        self.url = ''
        self.urls = []
        self.content = []
        self.content_raw = ''

    def __str__(self):
        return f"EzineItem(title={self.title}, category={self.category}, url={self.url}, urls={self.urls})"

class Ezine:
    def __init__(self):
        self.edition = 0
        self.date = datetime.datetime.now()
        self.credits = ''
        self.url = ''
        self.items = []

    def __str__(self):
        return f"Ezine(\n  edition={self.edition},\n  date={self.date},\n  credits={self.credits},\n  url={self.url},\n  items={self.items}\n)"

categories = {
    'mustsee': "Must see",
    'hack': "Hack",
    'security': "Security",
    'fun': "Fun",
    'credits': "Credits"
}

d2c = {
    "Something that really worth your time!": 'mustsee',
    "Something that's really worth your time!": 'mustsee',
    "Some Kung Fu Techniques.": 'hack',
    "Some Kung Fu Techniques/Tools.": 'hack',
    "All about security issues.": 'security',
    "All about security issues/problems.": 'security',
    "Spare time?": 'fun',
    "Spare time ?": 'fun',
    "Content Helpers (0x)": 'credits',
}

def parse_ezine(path):
    result = Ezine()
    current_category = None
    current_item = EzineItem()
    extra_url_regexp = re.compile("([\w \-]+): (https?://[\w\./?&]+) ?")
    with open(path, 'r') as fp:
        for row in fp:
            row = row.strip()
            if row == "":
                if current_item.title != "":
                    current_item.category = current_category
                    result.items.append(current_item)
                current_item = EzineItem()
                continue
            elif row[0] == "#":
                headers = row.strip(" #º").split("|")
                date_header = headers[3].split(" ")[3].split("/")
                # todo: or get date from git history?
                date = datetime.datetime(int(date_header[2]), int(date_header[1]), int(date_header[0]), tzinfo=datetime.timezone.utc)
                edition = headers[4].strip().split(" ")[1].strip(" #º")
                result.edition = edition
                result.date = date
                continue
            elif row[0] == "'":
                row = row.strip(" '")
                if ord(row[0]) > 127:
                    continue
                if row in d2c:
                    current_category = d2c[row]
                else:
                    print("Unknown category: " + row, file=sys.stderr)
                continue
            
            if current_category == "credits":
                if row.startswith("http"):
                    result.url = row
                else:
                    result.credits = bytes.fromhex(row).decode('ascii')
                continue
            
            current_item.content_raw += row + "<br>\n"
            if row.startswith("Description:"):
            # if row.startswith("Description:") or row.startswith("Descritpion:") or row.startswith("Descripion:") or row.startswith("Descriptions:") or row.startswith("Descxription:") or row.startswith("Descrription:") or row.startswith("Descripton:"):
                current_item.title = row[13:]
                current_item.content.insert(0, row)
            elif row.startswith("URL:"):
                url = row[5:].strip()
                if url.endswith("(+)"):
                    url = url[:-4]
                    current_item.urls += ("bit.ly inspect", url + "+")
                    current_item.content.append("bit.ly inspect: <a href='" + url + "+'>" + url + "+</a>")
                current_item.url = url
                current_item.content.insert(0, "URL: <a href='" + url + "'>" + url + "</a>")
            else:
                res = extra_url_regexp.match(row)
                if res:
                    # print("EXTRA URL FOUND")3
                    current_item.urls += (res.group(1), res.group(2))
                    current_item.content.append(res.group(1) + ": <a href='" + res.group(2) + "'>" + res.group(2) + "</a>")
                else:
                    if ord(row[0]) > 127:
                        continue
                    print("EXTRA DATA FOUND", row)
                    current_item.content.append(row)

            # print(current_category, row[:-1])
    # print(result)
    generate_feed(result)

def generate_feed(ezine):
    fg = FeedGenerator()
    fg.id(ezine.url)
    fg.title('AppSec Ezine #' + ezine.edition)
    fg.description('AppSec Ezine #' + ezine.edition)
    fg.pubDate(ezine.date)
    # todo: handle multiple credits
    fg.author({'name': ezine.credits,'email': "simpsonpt@gmail.com"})
    fg.link( href=ezine.url, rel='alternate' )
    # fg.logo('http://ex.com/logo.jpg')
    # fg.subtitle('This is a cool feed!')
    fg.link( href='https://xl-sec.github.io/AppSecEzine/latest.xml', rel='self' )
    fg.language('en')

    for item in ezine.items:
        fe = fg.add_entry(order='append')
        fe.title(categories[item.category] + ": " + item.title)
        fe.content("<br>\n".join(item.content), type="html")
        fe.category({'term': categories[item.category]})
        fe.id(item.url)
        fe.link(href=item.url)

    print(fg.rss_str(pretty=True).decode(), end="")
    # print(fg.atom_str(pretty=True).decode(), end="")

def main():
    if len(sys.argv) != 2:
        print("Error: expecting path to ezine as only argument")
        sys.exit(1)

    parse_ezine(sys.argv[1])

if __name__ == "__main__":
    main()