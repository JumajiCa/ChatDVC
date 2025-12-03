# ChatDVC Documentation

## 1. Application Architecture

ChatDVC is a full-stack application designed to assist Diablo Valley College students.

-   **Frontend**: Svelte (Vite-based) - A reactive, modern web interface.
-   **Backend**: Flask (Python) - Handles API requests, database interactions, and LLM communication.
-   **Database**: SQLite - Local storage for user profiles.
-   **AI Engine**: Deepseek LLM (via OpenAI-compatible API) - Provides counseling responses.

## 2. Database & Storage

### Technology
We use **SQLite**, a serverless, file-based database engine. It is lightweight and ideal for single-user or embedded applications like this prototype.

### Integration
-   **ORM**: `Flask-SQLAlchemy` is used to map Python classes (like `User`) to database tables.
-   **Model**: Defined in `app/models.py`.
    -   Stores: Name, Major, Discipline, Grad Date, Counselor Name, and Insite Credentials.

### Security (Encryption)
-   **Sensitive Data**: The `insite_password` is **never stored in plain text**.
-   **Encryption**: We use the `cryptography` library (Fernet symmetric encryption).
-   **Key Management**: An `ENCRYPTION_KEY` is loaded from the environment (`.env`). If not present, a temporary key is generated (warning: data encrypted with a temp key cannot be decrypted after a restart).
    -   **Persistence**: If no env var is found, the key is generated and saved to `encryption.key` in the root directory.
-   **Process**:
    1.  Password arrives via SSL/TLS (in production) to the API.
    2.  Backend encrypts it immediately using `EncryptionManager.encrypt()`.
    3.  Encrypted string is saved to SQLite.
    4.  When needed (e.g., for scraping), it is decrypted via `EncryptionManager.decrypt()`.

### Storage Location
The database file is located at `instance/users.db` (or `users.db` in the root, depending on the Flask instance path configuration).

## 3. Deployment Guide

### Option A: Docker Deployment (Recommended)

We provide a production-ready `Dockerfile` that builds the Svelte frontend and serves it via Nginx alongside the Flask backend.

**Prerequisites:**
-   Docker installed.

**Steps:**

1.  **Build the Image:**
    ```bash
    docker build -t chatdvc:latest .
    ```

2.  **Run the Container:**
    You need to provide the `DEEPSEEK_API_KEY` as an environment variable.
    
    ```bash
    docker run -d \
      -p 80:80 \
      -e DEEPSEEK_API_KEY="your_api_key_here" \
      -v $(pwd)/data:/app/data \
      --name chatdvc_container \
      chatdvc:latest
    ```
    *Note: We mount a volume to `/app/data` if you configured your app to store DB there, otherwise check persistent storage requirements.*

3.  **Access:**
    Open `http://localhost` in your browser.

### Option B: Manual Deployment (VPS/Server)

**Prerequisites:**
-   Python 3.11+
-   Node.js & npm
-   A Deepseek API Key

**Steps:**

1.  **Environment Setup**:
    -   Clone the repository.
    -   Create a `.env` file in the root with:
        ```
        DEEPSEEK_API_KEY=your_key_here
        ENCRYPTION_KEY=generate_a_valid_fernet_key_here
        BASE_URL=https://api.deepseek.com
        ```

2.  **Backend Deployment**:
    -   Create a virtual environment: `python -m venv venv`
    -   Activate it: `source venv/bin/activate`
    -   Install dependencies: `pip install -r requirements.txt`
    -   Use a production WSGI server (like Gunicorn) instead of the dev server:
        ```bash
        gunicorn -w 4 -b 0.0.0.0:5000 main:app
        ```

3.  **Frontend Deployment**:
    -   Navigate to client: `cd client`
    -   Install dependencies: `npm install`
    -   Build for production: `npm run build`
    -   Serve the `build/` folder using Nginx or Apache.

4.  **Reverse Proxy (Nginx)**:
    -   Configure Nginx to serve the frontend static files.
    -   Proxy API requests (`/api/*`) to the Gunicorn backend (localhost:5000).

## 4. Insite Credential Checker

A stub function `verify_insite_credentials` exists in `main.py`.
-   **Current Behavior**: Checks if fields are non-empty.
-   **Future Implementation**: Should integrate Selenium or `requests` to attempt a real login to the DVC Insite portal using the provided credentials.
