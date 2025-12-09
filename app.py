# Entry point for Streamlit Cloud
# Redirects to Home.py so sidebar shows "Home" instead of "app"
import runpy
runpy.run_path("Home.py", run_name="__main__")
