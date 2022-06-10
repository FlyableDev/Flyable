import os

package_root_path = os.path.abspath(os.path.dirname(__file__))

def get_package_data_path(system: str):
    return os.path.join(package_root_path, 'dyn_lib', system)