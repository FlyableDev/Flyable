from flyable import flyable_usage, library_loader


def run(email=None):
    flyable_usage.send_infos(email)
    lib = library_loader.call()
    print("now running flyable engine")
