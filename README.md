<img width="607" height="376" alt="image" src="https://github.com/user-attachments/assets/4be68293-3e2b-4336-80e0-dc8c9425b6e6" /><img width="607" height="376" alt="image" src="https://github.com/user-attachments/assets/c18b69e4-b666-456d-9a81-81ba6a5ff043" /># Data Sync Pipeline (DSP)

An automated pipeline that ingests Help Center articles via the Zendesk API, normalizes HTML into clean Markdown, and synchronizes only changed content (using MD5 hashing) to Google Gemini's Vector Store.

---

## 🧠 Chunking Strategy

This project uses the **Google Gemini File API (`google-genai`)** together with the native **FileSearch** tool. Therefore, chunking and embedding are handled automatically by Google's infrastructure.

### Document Level
- Each Zendesk Help Center article is scraped, cleaned, and converted into an individual `.md` file.

### System Level
- Gemini's internal RAG mechanism automatically splits uploaded Markdown files into semantically meaningful chunks (based on headings and paragraphs) and generates embeddings for accurate retrieval.

---

## ⚙️ Setup

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPO_URL>
cd <YOUR_REPO_NAME>
```

### 2. Create a Virtual Environment & Install Dependencies

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root based on `.env.sample`.

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_STORE_NAME=your_file_search_store_id_here
```

---

## 🚀 Running the Project Locally

### 1. Run the Scraper & Delta Uploader

This pipeline:

- Fetches Zendesk articles
- Cleans HTML into Markdown
- Detects changes using MD5 hashing
- Uploads only new or modified documents to the Gemini Vector Store

```bash
python main.py
```

### Run with Docker (Optional)

```bash
docker build -t dsp-job .

docker run --env-file .env dsp-job
```

---

### 2. Test the AI Assistant (OptiBot)

Launch the assistant connected to the Gemini Vector Store.

```bash
python test_bot.py
```

---

## ☁️ Daily Job Logs

The scraper is containerized with Docker and deployed to **Railway** as a scheduled Cron Job.

**Schedule**

- Runs every day at **00:00**

**Behavior**

- Detects newly added articles
- Detects updated articles
- Skips unchanged articles
- Completes successfully with exit code `0`

**Latest Deployment Logs**

[View Railway Deployment Logs](https://railway.com/project/2ce287bb-b8f8-44c8-ba08-b564032715ab/service/6cd3c528-deb4-4d74-b12c-1717614fa447?environmentId=40f98510-3f6d-45fe-a5e7-6903efb79ac6&id=860b4359-911c-40cc-bde8-ad37e01db602#deploy)

---

## 📸 Assistant Screenshot

The image below demonstrates the assistant successfully answering the sample question:

> **"How do I add a YouTube video?"**

The response includes the correct answer along with citations from the indexed knowledge base.

![Assistant Demo](https://github.com/user-attachments/assets/0bd8f357-3f42-4b1e-be70-9b3e93dc022a)
