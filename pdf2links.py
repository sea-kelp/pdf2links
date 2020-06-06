#!/usr/bin/env python3

import csv
import itertools
import os
import sys

from re import findall
from string import Template
from urllib.parse import urlparse

html_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <title>$title</title>

    <style>
        li.collapsible {
            list-style: none;
        }
    </style>
</head>
<body>
    <h2>$title</h2>

    <ul>
        $body
    </ul>

    <script src="https://code.jquery.com/jquery-3.5.1.js"></script>
    <script>
        $$('.collapsible').each(function () {
            var el = $$(this);
            var collapser = $$('<span>').text('+');
            el.prepend(collapser);
            collapser.click(function () {
                el.children('ul').toggle();
                collapser.text(collapser.text() == '+' ? '-' : '+');
            })
            el.find('ul').hide();
            console.log(el.children('ul'));
        });
    </script>
</body>
</html>
""")

def run(pdf_dir):
    pdfs = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    pdf_links = [find_links_in_pdf(pdf_dir, f) for f in pdfs]
    pdf_links = list(itertools.chain.from_iterable(pdf_links))

    dump_csv(pdf_links, pdf_dir, "out.csv")
    write_pdf_html(pdf_links, pdf_dir, "pdfs.html")
    write_domain_html(pdf_links, pdf_dir, "domains.html")
    write_index_html(pdf_dir, "index.html")

def find_links_in_pdf(base_dir, f):
    with open(os.path.join(base_dir, f), 'rb') as pdf:
        urls = set(findall(r'URI\(([^)]+)\)', pdf.read().decode("ISO-8859-1")))
        return [(f, urlparse(url).netloc, url) for url in urls]

def dump_csv(pdf_links, base_dir, out_file):
    with open(os.path.join(base_dir, out_file), "w") as csvfile:
        writer = csv.writer(csvfile)
        for link in pdf_links:
            writer.writerow(link)

def write_pdf_html(pdf_links, base_dir, out_file):
    with open(os.path.join(base_dir, out_file), "w") as f:
        data = {}
        for link in pdf_links:
            filename, domain, url = link
            if filename not in data:
                data[filename] = {}
            if domain not in data[filename]:
                data[filename][domain] = []
            data[filename][domain].append(url)

        body = "".join([make_section(
            make_link(filename),
            "".join([
                make_section(
                    domain,
                    "".join([make_list_link(l) for l in links]),
                    len(links)
                ) for domain, links in sorted(domains.items())
            ]),
            len(domains)
        ) for filename, domains in sorted(data.items())])
        f.write(html_template.substitute(title="PDFs", body=body))

def write_domain_html(pdf_links, base_dir, out_file):
    with open(os.path.join(base_dir, out_file), "w") as f:
        data = {}
        for link in pdf_links:
            filename, domain, url = link
            if domain not in data:
                data[domain] = {}
            if filename not in data[domain]:
                data[domain][filename] = []
            data[domain][filename].append(url)

        body = "".join([make_section(
            domain,
            "".join([
                make_section(
                    make_link(filename),
                    "".join([make_list_link(l) for l in links]),
                    len(links)
                ) for filename, links in sorted(filenames.items())
            ]),
            len(filenames)
        ) for domain, filenames in sorted(data.items())])
        f.write(html_template.substitute(title="Domains", body=body))

def write_index_html(base_dir, out_file):
    with open(os.path.join(base_dir, out_file), "w") as f:
        content = "".join(
            [make_list_link(page) for page in ["pdfs.html", "domains.html"]]
        )
        f.write(html_template.substitute(title="Home", body=content))

def make_link(link):
    return "<a href='" + link + "'>" + link + "</a>"

def make_list_link(link):
    return "<li>" + make_link(link) + "</li>"

def make_section(title, content, content_len):
    return Template("""
    <li class="collapsible">
        <b>$title ($content_len)</b><br />
        <ul>
            $content
        </ul>
    </li>
    """).substitute(title=title, content=content, content_len=content_len)

def usage():
    print("Usage: python3 pdf2links.py <pdf_dir>")
    sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        usage()
    else:
        pdf_dir = sys.argv[1]
        if os.path.isdir(pdf_dir) and os.path.exists(pdf_dir):
            run(pdf_dir)
