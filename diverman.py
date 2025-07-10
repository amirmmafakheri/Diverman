import argparse
import re
import requests
import concurrent.futures
import sys
from typing import Tuple, List, Set
from io import StringIO

# Pre-compiled regex patterns for performance
WORD_PATTERN = re.compile(r'\b\w+\b')
HYPHEN_PATTERN = re.compile(r'\b\w+(?:-\w+)+\b')

# Optimized file extensions using a set for O(1) lookup
COMMON_EXTENSIONS = {
    '3g2', '3gp', '7z', 'ai', 'aif', 'apk', 'arj', 'asp', 'aspx', 'avi', 
    'bak', 'bat', 'bin', 'bmp', 'cab', 'cda', 'cer', 'cfg', 'cfm', 'cgi', 
    'class', 'cpl', 'cpp', 'css', 'csv', 'cur', 'dat', 'db', 'dbf', 'deb', 
    'dll', 'dmg', 'dmp', 'doc', 'docx', 'drv', 'email', 'eml', 'emlx', 'exe', 
    'flv', 'fnt', 'fon', 'gadget', 'gif', 'git', 'h264', 'hta', 'htm', 'html', 
    'icns', 'ico', 'inc', 'ini', 'iso', 'jar', 'java', 'jhtml', 'jpeg', 'jpg', 
    'js', 'jsa', 'jsp', 'key', 'lnk', 'log', 'm4v', 'mdb', 'mid', 'mkv', 
    'mov', 'mp3', 'mp4', 'mpa', 'mpeg', 'mpg', 'msg', 'msi', 'nsf', 'odp', 
    'ods', 'odt', 'oft', 'ogg', 'ost', 'otf', 'part', 'pcap', 'pdb', 'pdf', 
    'phar', 'php', 'php2', 'php3', 'php4', 'php5', 'php6', 'php7', 'phps', 
    'pht', 'phtml', 'pkg', 'pl', 'png', 'pps', 'ppt', 'pptx', 'ps', 'psd', 
    'pst', 'py', 'rar', 'reg', 'rm', 'rpm', 'rss', 'rtf', 'sav', 'sh', 
    'shtml', 'sql', 'svg', 'swf', 'swift', 'sys', 'tar', 'targz', 'tex', 
    'tif', 'tiff', 'tmp', 'toast', 'ttf', 'txt', 'vb', 'vcd', 'vcf', 'vob', 
    'wav', 'wma', 'wmv', 'wpd', 'wpl', 'wsf', 'xhtml', 'xls', 'xlsm', 'xlsx', 
    'xml', 'z', 'zip', 'json'
}

# Optimized filename pattern - matches word.extension format
FILENAME_PATTERN = re.compile(r'\b\w+\.(\w+)\b')

# HTTP session for connection pooling and performance
session = requests.Session()
session.headers.update({
    'Accept-Encoding': 'gzip, deflate',
    'User-Agent': 'Diverman/1.0 (Word Extractor Tool)'
})

def extract_words_from_text(text: str) -> List[str]:
    """Extract words using pre-compiled regex pattern."""
    return WORD_PATTERN.findall(text)

def extract_words_hyphen_from_text(text: str) -> List[str]:
    """Extract hyphenated words using pre-compiled regex pattern."""
    return HYPHEN_PATTERN.findall(text)

def extract_filenames_from_text(text: str) -> List[str]:
    """Extract filenames with optimized extension checking."""
    filenames = []
    matches = FILENAME_PATTERN.findall(text)
    
    for extension in matches:
        if extension.lower() in COMMON_EXTENSIONS:
            # Reconstruct the full filename from the original text
            pattern = re.compile(rf'\b\w+\.{re.escape(extension)}\b', re.IGNORECASE)
            filename_matches = pattern.findall(text)
            filenames.extend(filename_matches)
    
    return list(set(filenames))  # Remove duplicates

def extract_words_from_url(url: str, headers: dict = None, timeout: int = 30) -> Tuple[List[str], List[str], List[str]]:
    """Extract words from URL with proper error handling and optimization."""
    try:
        # Merge custom headers with session headers
        request_headers = session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        response = session.get(
            url, 
            headers=request_headers, 
            allow_redirects=True,
            timeout=timeout,
            stream=True  # Enable streaming for large responses
        )
        response.raise_for_status()
        
        # Handle large responses efficiently
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB threshold
            print(f"Warning: Large response ({content_length} bytes) from {url}, processing in chunks...")
            text = ""
            for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
                if chunk:
                    text += chunk
                    # Process in chunks to avoid memory issues
                    if len(text) > 1024 * 1024:  # Process every 1MB
                        break
        else:
            text = response.text
        
        words = extract_words_from_text(text)
        hyphen_words = extract_words_hyphen_from_text(text)
        filenames = extract_filenames_from_text(text)
        
        return words, hyphen_words, filenames
        
    except requests.exceptions.Timeout:
        print(f"Timeout error for URL: {url}")
        return [], [], []
    except requests.exceptions.ConnectionError:
        print(f"Connection error for URL: {url}")
        return [], [], []
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error {e.response.status_code} for URL: {url}")
        return [], [], []
    except requests.exceptions.RequestException as e:
        print(f"Request error for URL {url}: {str(e)}")
        return [], [], []
    except Exception as e:
        print(f"Unexpected error for URL {url}: {str(e)}")
        return [], [], []

