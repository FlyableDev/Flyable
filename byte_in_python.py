# mode: debug


def report_energy(b):
    return b * 2


# start:tree:<label>
a = 2
print(report_energy(12))  # show:cpp_output
print(report_energy("abc"))
# end:tree:<label>

# start:var
b = 12
c = 3 ** 2
# end:var
