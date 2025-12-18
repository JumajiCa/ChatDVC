<script lang="ts">
    import { onMount } from 'svelte';
    import { marked } from 'marked';
    import DOMPurify from 'dompurify';

    interface Message {
        role: 'user' | 'bot' | 'system';
        content: string;
    }

    let question = "";
    let lastQuestion = ""
    let messages: Message[] = [];
    let showProfile = false;
    let isLoading = false;
    let isDarkMode = false;

    // --- New State for 2FA ---
    let is2FAModalOpen = false;
    let twoFACode = "";
    let isVerifying = false;

    // Profile Data
    let profile = {
        name: "",
        insite_username: "",
        insite_password: "",
        major: "",
        discipline: "",
        expected_grad_date: "",
        counselor: ""
    };

    function toggleTheme() {
        isDarkMode = !isDarkMode;
        if (isDarkMode) {
            document.body.setAttribute('data-theme', 'dark');
        } else {
            document.body.removeAttribute('data-theme');
        }
    }

    function renderMarkdown(content: string): string {
        const rawHtml = marked.parse(content);
        return DOMPurify.sanitize(rawHtml as string);
    }

    async function fetchProfile() {
        try {
            const res = await fetch('/api/user');
            if (res.ok) {
                const data = await res.json();
                if (data.name) {
                    profile = { ...profile, ...data, insite_password: "" };
                }
            }
        } catch (e) {
            console.error("Failed to load profile", e);
        }
    }

    async function saveProfile() {
        try {
            const res = await fetch('/api/user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(profile)
            });
            if (res.ok) {
                alert("Profile saved!");
                showProfile = false;
            } else {
                alert("Failed to save profile.");
            }
        } catch (e) {
            console.error("Error saving profile", e);
        }
    }

    async function askQuestion() {
        if (!question.trim()) return;

        lastQuestion = question;

        const userMsg: Message = { role: 'user', content: question };
        messages = [...messages, userMsg];
        const currentQuestion = question;
        question = "";
        isLoading = true;

        try {
            const response = await fetch('/api/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: currentQuestion })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            const botMsg: Message = { role: 'bot', content: data.answer };
            messages = [...messages, botMsg];

            // --- CHECK FOR 2FA REQUEST ---
            if (data.action_required === '2fa_input') {
                is2FAModalOpen = true;
            }

        } catch (error) {
            console.error("Error fetching from Flask:", error);
            messages = [...messages, { role: 'bot', content: "Error connecting to the server." }];
        } finally {
            isLoading = false;
        }
    }

    // --- New Function to Submit Code ---
    async function submit2FA() {
        if (!twoFACode) return;
        isVerifying = true;

        try {
            const res = await fetch('/api/submit_2fa', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: twoFACode })
            });

            const data = await res.json();

            // Close modal
            is2FAModalOpen = false;
            twoFACode = "";
            if (data.success) {
                // SUCCESS!
                messages = [...messages, { role: 'system', content: "Verification successful. Retrieving data..." }];

                // AUTOMATICALLY RE-ASK THE LAST QUESTION
                // We fake a loading state and call the API directly
                isLoading = true;
                const retryRes = await fetch('/api/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: lastQuestion })
                });

                const retryData = await retryRes.json();
                messages = [...messages, { role: 'bot', content: retryData.answer }];
                isLoading = false;

            } else {
                messages = [...messages, { role: 'system', content: `Verification failed: ${data.message}` }];
            }

        } catch (e) {
            console.error(e);
            alert("Error submitting code");
        } finally {
            isVerifying = false;
        }
    }

    onMount(() => {
        fetchProfile();
        messages = [{ role: 'bot', content: "Hello! I'm your DVC Counselor Assistant. How can I help you today?" }];
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            toggleTheme();
        }
    });
</script>

