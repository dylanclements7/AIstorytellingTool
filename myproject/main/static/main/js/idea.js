document.querySelectorAll('.prompt-badge').forEach(badge => {
            badge.addEventListener('click', function() {
                const promptText = this.textContent;
                document.getElementById('storyPrompt').value = promptText;
            });
        });

document.getElementById('regeneratePrompts').addEventListener('click', function() {
    console.log('Regenerate');
});