def process_urls_from_file(file_path: str, num_threads: int, headers: dict = None, timeout: int = 30) -> None:
    """Process multiple URLs with optimized threading and error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            urls = [line.strip() for line in file if line.strip()]
        
        if not urls:
            print("No valid URLs found in the file.")
            return
        
        print(f"Processing {len(urls)} URLs with {num_threads} threads...")
        
        # Collect all results for batch processing
        all_words = set()
        all_hyphen_words = set()
        all_filenames = set()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(extract_words_from_url, url, headers, timeout): url 
                for url in urls
            }
            
            # Process completed tasks
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    words, hyphen_words, filenames = future.result()
                    all_words.update(words)
                    all_hyphen_words.update(hyphen_words)
                    all_filenames.update(filenames)
                except Exception as e:
                    print(f"Failed to process {url}: {str(e)}")
        
        # Batch output for better performance
        print_words_batch(list(all_words))
        print_hyphenated_words_batch(list(all_hyphen_words))
        print_filenames_batch(list(all_filenames))
        
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except PermissionError:
        print(f"Error: Permission denied reading '{file_path}'.")
    except Exception as e:
        print(f"Error processing URL file: {str(e)}")

def print_words_batch(words: List[str]) -> None:
    """Optimized batch printing of words."""
    if not words:
        return
    
    output = StringIO()
    processed_words = set()
    
    for word in words:
        if word not in processed_words:
            output.write(f"{word}\n")
            processed_words.add(word)
            
            # Handle underscore-separated words
            if "_" in word:
                pieces = word.split("_")
                for piece in pieces:
                    if piece and piece not in processed_words:
                        output.write(f"{piece}\n")
                        processed_words.add(piece)
    
    sys.stdout.write(output.getvalue())
    output.close()

def print_words(words: List[str]) -> None:
    """Legacy method for single URL processing."""
    print_words_batch(words)

def print_hyphenated_words_batch(hyphen_words: List[str]) -> None:
    """Optimized batch printing of hyphenated words."""
    if not hyphen_words:
        return
    
    unique_words = set(hyphen_words)
    output = "\n".join(sorted(unique_words)) + "\n"
    sys.stdout.write(output)

def print_hyphenated_words(hyphen_words: List[str]) -> None:
    """Legacy method for single URL processing."""
    print_hyphenated_words_batch(hyphen_words)

def print_filenames_batch(filenames: List[str]) -> None:
    """Optimized batch printing of filenames."""
    if not filenames:
        return
    
    unique_filenames = set(filenames)
    output = "\n".join(sorted(unique_filenames)) + "\n"
    sys.stdout.write(output)

def print_filenames(filenames: List[str]) -> None:
    """Legacy method for single URL processing."""
    print_filenames_batch(filenames)

def process_file_content(file_path: str) -> None:
    """Process local file with memory-efficient reading."""
    try:
        # Check file size for memory optimization
        import os
        file_size = os.path.getsize(file_path)
        
        if file_size > 50 * 1024 * 1024:  # 50MB threshold
            print(f"Warning: Large file ({file_size} bytes), processing in chunks...")
            # For very large files, process in chunks
            words, hyphen_words, filenames = set(), set(), set()
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                chunk_size = 1024 * 1024  # 1MB chunks
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    
                    words.update(extract_words_from_text(chunk))
                    hyphen_words.update(extract_words_hyphen_from_text(chunk))
                    filenames.update(extract_filenames_from_text(chunk))
            
            print_words_batch(list(words))
            print_hyphenated_words_batch(list(hyphen_words))
            print_filenames_batch(list(filenames))
        else:
            # For smaller files, read normally
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
                words = extract_words_from_text(text)
                hyphen_words = extract_words_hyphen_from_text(text)
                filenames = extract_filenames_from_text(text)
                print_words(words)
                print_hyphenated_words(hyphen_words)
                print_filenames(filenames)
                
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except PermissionError:
        print(f"Error: Permission denied reading '{file_path}'.")
    except Exception as e:
        print(f"Error processing file: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description="Extract and display words and filenames from a text file or URL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python diverman.py -f input.txt
  python diverman.py -u https://example.com
  python diverman.py -l urls.txt -t 5
  python diverman.py -u https://example.com -H "User-Agent:custom,Accept:text/html"
        """
    )
    parser.add_argument("-f", "--file", help="Path to the text file.")
    parser.add_argument("-u", "--url", help="URL to retrieve text from.")
    parser.add_argument("-l", "--url_list", help="Path to a file containing a list of URLs.")
    parser.add_argument("-t", "--threads", type=int, default=5, help="Number of threads to use for sending HTTP requests (default: 5).")
    parser.add_argument("-H", "--headers", help="Custom HTTP headers as a string in the format 'key1:value1,key2:value2'")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP request timeout in seconds (default: 30)")
    args = parser.parse_args()

    # Parse custom headers
    headers = {}
    if args.headers:
        try:
            header_list = args.headers.split(",")
            for header in header_list:
                parts = header.split(":", 1)
                if len(parts) == 2:
                    key, value = parts
                    headers[key.strip()] = value.strip()
                else:
                    print(f"Warning: Ignoring invalid header format: {header}")
        except Exception as e:
            print(f"Error parsing headers: {str(e)}")

    # Process based on input type
    if args.file:
        process_file_content(args.file)
    elif args.url:
        words, hyphen_words, filenames = extract_words_from_url(args.url, headers=headers, timeout=args.timeout)
        print_words(words)
        print_hyphenated_words(hyphen_words)
        print_filenames(filenames)
    elif args.url_list:
        process_urls_from_file(args.url_list, args.threads, headers=headers, timeout=args.timeout)
    else:
        print("Error: Please provide either a file path (-f), a URL (-u), or a file containing URLs (-l).")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
