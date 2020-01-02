import setuptools

with open("../README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gryml",
    version="0.20.01.a1",
    author="Alexander Chichenin",
    author_email="admin@somebugs.com",
    description="Gryml YAML Processor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/sovnarkom/remak8s/tree/master/gryml",
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
        'ruamel.yaml>=0.16.5'
    ],

    entry_points={
        'console_scripts': [
            'gryml=gryml.cli:main',
        ],
    },
)
