import re

with open('temp_script.js') as f:
    code = f.read()

def find_js_error(code):
    try:
        # A poor man's JS parser using regex to remove strings and comments
        # First remove block comments
        code = re.sub(r'/\*[\s\S]*?\*/', '', code)
        # Then remove line comments
        code = re.sub(r'//.*', '', code)
        
        # Check for unclosed strings
        lines = code.split('\n')
        for i, line in enumerate(lines):
            # very basic check: count quotes (not robust against escaped quotes)
            s_quotes = line.replace("\\'", "").count("'")
            d_quotes = line.replace('\\"', "").count('"')
            # backticks can be multiline, so we count them globally later
            if s_quotes % 2 != 0:
                print(f"Possible unclosed single quote at line {i+1}: {line}")
            if d_quotes % 2 != 0:
                print(f"Possible unclosed double quote at line {i+1}: {line}")
                
        # Check backticks globally
        b_quotes = code.count('`')
        if b_quotes % 2 != 0:
            print("Unclosed backtick ` found in the script!")
            
    except Exception as e:
        print(f"Error parsing: {e}")

find_js_error(code)
