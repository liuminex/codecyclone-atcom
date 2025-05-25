# gui.py
import gradio as gr
import random
import string

from user_profiling import get_user_profile
from suggest_bundles import suggest_bundles




def get_revenue_information():

    return "not yet"







# Define your functions
def my_function(user_input):
    return f"Echo from my_function: {user_input}"

def my_function_2(random_input, sku_priority, number_input, bundle_type):
    return (f"my_function_2 received: {random_input}, "
            f"SKU Priority: {sku_priority}, "
            f"Number: {number_input}, "
            f"Bundle Type: {bundle_type}")

# Utility to generate random 8-character string
def generate_random_string():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

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
        user_input = gr.Textbox(
            label="",
            placeholder="e.g. 'Create 3 thematic bundles with SKU priority'",
            elem_classes=["standout"]
        )
        send_button = gr.Button("Send")
        output_text = gr.Textbox(label="", interactive=False, elem_classes=["output-box"])
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
            choices=["thematic", "seasonal", "personalized1", "personalized2", "cross-match"],
            label="Bundle Type", value="thematic"
        )
        with gr.Row():
            number_input = gr.Number(value=3, label="Number of bundles")
            gr.HTML(
                '<div class="inline-checkbox"><span style="cursor:pointer;" onclick="alert(\'Result will contain up to this number of bundles.\')">❓</span></div>'
            )
        go_button = gr.Button("GO")
        result_text = gr.Textbox(interactive=False, elem_classes=["output-box"])

        autofill_button.click(fn=generate_random_string, inputs=None, outputs=random_input)
        go_button.click(fn=my_function_2,
                        inputs=[random_input, sku_priority, number_input, bundle_type],
                        outputs=result_text)

if __name__ == "__main__":
    demo.launch()
