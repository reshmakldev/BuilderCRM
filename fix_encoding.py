import codecs

def convert_encoding(filename):
    try:
        # Try to read as UTF-16 (PowerShell default for >)
        with codecs.open(filename, 'r', 'utf-16') as f:
            content = f.read()
        
        # Write back as UTF-8
        with codecs.open(filename, 'w', 'utf-8') as f:
            f.write(content)
        print("Converted from UTF-16 to UTF-8")
        return
    except UnicodeError:
        pass

    try:
        # Try to read as UTF-8 with BOM
        with codecs.open(filename, 'r', 'utf-8-sig') as f:
            content = f.read()
            
        # Write back as UTF-8 without BOM
        with codecs.open(filename, 'w', 'utf-8') as f:
            f.write(content)
        print("Converted from UTF-8-SIG to UTF-8")
    except UnicodeError:
        print("Could not determine encoding or already UTF-8")

if __name__ == "__main__":
    convert_encoding('data.json')
