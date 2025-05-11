# Job Application Automation

The job application automation feature allows you to automatically search for jobs, generate tailored resumes and cover letters, submit applications, and track your job search progress.

## Features

1. **Job Search**: Automatically search for jobs matching your criteria on supported platforms
2. **Resume & Cover Letter Generation**: Create tailored documents for each job application
3. **Application Submission**: Automatically fill out application forms and submit your documents
4. **Application Tracking**: Keep track of all your applications, their status, and follow-up dates
5. **Statistics**: View insights about your job search progress

## Supported Job Boards

- Indeed
- ZipRecruiter

## How to Use

1. Configure your work preferences in `data_folder/work_preferences.yaml` (use the template provided in `data_folder/work_preferences_template.yaml`)
2. Run `python main.py` and select "Run Automated Job Applications"
3. Choose which job boards to use and set a maximum number of applications
4. The system will automatically search for jobs, generate tailored documents, and submit applications
5. Use the "View Application Statistics" and "Manage Existing Applications" options to track your progress

## Configuration

The job application automation can be configured through the `work_preferences.yaml` file. This file allows you to specify:

- Job titles to search for
- Locations
- Experience level
- Remote work preferences
- Companies and titles to avoid
- And more

### Example Configuration

```yaml
# Job search preferences
remote: true
hybrid: true
onsite: false

# Experience level preferences
experience_level:
  internship: true
  entry: true
  associate: true
  mid_senior_level: true
  director: false
  executive: false

# Job titles/positions to search for
positions:
  - "Web Developer"
  - "Frontend Developer"
  - "Full Stack Developer"
  - "Software Engineer"
  - "JavaScript Developer"

# Locations to search in
locations:
  - "Remote"
  - "New York, NY"
  - "San Francisco, CA"

# Skills to highlight (used for job suitability scoring)
skills:
  - "JavaScript"
  - "React"
  - "Node.js"
  - "HTML/CSS"
  - "Python"
  - "SQL"

# Companies to avoid
company_blacklist:
  - "Scam Inc"
  - "MLM Solutions"

# Job titles to avoid
title_blacklist:
  - "Sales Representative"
  - "Commission Only"
  - "Unpaid Internship"
```

## Application Tracking

The application tracking system allows you to:

- View all your applications and their status
- Update application status (applied, interview scheduled, rejected, etc.)
- Add notes to applications
- Set follow-up dates
- View job details
- Get statistics about your job search

## Ethical Considerations

This tool is designed to help job seekers streamline their application process. Please use it responsibly:

- Don't submit more applications than you can reasonably follow up on
- Be honest in your applications and prepared to discuss anything on your resume
- Respect the terms of service of job platforms
- Consider the load your automation places on job sites' servers

## Limitations

- The automation may break if job sites change their layouts or add new anti-bot measures
- Some applications may require manual intervention for complex forms or assessment tests
- The tool cannot guarantee successful applications or interviews

## Handling Cloudflare Protection

Many job boards like Indeed use Cloudflare protection to prevent automated access. This tool includes features to help bypass these protections:

1. **Undetected ChromeDriver**: The tool attempts to use undetected-chromedriver, which is designed to bypass detection mechanisms. To install it, run:
   ```
   pip install -r requirements_job_automation.txt
   ```

2. **Manual CAPTCHA Solving**: When a Cloudflare challenge is detected, the tool will pause and wait for you to manually solve the CAPTCHA in the browser window. Once solved, the automation will continue automatically.

3. **Random User Agents**: The tool uses random user agents to appear more like a regular browser.

The tool includes several advanced features to handle Cloudflare challenges:

1. **Automatic Version Matching**: The tool automatically detects your Chrome browser version and uses a compatible ChromeDriver.

2. **Retry Mechanism**: All operations include automatic retries with exponential backoff to handle temporary failures.

3. **Manual Intervention Mode**: When automated methods fail, the tool will pause and allow you to manually solve CAPTCHAs.

4. **Manual Search Mode**: For sites with strong anti-bot protection like Indeed, the tool offers a manual search mode where:
   - You can browse job listings manually in the browser
   - The tool tracks which jobs you view
   - You can apply to jobs manually while the tool records your applications
   - All applications are still tracked in the application database

### Using Manual Mode

When the tool detects Cloudflare protection, it will offer you two options:

1. **Solve the CAPTCHA manually**: The tool will wait while you solve the CAPTCHA, then continue automatically.

2. **Switch to manual search mode**: The browser will remain open and you can:
   - Search for jobs manually
   - Browse job listings
   - View job details
   - Apply to jobs

The tool will track your activity in the background and record which jobs you view and apply to. This allows you to bypass anti-bot measures while still benefiting from the application tracking features.

If you encounter Cloudflare challenges frequently, consider these additional steps:

- Use a VPN or proxy to change your IP address
- Run the tool less frequently to avoid triggering rate limits
- Consider using a residential proxy service for more reliable access
- Keep your Chrome browser updated to the latest version
- Try running the tool at different times of day (Cloudflare often has stricter rules during peak hours)
