<script>
    let question = ""; // Binds to the text input
    let answer = "Ask a question and I'll send it to Flask...";

    async function askQuestion() {
        try {
            const response = await fetch('http://localhost:5000/api/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question: question })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            answer = data.answer; // Display the answer from Flask

        } catch (error) {
            console.error("Error fetching from Flask:", error);
            answer = "Error connecting to the Flask backend.";
        }
    }
</script>

<h1>ChatDVC!!</h1>
<div class="chat-window">
    <p><strong>Bot:</strong> {answer}</p>
</div>

<input type="text" bind:value={question} placeholder="Type your question..." />
<button on:click={askQuestion}>Send</button>

<style>
    /* Add some basic styles here */
</style>
