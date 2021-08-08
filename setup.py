from os import path

from setuptools import setup, find_packages

from mediakit import info

current_dirname = path.dirname(path.abspath(__file__))
readme_path = path.join(current_dirname, 'README.md')

with open(readme_path, encoding='utf-8') as readme:
    long_description = readme.read()

setup(
    name=info.name.lower(),
    version=info.version,
    description=info.description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=info.author,
    author_email=info.author_email,
    url=info.url,
    download_url=info.download_url,
    license=info.license,
    packages=find_packages(),
    include_package_data=True,
    keywords=[
        'youtube',
        'media',
        'video',
        'audio',
        'download',
        'convert',
        'command line',
        'cli'
    ],
    python_requires='>=3.6',
    install_requires=[
        'pytube>=11.0.0',
        'clint',
        'imageio',
        'imageio-ffmpeg',
        'colorama',
        'wheel'
    ],
    entry_points={
        'console_scripts': [
            'mediakit=mediakit:main'
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',

        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: Unix',

        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',

        'Topic :: Multimedia :: Video',
        'Topic :: Multimedia :: Video :: Conversion',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Sound/Audio :: Conversion'
    ]
)
