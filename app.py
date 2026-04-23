
import gradio as gr
import nltk
import textstat
import re
import pandas as pd
from datetime import datetime

# Download NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except:
    nltk.download('punkt')
    nltk.download('punkt_tab')

class PromptAnalyzer:
    def __init__(self):
        self.weights = {'clarity': 25, 'specificity': 25, 'context': 20, 'format': 15, 'actionability': 15}

    def analyze_clarity(self, prompt):
        score = 100
        ambiguous = ['something', 'some', 'maybe', 'perhaps']
        for word in ambiguous:
            if word in prompt.lower():
                score -= 10
        try:
            if len(nltk.sent_tokenize(prompt)) > 10:
                score -= 20
        except:
            pass
        return max(0, min(100, score))

    def analyze_specificity(self, prompt):
        score = 50
        patterns = [r'\d+', r'for example', r'must', r'should', r'format']
        for p in patterns:
            if re.search(p, prompt.lower()):
                score += 10
        generic = ['thing', 'stuff', 'whatever']
        for g in generic:
            if g in prompt.lower():
                score -= 5
        return max(0, min(100, score))

    def analyze_context(self, prompt):
        score = 50
        words = len(prompt.split())
        if 50 <= words <= 200:
            score += 20
        elif words < 20:
            score -= 30
        context_words = ['background', 'context', 'as a', 'act as']
        for cw in context_words:
            if cw in prompt.lower():
                score += 10
        return max(0, min(100, score))

    def analyze_format(self, prompt):
        score = 60
        if '\n' in prompt:
            score += 10
        if re.search(r'^\d+\.|•|-', prompt, re.MULTILINE):
            score += 15
        return max(0, min(100, score))

    def analyze_actionability(self, prompt):
        score = 50
        verbs = ['write', 'create', 'explain', 'analyze', 'summarize']
        for v in verbs:
            if v in prompt.lower():
                score += 10
        return max(0, min(100, score))

    def get_overall_score(self, prompt):
        scores = {
            'Clarity': self.analyze_clarity(prompt),
            'Specificity': self.analyze_specificity(prompt),
            'Context': self.analyze_context(prompt),
            'Format': self.analyze_format(prompt),
            'Actionability': self.analyze_actionability(prompt)
        }
        total = (scores['Clarity'] * 0.25 + scores['Specificity'] * 0.25 + 
                 scores['Context'] * 0.20 + scores['Format'] * 0.15 + 
                 scores['Actionability'] * 0.15)
        return total, scores

    def get_rating(self, score):
        if score >= 85: return "EXCELLENT"
        if score >= 70: return "GOOD"
        if score >= 55: return "AVERAGE"
        if score >= 40: return "BELOW AVERAGE"
        return "POOR"

analyzer = PromptAnalyzer()
history = []

def analyze_prompt(prompt):
    if not prompt or prompt.strip() == "":
        return "Please enter a prompt.", "", pd.DataFrame()

    score, scores = analyzer.get_overall_score(prompt)
    rating = analyzer.get_rating(score)

    history.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'prompt': prompt[:50],
        'score': f"{score:.1f}/100",
        'rating': rating
    })

    bar_length = int(score / 5)
    bar = "█" * bar_length + "░" * (20 - bar_length)

    report = f"""
### Overall Score: {score:.1f}/100
Rating: {rating}

Score Bar: [{bar}]

### Detailed Breakdown
- Clarity: {scores['Clarity']:.0f}/100
- Specificity: {scores['Specificity']:.0f}/100
- Context: {scores['Context']:.0f}/100
- Format: {scores['Format']:.0f}/100
- Actionability: {scores['Actionability']:.0f}/100

### Tips
"""
    if score < 70:
        if scores['Clarity'] < 70:
            report += "- Improve clarity\n"
        if scores['Specificity'] < 70:
            report += "- Add specific details\n"
        if scores['Context'] < 70:
            report += "- Provide more context\n"
    else:
        report += "- Great prompt!\n"

    history_df = pd.DataFrame(history[-10:]) if history else pd.DataFrame()
    return report, f"Score: {score:.1f}/100", history_df

# Create Gradio interface
with gr.Blocks(title="Prompt Analyzer") as demo:
    gr.Markdown("# Prompt Effectiveness Analyzer")
    gr.Markdown("Get instant feedback on your prompts!")

    with gr.Row():
        with gr.Column(scale=2):
            prompt_input = gr.Textbox(label="Enter Your Prompt", lines=5)
            analyze_btn = gr.Button("Analyze Prompt")
            clear_btn = gr.Button("Clear")

            gr.Examples(
                examples=[
                    ["Write about AI"],
                    ["Explain machine learning in 3 paragraphs"],
                    ["As an expert, write a detailed analysis"],
                ],
                inputs=prompt_input
            )
        with gr.Column(scale=1):
            output = gr.Markdown("Results will appear here")
            score_display = gr.Markdown("")

    history_display = gr.Dataframe()

    analyze_btn.click(analyze_prompt, inputs=prompt_input, outputs=[output, score_display, history_display])
    clear_btn.click(lambda: ("", "Results will appear here", "", pd.DataFrame()), 
                    outputs=[prompt_input, output, score_display, history_display])

if __name__ == "__main__":
    demo.launch(share=False)
