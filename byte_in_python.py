print(True + 1.0)


print(bin(10))

a = 10
b = a.to_bytes(4, byteorder='little', signed=True)
c = int(b.hex(), base=16)
print(c)
r = int.from_bytes(c.to_bytes(4, byteorder='little', signed=False), byteorder='big', signed=True)
if r != a:
    print(f"Failed at {a=} / {r=}")

