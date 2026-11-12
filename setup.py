from setuptools import find_packages, setup

package_name = 'warehouse_nodes'

setup(
    name=package_name,
    version='0.0.0',

    packages=find_packages(exclude=['test']),

    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),

        ('share/' + package_name, ['package.xml']),
    ],

    install_requires=['setuptools'],

    zip_safe=True,

    maintainer='user',
    maintainer_email='user@example.com',

    description='Warehouse delivery robot nodes',

    license='Apache-2.0',

    entry_points={
        'console_scripts': [
            'warehouse_node = warehouse_nodes.warehouse_node:main',
            'delivery_server = warehouse_nodes.delivery_node:server_main',
            'delivery_client = warehouse_nodes.delivery_node:client_main',
        ],
    },
)
