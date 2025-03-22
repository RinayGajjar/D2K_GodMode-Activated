import os

import chromadb
from langchain_community.document_loaders import TextLoader, PyPDFLoader, CSVLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


class DocumentProcessor:
    def __init__(self):
        """Initialize document processor with ChromaDB connection and NLP components"""
        # Initialize Chroma connection in client mode
        self.chroma_client = chromadb.Client()

        # Initialize processing components
        self.text_splitter = CharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )

    def process_file(self, file_path: str, file_type: str):
        """Process and store documents in ChromaDB"""
        # Load document
        if file_type == "text/plain":
            loader = TextLoader(file_path)
        elif file_type == "text/csv":
            loader = CSVLoader(file_path)
        elif file_type == "application/pdf":
            loader = PyPDFLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        documents = loader.load()

        # Split text
        chunks = self.text_splitter.split_documents(documents)

        # Store in Chroma
        Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            client=self.chroma_client,
            collection_name="processed_docs",
            collection_metadata={"hnsw:space": "cosine"}
        )

        return chunks