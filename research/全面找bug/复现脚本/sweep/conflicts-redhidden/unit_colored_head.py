"""Latent renderer behaviour: _colored_html with overlapping red/blue ranges (pure function, no workspace)."""
import sys
sys.path.insert(0, "/home/user/literate-enigma")
import app_head as A
t = "首先我们看一个宾语从句的例子。"
for red, blue in [([(7, 8)], [(7, 8)]), ([(7, 9)], [(7, 8)]), ([(7, 8)], [(7, 9)]), ([(8, 9)], [(7, 9)])]:
    h = A._colored_html({"text": t, "red": red, "blue": blue, "deleted": []})
    print(red, blue, "vt-red:", "vt-red" in h, "vt-blue:", "vt-blue" in h)
