import setuptools

with open("../README.md", "r") as fh:
    long_description = fh.read()

with open("../VERSION.md", "r") as fh:
    version = fh.read().strip()

setuptools.setup(
    name="gryml",
    version=version,
    author="Alexander Chichenin",
    author_email="admin@somebugs.com",
    description="Gryml YAML Processor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/achichenin/gryml",
    packages=setuptools.find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords='yaml helm chart k8s kubernetes',

    python_requires='>=3.7',
    install_requires=[
        'ruamel.yaml>=0.16.5',
        'jinja2>=2.10.3',
        'colorlog>=4.1.0',
    ],

    entry_points={
        'console_scripts': [
            'gryml=gryml.cli:main',
        ],
    },
)
