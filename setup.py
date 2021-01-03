import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="vm16asm",
    version="1.1",
    author="Joe",
    author_email="iauit@gmx.de",
    description="Assembler for the VM16 CPU",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/joe7575/vm16asm",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPLv3 License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',

    entry_points={
        'console_scripts': [
            'vm16asm=vm16asm.assembler:main',
        ],
    },
)









