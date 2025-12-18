***

# ChatDVC
#### Video Demo: https://youtu.be/QkSqo8_A314

#### Description:

**ChatDVC** is an intelligent, AI-powered counselor assistant designed specifically for students of Diablo Valley College (DVC). It serves as a bridge between the modern student's expectation for instant, conversational information and the reality of legacy educational portals.

The primary problem ChatDVC solves is the friction involved in accessing essential academic data. To find a simple "Priority Registration Date" or a live "Course Schedule," a student typically has to navigate the district's "InSite" portal, perform a multi-step login, handle Two-Factor Authentication (2FA), and click through several nested menus. ChatDVC automates this entire process. It provides a chat interface where a student can simply ask, "When do I register?" or "What is my schedule?", and the system performs the browser automation in the background, parses the complex HTML data, and uses a Large Language Model (DeepSeek) to present the information in a clear, conversational format.

### Project Architecture

The project is built as a full-stack web application.
*   **Backend:** Python with **Flask**. It handles the API endpoints, database interactions, and runs the Selenium automation script.
*   **Frontend:** **Svelte** (via Vite). It provides a reactive, modern user interface that handles real-time chat, Markdown rendering, and dynamic modals for security verifications.
*   **Database:** **SQLite** with **SQLAlchemy**. It stores user profiles and encrypted credentials locally.
*   **AI Engine:** **DeepSeek API**. It processes natural language queries and formats the raw scraped data into human-readable responses.

### File Descriptions

The project structure was carefully organized to separate concerns between the web server, the automation service, and the data models.

#### `app/routes.py`
This file serves as the central controller of the backend. It defines the Flask Blueprint and manages the HTTP endpoints (`/api/ask`, `/api/user`, `/api/submit_2fa`).
*   **Logic Flow:** When a user asks a question, `routes.py` analyzes the text for keywords (e.g., "schedule", "register"). If detected, it triggers the automation service.
*   **2FA Orchestration:** Crucially, this file handles the logic for the "2FA Pause." If the scraping service reports that a code is required, `routes.py` returns a specific JSON signal (`action_required: "2fa_input"`) to the frontend instead of an answer, pausing the conversation until the user provides the code.

#### `app/insite_service.py`
This is the most complex file in the project, containing the logic for the **Selenium WebDriver**. Unlike a standard stateless REST API, this service is stateful.
*   **Browser Management:** It maintains a dictionary of active Chrome driver instances, allowing the browser to stay open in the backend memory while waiting for the user to input a 2FA code on the frontend.
*   **Scraping Logic:** It contains robust parsing algorithms designed to handle the specific, nested table structure of the InSite portal. It uses JavaScript execution within Python (`driver.execute_script`) to accurately locate course titles relative to their container tables—a solution derived after standard XPath selectors failed to handle dynamic DOM elements.
*   **Cookie Persistence:** To improve performance, it serializes session cookies to local JSON files (`user_cookies/`). This allows the system to bypass the login screen entirely on subsequent requests.

#### `app/models.py`
This file defines the database schema using SQLAlchemy.
*   **User Class:** It represents the student. It stores standard fields (Name, Major, Counselor) and the sensitive InSite credentials.
*   **Security:** It is designed to work with the encryption utilities; passwords are never stored in plain text, ensuring that even if the database file is accessed, the credentials remain secure.

#### `app/utils/encryption.py` (and `__init__.py`)
This module handles the security cryptography. It uses the `cryptography` library (Fernet) to encrypt the user's portal password before saving it to the database and decrypts it only momentarily when the Selenium driver needs to perform a login operation.

#### `src/routes/+page.svelte`
The main frontend file built with Svelte.
*   **Reactive State:** It manages the chat history, the "isLoading" states, and the visibility of the Profile and 2FA modals.
*   **2FA Modal:** This component listens for the specific API flag from the backend. When triggered, it interrupts the chat flow to present a high-priority overlay, asking the user for their email code.
*   **Markdown Rendering:** It integrates `marked` and `dompurify` to safely render the AI's rich-text responses (lists, bold text) into HTML.

### Design Choices and Trade-offs

#### 1. Selenium vs. HTTP Requests
The most significant design decision was choosing **Selenium** (browser automation) over standard HTTP libraries like `requests` or `BeautifulSoup`.
*   *The Trade-off:* Selenium is slower and resource-intensive because it loads a full Chromium browser instance.
*   *The Reason:* The 4CD InSite portal is a legacy ASP.NET application that relies heavily on server-side session state, JavaScript postbacks, and dynamic ID generation. A simple HTTP request could not handle the complex 2FA redirection flow or the JavaScript-rendered tables. Browser automation was the only reliable way to mimic a real user interaction.

#### 2. Handling Stateful 2FA in a Stateless Web Server
Web servers (Flask) are designed to be stateless—a request comes in, a response goes out, and the connection closes. However, the login process requires a "pause":
1.  Enter Username/Password.
2.  **Wait** for the user to check their email.
3.  Enter Code.
4.  Resume.

I debated using WebSockets for this, but decided on a **Polling/Signal** architecture for simplicity and robustness. The backend keeps the browser "alive" in a global dictionary variable (`self.active_drivers`). When 2FA is hit, the server responds immediately to the frontend saying "I'm waiting." The frontend then sends a *new* HTTP POST request with the code. The backend looks up the active browser instance by User ID and resumes typing in that specific window. This design allowed me to maintain a clean RESTful API structure while supporting a multi-step, stateful process.

#### 3. DeepSeek Integration
I chose to integrate the **DeepSeek API** rather than using regex or hard-coded string templates to answer questions.
*   *Reasoning:* The scraped data is raw and messy (e.g., "COMM-163 | M W | DVC"). A regex solution would be brittle and hard to maintain if the school changed the table format. By feeding the raw text into an LLM with a system prompt ("You are a helpful counselor..."), the system becomes resilient. It can figure out that "M W" means "Mondays and Wednesdays" without me writing specific parsing logic for every edge case.

#### 4. Svelte & Vite
I chose **Svelte** over Jinja2 (Flask's default templating engine) because I wanted a highly reactive Single Page Application (SPA) feel. The chat interface needs to update instantly, and the 2FA modal needs to appear without a page reload. Svelte's simplified syntax and compiled nature made the frontend lightweight and fast, providing a much smoother user experience than server-side rendering could offer.

#### 5. Local Cookie Storage
To mitigate the slowness of Selenium, I implemented a cookie caching mechanism. Logging in takes 10-15 seconds. By dumping the authenticated cookies to `user_cookies/*.json` and reloading them on the next request, the response time for subsequent queries drops from ~15 seconds to ~2 seconds. This was a critical optimization for user experience.

### Conclusion
ChatDVC represents a complex integration of modern AI, full-stack web development, and legacy system automation. It solves a real-world frustration for students by abstracting away administrative tedium behind a friendly, intelligent interface.