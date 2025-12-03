<script lang="ts">
    import { onMount } from 'svelte';
    import { marked } from 'marked';
    import DOMPurify from 'dompurify';

    interface Message {
        role: 'user' | 'bot';
        content: string;
    }

    let question = ""; 
    let messages: Message[] = [];
    let showProfile = false;
    let isLoading = false;
    let isDarkMode = false;

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
                if (data.name) { // Check if we got a valid profile
                    profile = { ...profile, ...data, insite_password: "" }; // Don't populate password
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
        
        const userMsg: Message = { role: 'user', content: question };
        messages = [...messages, userMsg];
        const currentQuestion = question;
        question = "";
        isLoading = true;

        try {
            const response = await fetch('/api/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question: currentQuestion })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            const botMsg: Message = { role: 'bot', content: data.answer };
            messages = [...messages, botMsg];

        } catch (error) {
            console.error("Error fetching from Flask:", error);
            messages = [...messages, { role: 'bot', content: "Error connecting to the server." }];
        } finally {
            isLoading = false;
        }
    }

    onMount(() => {
        fetchProfile();
        messages = [{ role: 'bot', content: "Hello! I'm your DVC Counselor Assistant. How can I help you today?" }];
        
        // Check system preference for dark mode
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
                    <strong>{msg.role === 'user' ? 'You' : 'DVC Bot'}:</strong>
                    <div class="markdown-content">
                        {#if msg.role === 'bot'}
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
</div>

<style>
    .controls {
        display: flex;
        gap: 10px;
    }
</style>
