# DocMate: AI-Powered Documentation Assistant  

DocMate is an advanced AI-powered solution designed to streamline project documentation processes by leveraging Retrieval-Augmented Generation (RAG). The application aims to reduce information overload, enhance knowledge retrieval, and improve onboarding efficiency, offering an intuitive and effective way to access and generate project insights.  

---

## Key Features  
- **Intelligent Document Retrieval**: Uses semantic search for precise and contextually relevant information.  
- **Natural Language Interaction**: Allows users to interact with the system through a conversational chatbot interface.  
- **Enhanced Productivity**: Reduces time spent on manual searches and accelerates decision-making.  

---

## Technologies Used  
- **Generative AI**: For understanding and generating natural language responses.  
- **Weaviate**: Vector database for semantic search and document indexing.  
- **AWS SageMaker & S3**: Machine learning model deployment and scalable data storage.  
- **Python**: Backend development and NLP integration.  
- **Chainlit**: User-friendly chatbot interface.  
- **Docker & Kubernetes (EKS)**: For containerization and deployment.  

---

## System Architecture  
1. **Frontend**: Interactive chatbot built using Chainlit.  
2. **Backend**: Python-based API that integrates LLMs, Weaviate, and RAG pipelines.  
3. **Database**: Weaviate for vector storage and semantic search capabilities.  
4. **Deployment**: Dockerized services orchestrated using Kubernetes on AWS EKS.  

---

## Installation and Setup  

### Prerequisites  
- Docker & Docker Compose  
- Python 3.8+  
- Kubernetes cluster (AWS EKS recommended)  

### Installation Steps  
1. Clone this repository:  
   ```bash
   git clone <repository-url>
   cd docmate
