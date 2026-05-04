import os
import sys

# Ensure src is on path when running from the repository root (Spaces will run this file)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the Gradio demo object from the package and launch it
try:
    from wagon_fem.ui import demo
except Exception:
    # Fallback: try importing the UI module which defines demo at module scope
    import wagon_fem.ui as ui
    demo = getattr(ui, 'demo', None)

if demo is None:
    raise RuntimeError(
        'Gradio demo could not be imported. Make sure the package is available.')

if __name__ == '__main__':
    # Spaces uses environment variables for host/port; default to 7860
    host = os.environ.get('GRADIO_SERVER_NAME', '0.0.0.0')
    port = int(os.environ.get('PORT', 7860))
    demo.launch(server_name=host, server_port=port)
