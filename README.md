# Word and Filename Extractor

This script is a command-line tool designed to extract words, hyphenated words, and common filename patterns from either a text file or the HTML content of a URL (or list of URLs). It's useful for **reconnaissance**, **web content analysis**, and **data extraction tasks** in fuzzing, automation, or text processing.

---

## Features

- Extracts:
  - Simple alphanumeric words
  - Hyphenated words
  - Filenames with common extensions (e.g., `.pdf`, `.jpg`, `.php`, `.json`, etc.)
- Supports:
  - Single file input
  - Single URL input
  - Multiple URLs (from a file) with multithreaded requests
- Allows custom HTTP headers for requests

---

## Usage

```bash
python script.py [OPTIONS]
```

### Options

- `-f`, `--file` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Path to a local text file
- `-u`, `--url` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Single URL to fetch content from
- `-l`, `--url_list` &nbsp;&nbsp; File containing a list of URLs (one per line)
- `-t`, `--threads` &nbsp;&nbsp;&nbsp;&nbsp; Number of threads for parallel URL fetching (default: 1)
- `-H`, `--headers` &nbsp;&nbsp;&nbsp; Custom HTTP headers in format `'key1:value1,key2:value2'`

---

## Examples

### Extract from a file:

```bash
python script.py -f input.txt
```

### Extract from a single URL:

```bash
python script.py -u https://example.com
```

### Extract from multiple URLs with 5 threads:

```bash
python script.py -l urls.txt -t 5
```

### Use custom headers:

```bash
python script.py -u https://example.com -H "User-Agent:custom-agent,Accept:text/html"
```

---

## Output

The script prints:
- All extracted words
- All hyphenated words
- All matched filenames with extensions

If a word contains underscores, each component is also printed individually.

---

## Requirements

- Python 3.x
- `requests` library (can be installed via `pip install requests`)

---

## License

This project is released under the MIT License.