<div class="container">
    <div class="header">
        <h1>ChatDVC ⚜️</h1>
        <div class="controls">
            <button class="secondary" on:click={toggleTheme} aria-label="Toggle Dark Mode">
                {isDarkMode ? '☀️ Fresco' : '🌑 Chiaroscuro'}
            </button>
            <button class="secondary" on:click={() => showProfile = !showProfile}>
                {showProfile ? '📜 Back to Chat' : '✍️ Edit Profile'}
            </button>
        </div>
    </div>

    {#if showProfile}
        <div class="card">
            <h2>Student Profile Ledger</h2>
            <p style="margin-bottom: 20px; font-style: italic;">Enter your details to guide the counsel.</p>

            <div class="profile-form">
                <div>
                    <label for="name">Full Name</label>
                    <input id="name" type="text" bind:value={profile.name} placeholder="Jane Doe" />
                </div>

                <div>
                    <label for="grad">Expected Graduation</label>
                    <input id="grad" type="text" bind:value={profile.expected_grad_date} placeholder="Spring 2026" />
                </div>

                <div>
                    <label for="major">Major</label>
                    <input id="major" type="text" bind:value={profile.major} placeholder="Computer Science" />
                </div>

                <div>
                    <label for="discipline">Discipline</label>
                    <input id="discipline" type="text" bind:value={profile.discipline} placeholder="STEM" />
                </div>

                <div class="full-width">
                    <label for="counselor">Current Counselor</label>
                    <input id="counselor" type="text" bind:value={profile.counselor} placeholder="Dr. Smith" />
                </div>

                <div style="margin-top: 10px;" class="full-width">
                    <h3>Insite Credentials</h3>
                    <p style="font-size: 0.8rem; margin-bottom: 10px;">Used securely for automated tasks.</p>
                </div>

                <div>
                    <label for="username">Insite Username</label>
                    <input id="username" type="text" bind:value={profile.insite_username} />
                </div>

                <div>
                    <label for="password">Insite Password</label>
                    <input id="password" type="password" bind:value={profile.insite_password} placeholder="Set new password..." />
                </div>

                <div class="full-width" style="margin-top: 10px; text-align: right;">
                    <button on:click={saveProfile}>Seal Profile</button>
                </div>
            </div>
        </div>
    {:else}
        <div class="chat-window">
            {#each messages as msg}
                <div class="message {msg.role}">
                    <strong>{msg.role === 'user' ? 'You' : (msg.role === 'system' ? 'System' : 'DVC Bot')}:</strong>
                    <div class="markdown-content">
                        {#if msg.role === 'bot' || msg.role === 'system'}
                            {@html renderMarkdown(msg.content)}
                        {:else}
                            {msg.content}
                        {/if}
                    </div>
                </div>
            {/each}
            {#if isLoading}
                <div class="message bot"><em>Scrivening...</em></div>
            {/if}
        </div>

        <div class="input-area">
            <input
                type="text"
                bind:value={question}
                placeholder="Inquire about classes, registration, or campus life..."
                on:keydown={(e) => e.key === 'Enter' && askQuestion()}
            />
            <button on:click={askQuestion}>Send</button>
        </div>
    {/if}

    <!-- 2FA POPUP MODAL -->
    {#if is2FAModalOpen}
        <div class="modal-overlay">
            <div class="modal card">
                <h3>🔐 Security Verification</h3>
                <p>I am logging into the 4CD Portal. Please enter the 4-digit code sent to your email.</p>

                <input
                    type="text"
                    bind:value={twoFACode}
                    placeholder="1234"
                    maxlength="4"
                    style="font-size: 1.5rem; letter-spacing: 5px; text-align: center; width: 150px; margin: 15px auto;"
                />

                <div class="modal-actions">
                    <button class="secondary" on:click={() => is2FAModalOpen = false}>Cancel</button>
                    <button on:click={submit2FA} disabled={isVerifying}>
                        {isVerifying ? 'Verifying...' : 'Submit Code'}
                    </button>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    .controls {
        display: flex;
        gap: 10px;
    }

    /* Modal Styles */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(2px);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }

    .modal {
        max-width: 400px;
        text-align: center;
        display: flex;
        flex-direction: column;
        border: 2px solid var(--primary-color, #4a90e2);
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }

    .modal-actions {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        margin-top: 15px;
    }

    /* System Message Style */
    .message.system {
        background-color: #fff3cd;
        color: #856404;
        font-style: italic;
        border-left: 4px solid #ffeeba;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
    }
</style>
