import json, os
from dataclasses import dataclass, field
from subprocess import Popen, PIPE
from io import StringIO
from contextlib import redirect_stdout


from flyable.compiler import Compiler
from flyable import constants
from flyable.debug.debug_flags import DebugFlag, disable_debug_flags, enable_debug_flags
from flyable.debug.debug_flags_list import FLAGS

from tests.quail.utils.utils import CompilationError
import tests.integration.constants as const
from tests.integration.output.logs import create_log



@dataclass
class IntegrationTest:
  name: str
  desc: str
  main: str
  dir_path: str
  flags: list[DebugFlag]
  __logging: bool;

  __lines: list[str] | None = field(default=None, init=False)
  __main_path: str = field(init=False)
  __output_dir: str = field(init=False)

  def __post_init__(self):
    self.__output_dir = "./build"
    self.__main_path = f"{self.dir_path}/src/{self.main if self.main.endswith('.py') else self.main + '.py'}"
    if self.logging(): 
      create_log(self)

  def py_compile(self):
    return compile("".join(self.lines), self.dir_path, "exec")

  def logging(self):
    return self.__logging

  @property
  def lines(self):
    if self.__lines is None:
      with open(self.__main_path, 'r') as f:
        self.__lines = f.readlines()
    
    return self.__lines


  def fly_compile(self, save_results: bool = False):
    disable_debug_flags()
    enable_debug_flags(*self.flags)
    compiler = Compiler()
    compiler.add_file(self.__main_path)
    compiler.set_output_path(f"{self.__output_dir}/output.o")

    try:
      compiler.compile()
    except Exception as e:
      raise CompilationError(f"COMPILATION_ERROR: {e}")

    if not compiler.has_error():
      return compiler

    raise CompilationError(compiler.get_errors())

  def fly_exec(self):
    disable_debug_flags()
    enable_debug_flags(*self.flags)
    self.fly_compile()
    linker_args = [
        "gcc",
        "-flto",
        "output.o",
        constants.LIB_FLYABLE_RUNTIME_PATH,
        constants.PYTHON_3_10_PATH,
    ]
    p0 = Popen(linker_args, cwd=self.__output_dir)
    p0.wait()
    if p0.returncode != 0:
        raise CompilationError("Linking error")

    p = Popen(
      [self.__output_dir + "/a.exe"],
      cwd=self.__output_dir,
      stdout=PIPE,
      text=True
    )

    if isinstance(p, str):
      raise CompilationError(p)
    
    result = p.communicate()[0]
    return result

  def py_exec(self):
    f = StringIO()
    with redirect_stdout(f):
      exec(self.py_compile(), {})
    s = f.getvalue()
    return s


def load_integration_tests(base_dir: str):
  tests = []

  for test_folder in os.listdir(base_dir):
    if not os.path.isdir(test_folder):
      continue

    for file in os.listdir(test_folder):
      if os.path.isdir(file):
        continue

      if file == const.quail_config_file_name:
        with open(f"{test_folder}/{file}", 'r') as name:
          config_content = json.loads("".join(name.readlines()))

        if not valid_config(config_content):
          raise Exception(f"Invalid test config in {test_folder} test")
        
        logging = config_content.get('logging', False)

        flags = []
        if "debug_flags" in config_content:
          flag_names = config_content["debug_flags"]
          for name in flag_names:
            flag_found = FLAGS.get(name, None)
            if flag_found is not None:
              flags.append(flag_found)
            else:
              # TODO: Add invalid flag warning
              pass
        print(flags)
        tests.append(IntegrationTest(config_content['name'], config_content['description'], config_content['main'], test_folder, flags, logging))

  return tests

def valid_config(config_content: dict):
  return all(key in config_content for key in const.required_keys)
  
