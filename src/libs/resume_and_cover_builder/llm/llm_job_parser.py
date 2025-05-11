import os
import tempfile
import textwrap
import re  # For email validation
from src.libs.resume_and_cover_builder.utils import LoggerChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.chat_models import ChatOllama
import config as app_config # Import the main config file
from loguru import logger
from pathlib import Path
from langchain_text_splitters import TokenTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings
# Import Ollama embeddings
from langchain_ollama import OllamaEmbeddings

# Load environment variables from the .env file
load_dotenv()

# Configure the log file
log_folder = 'log/resume/gpt_resume'
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
log_path = Path(log_folder).resolve()
logger.add(log_path / "gpt_resume.log", rotation="1 day", compression="zip", retention="7 days", level="DEBUG")


class LLMParser:
    def __init__(self, llm_client=None, api_key=None):
        """
        Initialize the LLMParser with either a pre-configured LLM client or an API key.

        Args:
            llm_client: A pre-configured LLM client (takes precedence if provided)
            api_key: API key for OpenAI (used only if llm_client is not provided)
        """
        # If a client is directly provided, use it
        if llm_client is not None:
            logger.info("Using provided LLM client")
            self.llm = LoggerChatModel(llm_client)
        else:
            # Otherwise, create a client based on configuration
            logger.info("Creating new LLM client from API key")
            client = None
            if app_config.LLM_MODEL_TYPE == 'ollama':
                logger.info(f"Initializing Ollama client with model: {app_config.LLM_MODEL} and URL: {app_config.LLM_API_URL}")
                client = ChatOllama(
                    model=app_config.LLM_MODEL,
                    base_url=app_config.LLM_API_URL,
                    temperature=0.4
                )
            elif app_config.LLM_MODEL_TYPE == 'openai':
                logger.info(f"Initializing OpenAI client with model: {app_config.LLM_MODEL}")
                client = ChatOpenAI(model_name=app_config.LLM_MODEL, openai_api_key=api_key, temperature=0.4)
            else:
                logger.warning(f"Unsupported LLM_MODEL_TYPE: {app_config.LLM_MODEL_TYPE}. Defaulting to OpenAI.")
                client = ChatOpenAI(model_name=app_config.LLM_MODEL, openai_api_key=api_key, temperature=0.4)

            self.llm = LoggerChatModel(client)

        # Initialize embeddings based on the LLM model type
        try:
            # First, try to use embeddings that match the LLM model type
            if app_config.LLM_MODEL_TYPE == 'ollama':
                logger.info(f"Initializing Ollama embeddings with model: {app_config.LLM_MODEL} and URL: {app_config.LLM_API_URL}")
                try:
                    # Try to use the same model for embeddings
                    self.llm_embeddings = OllamaEmbeddings(
                        model=app_config.LLM_MODEL,
                        base_url=app_config.LLM_API_URL
                    )
                    logger.info("Successfully initialized Ollama embeddings")
                except Exception as ollama_err:
                    logger.error(f"Error initializing Ollama embeddings with model {app_config.LLM_MODEL}: {ollama_err}")
                    # Try with a different model that might be better for embeddings
                    try:
                        logger.info("Trying with nomic-embed-text model for Ollama embeddings")
                        self.llm_embeddings = OllamaEmbeddings(
                            model="nomic-embed-text",
                            base_url=app_config.LLM_API_URL
                        )
                        logger.info("Successfully initialized Ollama embeddings with nomic-embed-text")
                    except Exception as nomic_err:
                        logger.error(f"Error initializing Ollama embeddings with nomic-embed-text: {nomic_err}")
                        raise
            elif app_config.LLM_MODEL_TYPE == 'openai' and api_key:
                logger.info("Initializing OpenAI embeddings")
                self.llm_embeddings = OpenAIEmbeddings(openai_api_key=api_key)
            else:
                # Try to use environment variable for OpenAI
                logger.info("Trying OpenAI embeddings with environment variable")
                self.llm_embeddings = OpenAIEmbeddings()
        except Exception as e:
            logger.error(f"Error initializing primary embeddings: {e}")
            # Fallback to HuggingFace embeddings
            try:
                logger.info("Falling back to HuggingFace embeddings")
                self.llm_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                logger.info("Successfully initialized HuggingFace embeddings")
            except Exception as e2:
                logger.error(f"Error initializing HuggingFace embeddings: {e2}")
                # Create a dummy embeddings class as last resort
                logger.warning("Using dummy embeddings as last resort")

                class DummyEmbeddings(Embeddings):
                    def embed_documents(self, texts):
                        return [[0.0] * 768 for _ in texts]

                    def embed_query(self, text):
                        # text parameter is required by the interface but not used
                        return [0.0] * 768

                self.llm_embeddings = DummyEmbeddings()

        self.vectorstore = None  # Will be initialized after document loading

    @staticmethod
    def _preprocess_template_string(template: str) -> str:
        """
        Preprocess the template string by removing leading whitespaces and indentation.
        Args:
            template (str): The template string to preprocess.
        Returns:
            str: The preprocessed template string.
        """
        return textwrap.dedent(template)

    def set_body_html(self, body_html):
        """
        Retrieves the job description from HTML, processes it, and initializes the vectorstore.
        Args:
            body_html (str): The HTML content to process.
        """
        temp_file_path = None
        try:
            # Save the HTML content to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as temp_file:
                temp_file.write(body_html)
                temp_file_path = temp_file.name

            # Load the document
            try:
                loader = TextLoader(temp_file_path, encoding="utf-8", autodetect_encoding=True)
                document = loader.load()
                logger.debug("Document successfully loaded.")
            except Exception as e:
                logger.error(f"Error during document loading: {e}")
                # Create a simple document from the HTML content directly
                from langchain_core.documents import Document
                document = [Document(page_content=body_html, metadata={"source": "html_content"})]
                logger.info("Created fallback document from HTML content")

            # Split the text into chunks
            text_splitter = TokenTextSplitter(chunk_size=500, chunk_overlap=50)
            all_splits = text_splitter.split_documents(document)
            logger.debug(f"Text split into {len(all_splits)} fragments.")

            # Create the vectorstore using FAISS
            try:
                self.vectorstore = FAISS.from_documents(documents=all_splits, embedding=self.llm_embeddings)
                logger.debug("Vectorstore successfully initialized.")
            except Exception as e:
                logger.error(f"Error during vectorstore creation: {e}")
                # Create a simple in-memory storage as fallback
                logger.info("Creating simple in-memory storage as fallback")
                self.vectorstore = SimpleVectorstore(all_splits)
                logger.debug("Simple vectorstore initialized as fallback.")

        except Exception as e:
            logger.error(f"Error in set_body_html: {e}")
            # Create a minimal fallback vectorstore with the raw HTML
            from langchain_core.documents import Document
            doc = Document(page_content=body_html[:10000], metadata={"source": "html_content"})
            self.vectorstore = SimpleVectorstore([doc])
            logger.warning("Created minimal fallback vectorstore")

        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.debug(f"Temporary file removed: {temp_file_path}")


