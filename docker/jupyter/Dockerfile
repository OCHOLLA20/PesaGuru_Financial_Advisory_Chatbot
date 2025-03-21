# Use the official Jupyter Notebook image
FROM jupyter/base-notebook:latest

# Set the working directory
WORKDIR /home/jovyan/work

# Copy any necessary files (if needed)
# COPY ./your-files /home/jovyan/work

# Install any additional packages (if needed)
# RUN pip install your-package

# Expose the default Jupyter Notebook port
EXPOSE 8888

# Start Jupyter Notebook
CMD ["start-notebook.sh", "--NotebookApp.token=''", "--NotebookApp.password=''"]
