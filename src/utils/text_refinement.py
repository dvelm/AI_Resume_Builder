"""
Text refinement utilities for improving LLM-generated text quality.
These functions help ensure consistent, high-quality text in generated PDFs.
"""

import re
import unicodedata
from loguru import logger

# Common spelling mistakes and their corrections
COMMON_CORRECTIONS = {
    # Technical terms
    "javascipt": "JavaScript",
    "javascript": "JavaScript",
    "react.js": "React.js",
    "reactjs": "React.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "typescript": "TypeScript",
    "python3": "Python 3",
    "html5": "HTML5",
    "css3": "CSS3",
    "jquery": "jQuery",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "angularjs": "AngularJS",
    "angular.js": "AngularJS",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "nosql": "NoSQL",
    "restful": "RESTful",
    "restful api": "RESTful API",
    "api": "API",
    "apis": "APIs",
    "json": "JSON",
    "xml": "XML",
    "aws": "AWS",
    "amazon web services": "Amazon Web Services",
    "gcp": "GCP",
    "google cloud platform": "Google Cloud Platform",
    "azure": "Azure",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "bitbucket": "Bitbucket",
    "ci/cd": "CI/CD",
    "devops": "DevOps",
    "agile": "Agile",
    "scrum": "Scrum",
    "kanban": "Kanban",
    "jira": "Jira",
    "trello": "Trello",
    "figma": "Figma",
    "adobe xd": "Adobe XD",
    "photoshop": "Photoshop",
    "illustrator": "Illustrator",

    # Common business terms
    "ecommerce": "e-commerce",
    "e commerce": "e-commerce",
    "saas": "SaaS",
    "software as a service": "Software as a Service",
    "paas": "PaaS",
    "platform as a service": "Platform as a Service",
    "iaas": "IaaS",
    "infrastructure as a service": "Infrastructure as a Service",
    "b2b": "B2B",
    "b2c": "B2C",
    "roi": "ROI",
    "kpi": "KPI",
    "kpis": "KPIs",
    "seo": "SEO",
    "sem": "SEM",
    "crm": "CRM",
    "erp": "ERP",

    # Common grammar/spelling mistakes
    "i": "I",
    "dont": "don't",
    "doesnt": "doesn't",
    "didnt": "didn't",
    "cant": "can't",
    "wont": "won't",
    "shouldnt": "shouldn't",
    "couldnt": "couldn't",
    "wouldnt": "wouldn't",
    "isnt": "isn't",
    "arent": "aren't",
    "wasnt": "wasn't",
    "werent": "weren't",
    "havent": "haven't",
    "hasnt": "hasn't",
    "hadnt": "hadn't",
    "ive": "I've",
    "youve": "you've",
    "weve": "we've",
    "theyve": "they've",
    "im": "I'm",
    "youre": "you're",
    "hes": "he's",
    "shes": "she's",
    "its": "it's",  # Only when used as contraction, not possessive
    "were": "we're",  # Only when used as contraction, not past tense
    "theyre": "they're",
    "theres": "there's",
    "heres": "here's",
    "wheres": "where's",
    "whats": "what's",
    "whos": "who's",
    "thats": "that's",
    "whens": "when's",
    "whys": "why's",
    "hows": "how's",

    # Common typos
    "teh": "the",
    "adn": "and",
    "waht": "what",
    "taht": "that",
    "ahve": "have",
    "owrk": "work",
    "expreience": "experience",
    "experiance": "experience",
    "expereince": "experience",
    "recieve": "receive",
    "recieved": "received",
    "acheive": "achieve",
    "acheived": "achieved",
    "accomodate": "accommodate",
    "acommodate": "accommodate",
    "definately": "definitely",
    "definatly": "definitely",
    "developement": "development",
    "developped": "developed",
    "occured": "occurred",
    "occurance": "occurrence",
    "refered": "referred",
    "referance": "reference",
    "relevent": "relevant",
    "seperate": "separate",
    "seperately": "separately",
    "succesful": "successful",
    "succesfully": "successfully",
    "untill": "until",
    "useable": "usable",
}

