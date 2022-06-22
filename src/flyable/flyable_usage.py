import platform, sys, time, socket, json

UDP_IP = "FlyableUsage-LB-978fa5a60c748a58.elb.us-east-1.amazonaws.com"
#UDP_IP = "3.97.53.150"
#UDP_IP = "127.0.0.1"
UDP_PORT = 53

sock = socket.socket(
  socket.AF_INET, # Internet
  socket.SOCK_DGRAM # UDP
)

def get_used_modules():
  modules = {}
  for module_name, module_info in sys.modules.items():
    if not hasattr(module_info, "__version__"):
      continue
    modules[module_name] = module_info.__version__

  return modules


def send_infos(email: str | None = None):
  data = {
    "plat": platform.platform(),
    "time": time.time(),
    "py_version": sys.version,
    "modules": get_used_modules(),
  }

  if email is not None:
    data["email"] = email

  sock.sendto(bytes(json.dumps(data), "utf-8"), (UDP_IP, UDP_PORT))