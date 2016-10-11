"""
Copyright (c) 2016 DigiFors GmbH, Leipzig

Permission is hereby granted, free of charge, to any person obtaining a 
copy of this software and associated documentation files (the "Software"), 
to deal in the Software without restriction, including without limitation 
the rights to use, copy, modify, merge, publish, distribute, sublicense, 
and/or sell copies of the Software, and to permit persons to whom the 
Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included 
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS 
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL 
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR 
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, 
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR 
OTHER DEALINGS IN THE SOFTWARE.
"""

from Tkinter import *
import ttk
import tkFileDialog
import tkMessageBox
import tkSimpleDialog
import better_bencode
import datetime

class BencodeViewer:
  
  """
  Provides a hex-editor-like view of the data.
  """
  def hex_viewer(self, data):
    self.hex_view_toplevel = Toplevel()
    self.hex_view_toplevel.title("Hex viewer")
    self.hex_view_text = Text(self.hex_view_toplevel, font=("Courier", 12), width=79)
    self.hex_view_scrollbar = Scrollbar(self.hex_view_toplevel, command=self.hex_view_text.yview)
    self.hex_view_text.config(yscrollcommand=self.hex_view_scrollbar.set)
    text = "Offset   00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F   Text\n"
    for index, char in enumerate(data):
      if index % 16 == 0:
        if index != 0:
          text += "  " + text_row + "\n" # extra spaces, hex values and text, newline
        text_row = ""
        text += hex(index)[2:].zfill(8) # offset
      if index % 8 == 0:
        text += " " # extra space after eight bytes
      if ord(char) <= 32 or ord(char) >= 127:
        text_row += "." # show non-printable characters and everything non-ASCII as dot
      else:
        text_row += char
      text += char.encode("hex").upper()
      text += " "
    if index >= 0:
      text += (16-(index%16))*"   " # extra spaces if the row isn't full
      if index % 16 > 7:
        text = text[:-1] # extra space from above
      text += text_row + "\n"
    self.hex_view_text.insert(1.0, text)
    self.hex_view_text.configure(state=DISABLED)
    self.hex_view_text.grid(row=0, column=0)
    self.hex_view_scrollbar.grid(row=0, column=1, sticky=N+E+W+S)
    
  """
  Shows a context menu with converted timestamp (if applicable) and hex viewer.
  """
  def extra_info(self, event):
    item = self.bencode_tree.identify("item", event.x, event.y)
    right_click_menu = Menu(self.bencode_tree)
    if self.sdata[item][0] == "integer" and self.sdata[item][1] >= 0 and self.sdata[item][1] <= 2147483647: # convert Unix timestamps
      right_click_menu.add_command(label="UTC: %s" % datetime.datetime.utcfromtimestamp(self.sdata[item][1]).isoformat())
    # this is an ugly hack, but it works because there's only one bencode representation of data
    right_click_menu.add_command(label="Hex viewer...", command=lambda: self.hex_viewer(better_bencode.dumps(self.sdata[item][1])))
    right_click_menu.post(event.x_root, event.y_root)
  
  """
  Clears the treeview to display the next file.
  """
  def clear_tree(self):
    for i in range(0, len(self.sdata.keys())):
      try:
        self.bencode_tree.delete(i)
        i += 1
      except TclError:
        pass
    self.data = None
    self.sdata = {}
  
  """
  Based on a decoded file, recursively inserts the objects into the tree.
  """
  def add_object(self, obj, parent):
    new_index = len(self.sdata.keys())
    if isinstance(obj, int):
      item_identifier = self.bencode_tree.insert(parent, new_index, text=str(obj))
      self.sdata[item_identifier] = ("integer", obj)
    elif isinstance(obj, str):
      try:
        obj_str = obj.decode("utf-8")
      except UnicodeDecodeError:
        obj_str = obj.encode("hex")
      item_identifier = self.bencode_tree.insert(parent, new_index, text=obj_str)
      self.sdata[item_identifier] = ("string", obj)
    elif isinstance(obj, list):
      item_identifier = self.bencode_tree.insert(parent, new_index, text="List (%s elements)" % len(obj))
      for list_item in obj:
        self.add_object(list_item, new_index)
      self.sdata[item_identifier] = ("list", obj)
    elif isinstance(obj, dict):
      item_identifier = self.bencode_tree.insert(parent, new_index, text="Dictionary (%s keys)" % len(obj.keys()))
      sorted_keys = obj.keys()
      sorted_keys.sort()
      for key in sorted_keys:
        key_identifier = self.add_object(key, item_identifier)
        self.add_object(obj[key], key_identifier)
      self.sdata[item_identifier] = ("dict", obj)
    return item_identifier
    
  """
  Opens a bencoded file with the help of better_bencode.
  """
  def open_file(self):
    filename = tkFileDialog.askopenfilename(filetypes=[("Bencoded file", "*")], title="Select file to open", parent=self.root) 
    if filename != "":
      self.clear_tree()
      try:
        with open(filename, "rb") as f:
          self.data = better_bencode.load(f)
      except IOError:
        tkMessageBox.showerror("Error", "Could not open file (input/output error)")
        return
      except TypeError, ValueError:
        tkMessageBox.showerror("Error", "Could not open file (is the file really a bencoded file?)")
        return
      self.sdata = {}
      self.add_object(self.data, "")
      
  """
  Initialization.
  """
  def __init__(self):
    self.root = Tk()
    self.root.wm_title("Bencode Viewer")
    self.menubar = Menu(self.root)
    self.menubar.add_command(label="Open file", command=self.open_file)
    self.menubar.add_command(label="Quit", command=self.root.destroy)
    self.root.config(menu=self.menubar)
    self.bencode_tree = ttk.Treeview(self.root)
    self.bencode_tree_ysb = ttk.Scrollbar(self.root, orient="vertical", command=self.bencode_tree.yview)
    self.bencode_tree_xsb = ttk.Scrollbar(self.root, orient="horizontal", command=self.bencode_tree.xview)
    self.bencode_tree.config(yscroll=self.bencode_tree_ysb.set, xscroll=self.bencode_tree_xsb.set)
    self.bencode_tree.bind("<Button-3>", self.extra_info)
    self.bencode_tree.grid(row=0, column=0, sticky=N+E+W+S)
    self.bencode_tree_ysb.grid(row=0, column=1, sticky=N+S)
    self.bencode_tree_xsb.grid(row=1, column=0, sticky=E+W)
    self.data = None
    self.sdata = {}
    self.root.rowconfigure(0, weight=1, minsize=800)
    self.root.columnconfigure(0, weight=1, minsize=500)
    self.root.mainloop()

if __name__ == "__main__":
  BencodeViewer()