def refine_text(text):
    """
    Refines text by correcting common spelling mistakes, improving formatting,
    and ensuring consistent capitalization.

    Args:
        text (str): The text to refine

    Returns:
        str: The refined text
    """
    if not text:
        return text

    # Log the original text for debugging
    logger.debug(f"Original text: {text}")

    # Normalize unicode characters
    text = unicodedata.normalize('NFKC', text)

    # Fix common spelling mistakes and ensure proper capitalization
    words = re.findall(r'\b\w+\b|\W+', text)
    for i, word in enumerate(words):
        # Skip non-word tokens
        if not re.match(r'\b\w+\b', word):
            continue

        # Check for common corrections (case-insensitive)
        lower_word = word.lower()
        if lower_word in COMMON_CORRECTIONS:
            words[i] = COMMON_CORRECTIONS[lower_word]

    # Rejoin the words
    text = ''.join(words)

    # Ensure proper sentence capitalization
    text = re.sub(r'(?<=[\.\?\!]\s)([a-z])', lambda m: m.group(1).upper(), text)

    # Ensure first character of text is capitalized
    if text and text[0].isalpha() and text[0].islower():
        text = text[0].upper() + text[1:]

    # Fix spacing issues
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    text = re.sub(r'\s([.,;:!?])', r'\1', text)  # Remove space before punctuation
    text = re.sub(r'([.,;:!?])([^\s\d])', r'\1 \2', text)  # Add space after punctuation if not followed by space or digit

    # Fix bullet points formatting
    text = re.sub(r'•\s*', '• ', text)  # Ensure consistent spacing after bullet points

    # Fix dash formatting
    text = re.sub(r'\s-\s', ' - ', text)  # Ensure consistent spacing around dashes

    # Fix quotation marks
    text = re.sub(r'(?<!\w)"(?=\w)', ' "', text)  # Add space before opening quotation if needed
    text = re.sub(r'(?<=\w)"(?!\w)', '" ', text)  # Add space after closing quotation if needed

    # Log the refined text for debugging
    logger.debug(f"Refined text: {text}")

    return text.strip()

def refine_html_content(html_content):
    """
    Refines text within HTML content while preserving HTML tags.

    Args:
        html_content (str): The HTML content to refine

    Returns:
        str: The refined HTML content
    """
    if not html_content:
        return html_content

    # Log the original HTML for debugging
    logger.debug(f"Original HTML length: {len(html_content)}")

    # Process text within HTML tags while preserving the tags
    def replace_text_in_tags(match):
        tag_content = match.group(2)
        # Only process if the content is not another HTML tag
        if not re.match(r'^\s*<', tag_content) and not re.match(r'>\s*$', tag_content):
            tag_content = refine_text(tag_content)
        return match.group(1) + tag_content + match.group(3)

    # Find text between HTML tags and refine it
    pattern = r'(>)([^<>]*?)(<)'
    html_content = re.sub(pattern, replace_text_in_tags, html_content)

    # Process text within attributes
    def replace_text_in_attributes(match):
        attr_name = match.group(1)
        attr_value = match.group(2)
        # Only refine certain attributes that might contain natural language
        if attr_name.lower() in ['title', 'alt', 'placeholder', 'aria-label']:
            attr_value = refine_text(attr_value)
        return f'{attr_name}="{attr_value}"'

    # Find attribute values and refine them if appropriate
    pattern = r'(\w+)="([^"]*)"'
    html_content = re.sub(pattern, replace_text_in_attributes, html_content)

    # Fix position and employment_period spacing issues
    html_content = fix_position_employment_period_spacing(html_content)

    # Fix personal information formatting issues
    html_content = fix_personal_information_formatting(html_content)

    # Log the refined HTML for debugging
    logger.debug(f"Refined HTML length: {len(html_content)}")

    return html_content

def fix_position_employment_period_spacing(html_content):
    """
    Specifically fixes spacing issues between position and employment_period in resume HTML.

    Args:
        html_content (str): The HTML content to fix

    Returns:
        str: The fixed HTML content
    """
    if not html_content:
        return html_content

    # Pattern to find entry-title and entry-year spans that are adjacent without proper spacing
    pattern = r'(<span class="entry-title">.*?</span>)(<span class="entry-year">)'

    # Replace with a space between the spans
    replacement = r'\1 \2'

    # Apply the fix
    fixed_html = re.sub(pattern, replacement, html_content)

    # Also fix cases where there might be a period or other character between them
    pattern2 = r'(<span class="entry-title">.*?</span>)([^\s<]*)(<span class="entry-year">)'
    replacement2 = r'\1 \3'
    fixed_html = re.sub(pattern2, replacement2, fixed_html)

    return fixed_html

def fix_personal_information_formatting(html_content):
    """
    Fixes formatting issues in personal information section:
    1. Ensures proper email formatting (removes spaces in domain)
    2. Ensures proper spacing after colons in labels

    Args:
        html_content (str): The HTML content to fix

    Returns:
        str: The fixed HTML content
    """
    if not html_content:
        return html_content

    # Fix email formatting - remove spaces in email domains
    # Pattern to find email addresses with spaces in the domain part
    email_pattern = r'([\w\.-]+@)[\s]*([a-zA-Z0-9\.-]+)[\s]*\.[\s]*([a-zA-Z]{2,})'

    # Replace with properly formatted email (no spaces)
    email_replacement = r'\1\2.\3'

    # Apply the email fix
    fixed_html = re.sub(email_pattern, email_replacement, html_content)

    # Fix spacing after colons in personal information labels
    # Pattern to find labels with missing space after colon
    colon_pattern = r'(font-weight: bold;">.*?:)(\s*)(.*?</span>)'

    # Replace with proper spacing after colon
    colon_replacement = r'\1 \3'

    # Apply the colon spacing fix
    fixed_html = re.sub(colon_pattern, colon_replacement, fixed_html)

    return fixed_html
