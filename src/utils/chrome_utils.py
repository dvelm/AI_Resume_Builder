import os
import time
import random
import tempfile
from src.logging import logger
from src.utils.loading_template import get_loading_template

# Try to import undetected_chromedriver, fall back to regular selenium if not available
# Import standard selenium components first
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Try to import undetected_chromedriver
try:
    import undetected_chromedriver as uc
    UNDETECTED_AVAILABLE = True
    logger.info("Using undetected-chromedriver for Cloudflare bypass")
except ImportError:
    UNDETECTED_AVAILABLE = False
    logger.info("undetected-chromedriver not available, using standard selenium")

def chrome_browser_options():
    logger.debug("Setting Chrome browser options")
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")  # Opzionale, utile in alcuni ambienti
    options.add_argument("window-size=1200x800")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-autofill")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-animations")
    options.add_argument("--disable-cache")
    options.add_argument("--incognito")
    options.add_argument("--allow-file-access-from-files")  # Consente l'accesso ai file locali
    options.add_argument("--disable-web-security")         # Disabilita la sicurezza web
    # Aggressive cache disabling
    options.add_argument('--disk-cache-size=0')
    options.add_argument('--media-cache-size=0')
    options.add_experimental_option('prefs', {'profile.default_content_setting_values.cookies': 2}) # Disable cookies
    logger.debug("Using Chrome in incognito mode")

    return options

