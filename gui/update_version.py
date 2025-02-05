"""
    update package.json with the version from lipidimea/__init__.py

    ! requires lipidimea to be in PYTHONPATH !
"""


import json

from lipidimea import __version__ as ver


def main():
    # read package.json
    with open('package.json', 'r') as jf:
        pkg = json.load(jf)
    # update version
    pkg['version'] = ver
    # re-write package.json
    with open('package.json', 'w') as jf:
        json.dump(pkg, jf, indent=2)
    

if __name__ == '__main__':
    main()
