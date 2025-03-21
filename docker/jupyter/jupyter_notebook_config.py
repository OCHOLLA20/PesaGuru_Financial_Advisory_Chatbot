# Configuration file for Jupyter Notebook.

c = get_config()  # Get the config object.

# Set the IP address and port for the notebook server.
c.NotebookApp.ip = '0.0.0.0'
c.NotebookApp.port = 8888

# Allow remote access to the notebook server.
c.NotebookApp.allow_remote_access = True

# Set the notebook directory.
c.NotebookApp.notebook_dir = '/home/jovyan/work'

# Enable password protection.
c.NotebookApp.password = ''  # Set a password here if needed.

# Enable the use of a browser.
c.NotebookApp.open_browser = False
