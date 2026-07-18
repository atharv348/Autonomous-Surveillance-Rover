from setuptools import setup
import os
from glob import glob

package_name = 'my_rover'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='joshi',
    maintainer_email='joshi@todo.todo',
    description='Lunar Rover simulation package',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'sensor_simulator.py = my_rover.sensor_simulator:main',
            'obstacle_avoidance.py = my_rover.obstacle_avoidance:main',
        ],
    },
)
