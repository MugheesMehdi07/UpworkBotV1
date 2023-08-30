import threading
import subprocess

def run_flask_app():
    subprocess.Popen(['python', 'app.py'])

def run_continuous_script():
    subprocess.Popen(['python', 'JobParser.py'])

if __name__ == "__main__":
    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()

    # Start the continuous script in a separate thread
    continuous_thread = threading.Thread(target=run_continuous_script)
    continuous_thread.start()

    # Wait for the threads to finish (which they won't)
    flask_thread.join()
    continuous_thread.join()