# Simple in-memory vectorstore implementation for fallback
class SimpleVectorstore:
    def __init__(self, documents):
        self.documents = documents

    def as_retriever(self):
        return self

    def get_relevant_documents(self, query):
        # query parameter is required by the interface but not used in this fallback implementation
        # Just return all documents as fallback
        return self.documents

    def _retrieve_context(self, query: str, top_k: int = 3) -> str:
        """
        Retrieves the most relevant text fragments using the retriever.
        Args:
            query (str): The search query.
            top_k (int): Number of fragments to retrieve.
        Returns:
            str: Concatenated text fragments.
        """
        if not self.vectorstore:
            logger.warning("Vectorstore not initialized. Creating a dummy vectorstore.")
            # Create a dummy vectorstore with a generic message
            from langchain_core.documents import Document
            dummy_doc = Document(
                page_content="No job description available. Please provide a job description.",
                metadata={"source": "dummy"}
            )
            self.vectorstore = SimpleVectorstore([dummy_doc])

        try:
            retriever = self.vectorstore.as_retriever()
            retrieved_docs = retriever.get_relevant_documents(query)

            # Limit to top_k documents if we have more
            if len(retrieved_docs) > top_k:
                retrieved_docs = retrieved_docs[:top_k]

            context = "\n\n".join(doc.page_content for doc in retrieved_docs)
            logger.debug(f"Context retrieved for query '{query}': {context[:200]}...")  # Log the first 200 characters
            return context
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return "Error retrieving job description context. Please try again with a valid job description."

    def _extract_information(self, question: str, retrieval_query: str) -> str:
        """
        Generic method to extract specific information using the retriever and LLM.
        Args:
            question (str): The question to ask the LLM for extraction.
            retrieval_query (str): The query to use for retrieving relevant context.
        Returns:
            str: The extracted information.
        """
        try:
            # Get context with error handling
            context = self._retrieve_context(retrieval_query)

            # Create a prompt template with clear instructions
            prompt = ChatPromptTemplate.from_template(
                template="""
                You are an expert in extracting specific information from job descriptions.
                Carefully read the job description context below and provide a clear and concise answer to the question.
                If the information is not available in the context, respond with "Not specified" or make a reasonable guess based on the available information.

                Context: {context}

                Question: {question}
                Answer:
                """
            )

            # Format the prompt and log it for debugging
            formatted_prompt = prompt.format(context=context, question=question)
            logger.debug(f"Formatted prompt for extraction: {formatted_prompt[:200]}...")  # Log the first 200 characters

            try:
                # Create and invoke the chain
                chain = prompt | self.llm | StrOutputParser()
                result = chain.invoke({"context": context, "question": question})
                extracted_info = result.strip()

                # Log the result and return it
                logger.debug(f"Extracted information: {extracted_info}")
                return extracted_info
            except Exception as e:
                logger.error(f"Error during information extraction: {e}")
                # Return a generic response based on the question
                if "company" in question.lower():
                    return "Unknown Company"
                elif "role" in question.lower() or "title" in question.lower():
                    return "Job Position"
                elif "location" in question.lower():
                    return "Remote"
                elif "description" in question.lower():
                    return "Job description not available. Please provide a valid job description."
                else:
                    return "Information not available"
        except Exception as outer_e:
            logger.error(f"Critical error in _extract_information: {outer_e}")
            return "Error processing job information"

    def extract_job_description(self) -> str:
        """
        Extracts the company name from the job description.
        Returns:
            str: The extracted job description.
        """
        question = "What is the job description of the company?"
        retrieval_query = "Job description"
        logger.debug("Starting job description extraction.")
        return self._extract_information(question, retrieval_query)

    def extract_company_name(self) -> str:
        """
        Extracts the company name from the job description.
        Returns:
            str: The extracted company name.
        """
        question = "What is the company's name?"
        retrieval_query = "Company name"
        logger.debug("Starting company name extraction.")
        return self._extract_information(question, retrieval_query)

    def extract_role(self) -> str:
        """
        Extracts the sought role/title from the job description.
        Returns:
            str: The extracted role/title.
        """
        question = "What is the role or title sought in this job description?"
        retrieval_query = "Job title"
        logger.debug("Starting role/title extraction.")
        return self._extract_information(question, retrieval_query)

    def extract_location(self) -> str:
        """
        Extracts the location from the job description.
        Returns:
            str: The extracted location.
        """
        question = "What is the location mentioned in this job description?"
        retrieval_query = "Location"
        logger.debug("Starting location extraction.")
        return self._extract_information(question, retrieval_query)

    def extract_recruiter_email(self) -> str:
        """
        Extracts the recruiter's email from the job description.
        Returns:
            str: The extracted recruiter's email.
        """
        question = "What is the recruiter's email address in this job description?"
        retrieval_query = "Recruiter email"
        logger.debug("Starting recruiter email extraction.")
        email = self._extract_information(question, retrieval_query)

        # Validate the extracted email using regex
        email_regex = r'[\w\.-]+@[\w\.-]+\.\w+'
        if re.match(email_regex, email):
            logger.debug("Valid recruiter's email.")
            return email
        else:
            logger.warning("Invalid or not found recruiter's email.")
            return ""

