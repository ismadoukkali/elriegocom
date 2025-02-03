import re
import markdown
from bs4 import BeautifulSoup

class MarkdownToHTML:
    def custom_markdown_to_html(markdown_text):
        # Ensure consistent line breaks in input
        markdown_text = markdown_text.strip()
        markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)
        
        # Convert markdown to initial HTML
        html = markdown.markdown(markdown_text, extensions=['extra'])
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Add classes and formatting
        for tag in soup.find_all(['p', 'ul', 'li']):
            # Add font_8 class to paragraphs and lists
            if tag.name in ['p', 'ul']:
                tag['class'] = tag.get('class', []) + ['font_8']
                
            # Wrap li text in p tags with font_8 class
            if tag.name == 'li':
                content = ''.join(str(c) for c in tag.contents)
                tag.clear()
                p = soup.new_tag('p')
                p['class'] = ['font_8']
                p.append(BeautifulSoup(content, 'html.parser'))
                tag.append(p)
        
        # Convert to string
        html_str = str(soup)
        
        # Add spacing between sections using <br> tags
        # Add space after regular paragraphs and before headers
        html_str = re.sub(r'(</p>)\s*(<p class="font_8"><strong>)', 
                         r'\1\n<p class="font_8"><br></p>\n\2', html_str)
        
        # Add space after lists and before headers
        html_str = re.sub(r'(</ul>)\s*(<p class="font_8"><strong>)', 
                         r'\1\n<p class="font_8"><br></p>\n\2', html_str)
        
        # Add consistent newlines between elements
        html_str = re.sub(r'</p>\s*<p', '</p>\n<p', html_str)
        html_str = re.sub(r'</ul>\s*<p', '</ul>\n<p', html_str)
        html_str = re.sub(r'</p>\s*<ul', '</p>\n<ul', html_str)
        html_str = re.sub(r'</ul>\s*<ul', '</ul>\n<ul', html_str)
        html_str = re.sub(r'</li>\s*<li', '</li>\n  <li', html_str)  # Preserve 2-space indent for list items
        
        # Add proper indentation for list items
        html_str = re.sub(r'<ul class="font_8">\s*<li', '<ul class="font_8">\n  <li', html_str)
        
        # Escape special characters
        special_chars = {
            'á': '\u00e1',
            'é': '\u00e9',
            'í': '\u00ed',
            'ó': '\u00f3',
            'ú': '\u00fa',
            'ñ': '\u00f1'
        }
        
        for char, escaped in special_chars.items():
            html_str = html_str.replace(char, escaped)
        
        return html_str
