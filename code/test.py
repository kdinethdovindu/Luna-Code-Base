import requests
import sys

print("Imported from:", requests.__file__)
print("Type:", type(requests))
print("Attributes:", dir(requests))
print("First few sys.path entries:", sys.path[:5])
