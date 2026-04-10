import gradio_client

print("Version:", gradio_client.__version__)
client = gradio_client.Client("Wan-AI/Wan2.1-I2V-14B-720P")
print(client.view_api(return_format="dict"))
