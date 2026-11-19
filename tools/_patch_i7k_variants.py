import io

p = r"D:\3dsg_1\experiments\run_frontier_i7k.sh"
s = io.open(p, encoding="utf-8").read()
a = "VARIANTS=${VARIANTS:-sh16_g16,sh12_g16,sh8_g16,p90}"
b = "VARIANTS=${VARIANTS:-clean,sh16_g16,sh12_g16,sh8_g16,p90}"
assert a in s, "variant line not found"
io.open(p, "w", encoding="utf-8", newline="\n").write(s.replace(a, b, 1))
print("ok")
