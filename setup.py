from distutils.core import setup

setup(
    name='Sojourner',
    version='0.1',
    description='Conference schedule application for the Nokia N900',
    author='Will Thompson',
    author_email='will@willthompson.co.uk',
    url='http://gitorious.org/sojourner',
    packages=['sojourner'],
    scripts=['bin/sojourner'],
    py_modules=['sojourner'],
    data_files=[
        ('share/sojourner', ['banner.png']),
        ('share/icons/hicolor/48x48/hildon', ['icons/48x48/sojourner.png']),
        # Yes, other apps put 64x64 icons in 'scalable'.
        ('share/icons/hicolor/scalable/hildon', ['icons/64x64/sojourner.png']),
        ('share/applications/hildon', ['sojourner.desktop']),
    ],
    license='GPL v3',
)

