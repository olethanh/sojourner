from distutils.core import setup

setup(
    name='Sojourner',
    version='0.1',
    description='Conference schedule application for the Nokia N900',
    author='Will Thompson',
    author_email='will@willthompson.co.uk',
    url='http://gitorious.org/sojourner',
    py_modules=['malvern', 'portrait'],
    packages=['sojourner'],
    scripts=['sojourner.py'],
    data_files=[('share/sojourner', ['banner.png'])],
    license='GPL v3',
)

