# gui.py
import gradio as gr
import random
import string, re, os, json

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Gemini setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

genai.configure(api_key=GEMINI_API_KEY)

from user_profiling import get_user_profile
from suggest_bundles import get_bundles, get_all_bundles, sort_bundles, print_bundles



BUNDLE_TYPES = ["complementary", "thematic", "cross-margin", "personalized", "seasonal"]

def parse_bundle_request_gemini(user_prompt):

    model = genai.GenerativeModel(GEMINI_MODEL)

    prompt = (
        "You are an assistant that extracts structured request parameters for bundle generation.\n\n"
        "Given a user query, extract:\n"
        "- priority: true if there is anything mentioned about high priority\n"
        f"- type: one of {BUNDLE_TYPES}\n"
        "- depth: number of bundles requested (as an integer)\n\n"
        "Respond ONLY in this JSON format:\n"
        '{\n  "priority": true,\n  "type": "thematic",\n  "depth": 3\n}\n\n'
        "User query:\n"
        f"{user_prompt}"
    )

    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        # Extract JSON block from response
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in Gemini response")

        cleaned_json = json_match.group(0)
        parsed = json.loads(cleaned_json)

        return {
            "priority": bool(parsed.get("priority", False)),
            "type": parsed.get("type", "thematic"),
            "depth": int(parsed.get("depth", 1))
        }

    except Exception as e:
        print(f"Gemini API Error: {e}\nRaw Response:\n{response.text if 'response' in locals() else 'No response'}")
        return {
            "priority": False,
            "type": "thematic",
            "depth": 1
        }





# Define your functions
def my_function(user_input): # answer user question

    result = parse_bundle_request_gemini(user_input)
    print(result)

    res = f"I undertand that you want to create {result['depth']} bundles of type '{result['type']} ' with priority set to {result['priority']}.\n Here are the bundles:"

    if result['type'] == "personalized":
        return "Personalized bundles are not supported in this mode. Please use the 'Query' tab to create personalized bundles."

    bundles = get_bundles(type=result['type'], depth=result['depth'], priority=result['priority'])

    bundles = sort_bundles(bundles)

    if not bundles:
        return "No bundles found for the given criteria."

    for b in bundles:
        res += f"<br>Bundle [{b['bundle_type']}] - added profit: ${b['added_profit']:.2f}"
        for product in b['bundle']:
            res += f"<br>    - {product}"

    return res

def my_function_2(random_input, sku_priority, number_input, bundle_type):


    random_input = random_input.strip() if random_input else None
    random_input = int(random_input) if random_input and random_input.isdigit() else None

    if bundle_type == "any":
        bundles, _ = get_all_bundles(userId=random_input, priority=sku_priority, depth=number_input)
    else:
        bundles = get_bundles(type=bundle_type, depth=number_input, userID=random_input, priority=sku_priority)

    bundles = sort_bundles(bundles)


    res = f"{number_input} {bundle_type} bundles (priority: {sku_priority})"
    if random_input:
        res += f" for user {random_input}"

    elif random_input == "":
        return "Please fill in the UserID field or click 'Autofill' for personalized bundles."
    res += ":"

    if not bundles:
        res += "<br>No bundles found for the given criteria."
        return res

    
    for b in bundles:
        res += f"<br>Bundle [{b['bundle_type']}] - added profit: ${b['added_profit']:.2f}"
        for product in b['bundle']:
            res += f"<br>    - {product}"

    return res

# Utility to generate random 8-character string
def generate_random_string():
    users = [44175, 10416]
    return random.choice(users)

# Custom CSS for styling
custom_css = """
textarea, input[type="text"], input[type="number"] {
    border-radius: 8px;
}
textarea.output-box, input.output-box {
    border: none !important;
    background-color: transparent !important;
    box-shadow: none !important;
}
textarea.standout, input.standout {
    border: 2px solid #4f46e5 !important;
    background-color: #eef2ff !important;
}
.inline-checkbox {
    display: flex;
    align-items: center;
    gap: 0.3em;
    margin-top: 0.25em;
}
"""

with gr.Blocks(css=custom_css) as demo:
    with gr.Tab("Chatbot"):
        gr.Markdown("### Ask the chatbot to create a number of bundles")
        gr.Markdown("<br>Examples:<br>\
        - Create 3 thematic bundles with SKU priority<br>\
        - Create 2 seasonal bundles with leftover priority<br>\
        - Create 5 personalized bundles")
        user_input = gr.Textbox(
            label="",
            placeholder="e.g. 'Create 3 thematic bundles with SKU priority'",
            elem_classes=["standout"]
        )
        send_button = gr.Button("Send")
        output_text = gr.Markdown(elem_classes=["output-box"])
        send_button.click(fn=my_function, inputs=user_input, outputs=output_text)

    with gr.Tab("Query"):
        with gr.Row():
            random_input = gr.Textbox(label="UserID (optional)")
            autofill_button = gr.Button("Autofill")
        with gr.Row():
            with gr.Column(scale=1):
                sku_priority = gr.Checkbox(label="SKU Priority")
            gr.HTML(
                '<div class="inline-checkbox"><span style="cursor:pointer;" onclick="alert(\'Enable this to give priority to products with high stock.\')">❓</span></div>'
            )
        bundle_type = gr.Dropdown(
            choices=["any", "complementary", "seasonal", "thematic", "cross-sell", "personalized"],
            label="Bundle Type", value="thematic"
        )
        with gr.Row():
            number_input = gr.Number(value=3, label="Number of bundles")
            gr.HTML(
                '<div class="inline-checkbox"><span style="cursor:pointer;" onclick="alert(\'Result will contain up to this number of bundles.\')">❓</span></div>'
            )
        go_button = gr.Button("GO")
        result_text = gr.Markdown(elem_classes=["output-box"])

        autofill_button.click(fn=generate_random_string, inputs=None, outputs=random_input)
        go_button.click(fn=my_function_2,
                        inputs=[random_input, sku_priority, number_input, bundle_type],
                        outputs=result_text)

if __name__ == "__main__":
    demo.launch()
