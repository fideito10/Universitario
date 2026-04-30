"""
Fix onclick JS: agregar Enter key press para que Streamlit procese el input.
"""
import re

with open('main_universitario.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the onclick JS pattern and add Enter key simulation
old = (
    "    f\"  var setter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;\"\n"
    "            f\"    setter.call(inp,'{page_id}');\"\n"
    "            f\"    inp.dispatchEvent(new Event('input',{{bubbles:true}}));\"\n"
    "            f\"  }}\"\n"
    "            f\"}})();\"\n"
)

new = (
    "    f\"  var setter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;\"\n"
    "            f\"    setter.call(inp,'{page_id}');\"\n"
    "            f\"    inp.dispatchEvent(new Event('input',{{bubbles:true}}));\"\n"
    "            f\"    inp.dispatchEvent(new Event('change',{{bubbles:true}}));\"\n"
    "            f\"    inp.dispatchEvent(new KeyboardEvent('keydown',{{key:'Enter',keyCode:13,which:13,bubbles:true}}));\"\n"
    "            f\"    inp.dispatchEvent(new KeyboardEvent('keypress',{{key:'Enter',keyCode:13,which:13,bubbles:true}}));\"\n"
    "            f\"    inp.dispatchEvent(new KeyboardEvent('keyup',{{key:'Enter',keyCode:13,which:13,bubbles:true}}));\"\n"
    "            f\"    inp.blur();\"\n"
    "            f\"  }}\"\n"
    "            f\"}})();\"\n"
)

if old in content:
    content = content.replace(old, new)
    with open('main_universitario.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Added Enter key + blur to onclick")
else:
    print("NOT FOUND")
    idx = content.find('setter.call(inp')
    if idx >= 0:
        print("Found at:", idx)
        print(repr(content[idx-50:idx+200]))