def get_chrome_version():
    """Get the Chrome version without launching a browser"""
    import re
    import subprocess
    import platform

    try:
        system = platform.system()
        if system == "Windows":
            # Check common Chrome installation paths
            import winreg
            try:
                # Try to get version from registry
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                winreg.CloseKey(key)
                logger.debug(f"Chrome version from registry: {version}")
                return version
            except:
                # Try common installation paths
                paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe"
                ]

                for path in paths:
                    expanded_path = os.path.expandvars(path)
                    if os.path.exists(expanded_path):
                        # Use wmic to get version info
                        escaped_path = expanded_path.replace('\\', '\\\\')
                        cmd = 'wmic datafile where name="' + escaped_path + '" get Version /value'
                        output = subprocess.check_output(cmd, shell=True).decode('utf-8')
                        match = re.search(r'Version=(.+)', output)
                        if match:
                            version = match.group(1).strip()
                            logger.debug(f"Chrome version from wmic: {version}")
                            return version

        elif system == "Darwin":  # macOS
            try:
                output = subprocess.check_output(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'], stderr=subprocess.STDOUT)
                version = re.search(r'Chrome\s+(\d+\.\d+\.\d+\.\d+)', output.decode('utf-8')).group(1)
                return version
            except:
                pass

        elif system == "Linux":
            try:
                output = subprocess.check_output(['google-chrome', '--version'], stderr=subprocess.STDOUT)
                version = re.search(r'Chrome\s+(\d+\.\d+\.\d+\.\d+)', output.decode('utf-8')).group(1)
                return version
            except:
                pass

    except Exception as e:
        logger.warning(f"Failed to get Chrome version: {e}")

    # Return None if we couldn't determine the version
    return None

def init_browser():
    """Initialize a browser with anti-detection capabilities if available"""
    # Get Chrome version without launching a browser
    chrome_version = get_chrome_version()
    version_main = None

    if chrome_version:
        try:
            # Extract major version
            import re
            version_main = int(re.search(r'^\d+', chrome_version).group(0))
            logger.info(f"Detected Chrome version: {chrome_version}, using version_main={version_main}")
        except Exception as e:
            logger.warning(f"Failed to parse Chrome version: {e}")

    try:
        # First try undetected-chromedriver if available
        if UNDETECTED_AVAILABLE:
            try:
                # Configure undetected-chromedriver
                options = uc.ChromeOptions()
                options.add_argument("--start-maximized")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-popup-blocking")
                options.add_argument("--disable-blink-features=AutomationControlled")

                # Add random user agent
                user_agents = [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
                ]
                options.add_argument(f"--user-agent={random.choice(user_agents)}")

                # Try to create undetected Chrome instance
                if version_main:
                    try:
                        # Use the detected version
                        driver = uc.Chrome(options=options, version_main=version_main)
                        logger.debug("Undetected Chrome browser initialized successfully with version matching.")
                        return driver
                    except Exception as version_error:
                        logger.warning(f"Failed to initialize undetected Chrome with version matching: {version_error}")

                # Try without version parameter as fallback
                driver = uc.Chrome(options=options)
                logger.debug("Undetected Chrome browser initialized successfully without version matching.")
                return driver

            except Exception as uc_error:
                logger.warning(f"Failed to initialize undetected Chrome: {uc_error}. Falling back to standard Selenium.")
                # Fall through to standard Selenium

        # Fall back to regular selenium
        options = chrome_browser_options()
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        logger.debug("Standard Chrome browser initialized successfully.")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize browser: {str(e)}")
        raise RuntimeError(f"Failed to initialize browser: {str(e)}")



def create_loading_screen_file(language="English"):
    """
    Create a temporary HTML file with the loading screen.

    Args:
        language (str): The language to use for the loading screen

    Returns:
        str: The path to the temporary HTML file
    """
    # Get the loading screen HTML
    loading_html = get_loading_template(language)

    # Create a temporary file
    temp_dir = tempfile.gettempdir()
    temp_file = os.path.join(temp_dir, f"loading_screen_{int(time.time())}.html")

    # Write the HTML to the file
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(loading_html)

    # Return the file path
    return temp_file

def show_loading_screen(driver, language="English"):
    """
    Show the loading screen in the browser.

    Args:
        driver: The WebDriver instance
        language: The language to use for the loading screen

    Returns:
        str: The path to the loading screen file
    """
    # Create the loading screen file
    loading_file = create_loading_screen_file(language)
    loading_url = f"file:///{loading_file.replace(os.sep, '/')}"

    # Load the loading screen
    driver.get(loading_url)

    # Wait a moment to ensure the loading screen is visible
    time.sleep(1)

    # Register a cleanup function to remove the file when the driver is closed
    driver.execute_script("""
        window.addEventListener('beforeunload', function() {
            // This will be triggered when the page is unloaded
            console.log('Page is being unloaded, cleanup will happen on the Python side');
        });
    """)

    return loading_file

def HTML_to_PDF(html_content, driver, language=None):
    """
    Converte una stringa HTML in un PDF e restituisce il PDF come stringa base64.

    :param html_content: Stringa contenente il codice HTML da convertire.
    :param driver: Istanza del WebDriver di Selenium.
    :param language: Lingua da utilizzare per la schermata di caricamento (non utilizzato in questa funzione).
    :return: Stringa base64 del PDF generato.
    :raises ValueError: Se l'input HTML non è una stringa valida.
    :raises RuntimeError: Se si verifica un'eccezione nel WebDriver.
    """
    # Validazione del contenuto HTML
    if not isinstance(html_content, str) or not html_content.strip():
        raise ValueError("Il contenuto HTML deve essere una stringa non vuota.")

    content_file = None

    try:
        # Create a temporary file for the actual content
        temp_dir = tempfile.gettempdir()
        content_file = os.path.join(temp_dir, f"content_{int(time.time())}.html")

        # Write the HTML content to the file
        with open(content_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Wait for the loading animation to run for a bit (showing progress)
        time.sleep(3)

        # Now load the actual content
        content_url = f"file:///{content_file.replace(os.sep, '/')}"
        driver.get(content_url)

        # Attendi che la pagina si carichi completamente
        time.sleep(3)  # Increased delay for rendering complex CSS

        # Add script to fix blank pages issues (both at beginning and end)
        driver.execute_script("""
            // Remove any extra elements that might cause blank pages
            const emptyElements = document.querySelectorAll('div:empty, p:empty, section:empty');
            emptyElements.forEach(el => el.remove());

            // Fix for blank first page - check if there are any absolutely positioned elements
            const absoluteElements = document.querySelectorAll('*[style*="position: absolute"], *[style*="position:absolute"]');
            absoluteElements.forEach(el => {
                // Convert absolute positioning to relative or static
                el.style.position = 'relative';
                el.style.top = '0';
                el.style.left = '0';
            });

            // Add page-break controls
            const allElements = document.querySelectorAll('body > *');
            if (allElements.length > 0) {
                // Fix first element to prevent blank first page
                const firstElement = allElements[0];
                firstElement.style.pageBreakBefore = 'avoid';
                firstElement.style.breakBefore = 'avoid';
                firstElement.style.marginTop = '0';
                firstElement.style.paddingTop = '0';

                // Fix last element to prevent blank last page
                const lastElement = allElements[allElements.length - 1];
                lastElement.style.pageBreakAfter = 'avoid';
                lastElement.style.breakAfter = 'avoid';
                lastElement.style.marginBottom = '0';
                lastElement.style.paddingBottom = '0';
            }

            // Add styles to prevent blank pages
            const style = document.createElement('style');
            style.textContent = `
                @page { margin: 0.8cm 0.4cm 0.4cm 0.4cm; }
                html, body {
                    margin: 0 !important;
                    padding: 0 !important;
                    height: auto !important;
                    position: static !important;
                }
                body::before, body::after {
                    display: none !important;
                    content: none !important;
                }
                * {
                    page-break-before: avoid !important;
                    page-break-after: avoid !important;
                    break-before: avoid !important;
                    break-after: avoid !important;
                }
            `;
            document.head.appendChild(style);
        """)

        # Wait a moment for the script to take effect
        time.sleep(1)

        # Execute a script to check if the document is ready for printing
        driver.execute_script("""
            // Force layout recalculation
            document.body.getBoundingClientRect();

            // Remove any hidden elements that might cause blank pages
            const hiddenElements = document.querySelectorAll('*[style*="display: none"], *[style*="display:none"], *[style*="visibility: hidden"], *[style*="visibility:hidden"]');
            hiddenElements.forEach(el => el.remove());
        """)

        # Add script to ensure links are preserved in the PDF
        driver.execute_script("""
            // Make sure all links are visible and properly styled for PDF
            const allLinks = document.querySelectorAll('a');
            allLinks.forEach(link => {
                // Ensure links have proper styling
                link.style.color = '#1a56a0';
                link.style.textDecoration = 'underline';

                // Make sure href attribute is preserved
                if (link.getAttribute('href')) {
                    // Force the link to be absolute if it's not
                    if (!link.href.startsWith('http')) {
                        if (link.href.startsWith('#') || link.href === '') {
                            // For placeholder links, use a real URL
                            if (link.textContent.includes('GitHub') || link.parentElement.innerHTML.includes('fa-github')) {
                                link.href = 'https://github.com';
                            } else if (link.textContent.includes('LinkedIn') || link.parentElement.innerHTML.includes('fa-linkedin')) {
                                link.href = 'https://linkedin.com';
                            } else {
                                link.href = 'https://example.com';
                            }
                        }
                    }
                }
            });
        """)

        # Wait a moment for the script to take effect
        time.sleep(1)

        # Esegue il comando CDP per stampare la pagina in PDF
        pdf_base64 = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,          # Includi lo sfondo nella stampa
            "landscape": False,               # Stampa in verticale (False per ritratto)
            "paperWidth": 8.27,               # Larghezza del foglio in pollici (A4)
            "paperHeight": 11.69,             # Altezza del foglio in pollici (A4)
            "marginTop": 0.4,                 # Margine superiore in pollici (ridotto)
            "marginBottom": 0.4,              # Margine inferiore in pollici (ridotto)
            "marginLeft": 0.4,                # Margine sinistro in pollici (ridotto)
            "marginRight": 0.4,               # Margine destro in pollici (ridotto)
            "displayHeaderFooter": False,     # Non visualizzare intestazioni e piè di pagina
            "preferCSSPageSize": False,       # Non preferire le dimensioni della pagina CSS
            "scale": 1.0,                     # Scala al 100%
            "generateDocumentOutline": True,  # Generate document outline to preserve links
            "generateTaggedPDF": True,        # Generate tagged PDF for better accessibility and link preservation
            "transferMode": "ReturnAsBase64"  # Restituire il PDF come stringa base64
        })
        return pdf_base64['data']
    except Exception as e:
        logger.error(f"Si è verificata un'eccezione WebDriver: {e}")
        raise RuntimeError(f"Si è verificata un'eccezione WebDriver: {e}")
    finally:
        # Clean up temporary files
        try:
            if content_file and os.path.exists(content_file):
                os.remove(content_file)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary files: {e}")
