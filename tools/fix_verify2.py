import io
p = r"D:\3dsg_1\research\code\scripts\verify_paper_numbers.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('("bicycle", 0.859, 0.653), ("stump", 0.903, 0.885)]',
              '("bicycle", 0.859, 0.653), ("stump", 0.903, 0.778)]')
io.open(p, "w", encoding="utf-8").write(s)
print("script expectation updated to match corrected paper")
