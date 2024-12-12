from importlib import metadata


def main():
    version = metadata.version("lenlab")
    print(f"Lenlab {version}")
