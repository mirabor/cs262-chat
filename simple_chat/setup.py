from setuptools import setup, find_packages

setup(
    name="simple_chat",
    version="0.1",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'custom-server=chat_system.custom_protocol.server:main',
            'custom-client=chat_system.custom_protocol.client:main',
            'json-server=chat_system.json_protocol.server:main',
            'json-client=chat_system.json_protocol.client:main',
        ],
    },
)