from setuptools import setup, find_packages

setup(
    name="ml_pipeline",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "torch>=2.1.0",
        "transformers>=4.36.0",
        "sentence-transformers>=2.2.2",
        "scikit-learn>=1.3.2",
        "numpy>=1.26.2",
        "librosa>=0.10.1",
        "mediapipe>=0.10.8",
        "opencv-python-headless>=4.8.1.78",
        "datasets>=2.15.0",
        "accelerate>=0.25.0",
        "safetensors>=0.4.1",
    ],
)
