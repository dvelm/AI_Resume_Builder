"""
Improved prompts for resume and cover letter generation.
These prompts are designed to produce higher quality text with fewer errors.
"""

# Translation prompt with quality improvements and technical accuracy
improved_translation_prompt = """
Translate the following text accurately into {language}.
Ensure the translation:
1. Maintains professional terminology and industry-specific vocabulary
2. Uses correct grammar, punctuation, and capitalization
3. Preserves the original meaning and tone
4. Avoids literal word-for-word translation when it would sound unnatural
5. Uses appropriate formal language for a professional document
6. Preserves technical terms, programming languages, and technology names in their original form
7. Adapts industry jargon appropriately for the target language
8. Maintains consistent tense and voice throughout
9. Uses natural phrasing that would be used by native speakers in professional contexts
10. Preserves any numerical data, metrics, or statistics exactly as presented

Text to translate: {text_to_translate}

Output only the translated text, nothing else.
"""

# Resume section generation prompt with quality improvements
improved_section_prompt = """
Act as an expert resume writer with extensive experience in creating professional, error-free content.
Your task is to generate content for a resume section based on the provided information.

Follow these guidelines to ensure high-quality output:
1. Use precise, professional language appropriate for a formal resume
2. Ensure all technical terms, company names, and proper nouns are correctly capitalized
3. Use active voice and strong action verbs
4. Be concise but informative - avoid unnecessary words
5. Maintain consistent tense (past tense for previous positions, present tense for current positions)
6. Check for and eliminate any spelling or grammatical errors
7. Ensure all dates and numbers are formatted consistently
8. Use industry-standard terminology for the applicant's field
9. Highlight achievements with measurable results when possible
10. Avoid clichés, buzzwords, and generic statements

Section information:
{section_info}

Output the content in {language}, formatted according to the template below:
{template}
"""

# Cover letter generation prompt with quality improvements
improved_cover_letter_prompt = """
Act as a professional resume writer with expertise in creating compelling, error-free cover letters.
Your task is to write a concise, impactful cover letter that connects the applicant's experience to the job requirements.

Follow these guidelines to ensure exceptional quality:
1. Use formal, professional language appropriate for business correspondence
2. Ensure perfect grammar, spelling, and punctuation
3. Write in a clear, direct style with no unnecessary words
4. Use active voice and strong, specific verbs
5. Avoid clichés, generic statements, and overused phrases
6. Highlight 2-3 specific qualifications that directly match the job requirements
7. Include measurable achievements when relevant
8. Maintain a confident but not arrogant tone
9. Ensure all technical terms and proper nouns are correctly capitalized
10. Keep paragraphs short and focused (3-5 sentences maximum)
11. Limit the entire letter to 3-4 paragraphs

Job Description:
```
{job_description}
```

Applicant's Resume:
```
{resume}
```

Output the cover letter in {language}, formatted according to the template below:
{template}
"""

# Project description prompt with quality improvements - enhanced for accuracy
improved_project_description_prompt = """
Create 2 professional bullet points for a resume based on this project description:

{project_description}

Guidelines:
- Start each point with a strong action verb in past tense (e.g., Developed, Implemented, Created)
- Highlight specific technical skills, technologies, and tools used
- Include measurable outcomes or impact when possible (e.g., improved efficiency by 30%)
- Keep each point concise (under 100 characters if possible)
- Use professional, industry-standard terminology
- Avoid generic statements - be specific about your contributions
- Ensure perfect grammar and punctuation

Output only the bullet points as HTML <li> elements, one per line, in {language}.
Example format:
<li>Developed a scalable web application using React and Node.js that improved user engagement by 25%</li>
<li>Implemented responsive design patterns and optimized database queries, reducing load time by 40%</li>
"""

# Fallback prompt for very small models or when the main prompt fails
simplified_project_description_prompt = """
Convert this project description into 2 professional bullet points for a resume:

{project_description}

Requirements:
- Use action verbs in past tense
- Be specific about technologies used
- Keep points concise and clear
- Focus on achievements and contributions

Format as HTML <li> elements in {language}.
"""

# Skills section prompt with quality improvements
improved_skills_prompt = """
Act as an expert resume writer specializing in technical skills sections.
Your task is to create a well-organized, professional skills section based on the provided information.

Follow these guidelines to ensure high-quality output:
1. Group similar skills into logical categories (e.g., Programming Languages, Frameworks, Tools)
2. Ensure all technical terms are correctly capitalized and spelled (e.g., JavaScript, React.js, Node.js)
3. List skills in order of relevance to the job description when possible
4. Include only skills that the applicant actually possesses
5. Use consistent formatting throughout the section
6. Avoid subjective skill levels unless specifically provided
7. Ensure perfect grammar, spelling, and punctuation
8. Be concise but comprehensive
9. Use industry-standard terminology
10. Highlight skills that match the job description

Skills Information:
{skills_info}

Job Description (for relevance):
{job_description}

Output the skills section in {language}, formatted according to the template below:
{template}
"""
